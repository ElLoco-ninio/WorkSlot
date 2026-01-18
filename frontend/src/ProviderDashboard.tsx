import { useState, useEffect } from 'react';
import axios from 'axios';
import { Loader2, Calendar, Check, X, Copy, ExternalLink, RefreshCw, Settings, Clock, Plus, Trash2, CheckCircle } from 'lucide-react';

interface Booking {
    id: number;
    customer_name: string;
    customer_email: string;
    customer_comment: string;
    start_time: string;
    end_time: string;
    status: string; // pending, confirmed, declined, expired
    created_at: string;
}

interface SlotConfig {
    type: 'window' | 'specific';
    start: string;
    end?: string;
}

interface Profile {
    slug: string;
    business_name: string;
    business_category: string;
    service_area: string;
    country?: string;
    logo_url?: string;
    availability_config: any;
    booking_rules: any;
}

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

export default function ProviderDashboard() {
    const [activeTab, setActiveTab] = useState<'bookings' | 'details' | 'availability' | 'rules'>('bookings');
    const [bookings, setBookings] = useState<Booking[]>([]);
    const [profile, setProfile] = useState<Profile | null>(null);
    const [status, setStatus] = useState('loading');
    const [actionStatus, setActionStatus] = useState<number | null>(null);

    // Modal State
    const [activeBooking, setActiveBooking] = useState<Booking | null>(null);
    const [modalType, setModalType] = useState<'confirm' | 'decline' | null>(null);
    const [comment, setComment] = useState('');

    // Settings Form State
    const [settingsForm, setSettingsForm] = useState<any>({});
    const [saveStatus, setSaveStatus] = useState('idle');

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setStatus('loading');
        try {
            const [bookingsRes, profileRes] = await Promise.all([
                axios.get('/api/provider/bookings', { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }),
                axios.get('/api/profile', { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } })
            ]);
            setBookings(bookingsRes.data);
            setProfile(profileRes.data);

            // Init settings form with Migration Logic
            const p = profileRes.data;
            const config = p.availability_config || {};

            let daySchedules = config.day_schedules || {};

            // Auto-Migrate Legacy Config if new schema is empty
            if (Object.keys(daySchedules).length === 0 && config.working_days) {
                config.working_days.forEach((day: string) => {
                    daySchedules[day] = [{
                        type: 'window', // Default to window
                        start: config.start_time || '09:00',
                        end: config.end_time || '17:00'
                    }];
                });
            }

            setSettingsForm({
                business_name: p.business_name,
                business_category: p.business_category,
                service_area: p.service_area,
                country: p.country,
                logo_url: p.logo_url, // NEW
                slug: p.slug, // NEW
                // Availability
                day_schedules: daySchedules,
                slot_duration: (config.slot_duration !== undefined && config.slot_duration !== null) ? config.slot_duration : 30,
                // Rules Defaults
                require_payment: p.booking_rules?.require_payment || false,
                payment_link: p.booking_rules?.payment_link || '',
                hold_duration: p.booking_rules?.hold_duration || 30,
            });

            setStatus('idle');
        } catch (err) {
            console.error(err);
            setStatus('error');
        }
    };

    const openModal = (booking: Booking, type: 'confirm' | 'decline') => {
        setActiveBooking(booking);
        setModalType(type);
        setComment('');
    };

    const closeModal = () => {
        setActiveBooking(null);
        setModalType(null);
        setComment('');
    };

    const confirmAction = async () => {
        if (!activeBooking || !modalType) return;

        const newStatus = modalType === 'confirm' ? 'confirmed' : 'declined';
        setActionStatus(activeBooking.id);

        try {
            await axios.put(`/api/provider/bookings/${activeBooking.id}/status`, {
                status: newStatus,
                provider_comment: comment
            }, {
                headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
            });

            setBookings(prev => prev.map(b => b.id === activeBooking.id ? { ...b, status: newStatus } : b));
            closeModal();
        } catch (err) {
            console.error(err);
            alert("Failed to update status");
        } finally {
            setActionStatus(null);
        }
    };

    // Link Logic
    const bookingUrl = profile?.slug
        ? `${window.location.origin}/book/${profile.slug}`
        : '';

    const saveSettings = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaveStatus('saving');
        try {
            const payload = {
                business_name: settingsForm.business_name,
                business_category: settingsForm.business_category,
                service_area: settingsForm.service_area,
                country: settingsForm.country,
                logo_url: settingsForm.logo_url,
                slug: settingsForm.slug,
                new_password: settingsForm.new_password, // Optional
                availability_config: {
                    day_schedules: settingsForm.day_schedules,
                    slot_duration: parseInt(settingsForm.slot_duration as string),
                },
                booking_rules: {
                    require_payment: settingsForm.require_payment,
                    payment_link: settingsForm.payment_link,
                    hold_duration: parseInt(settingsForm.hold_duration as string)
                }
            };

            // Optimistic UI update for slug if business name changes logic is complicated, 
            // so we rely on backend for slug.

            await axios.patch('/api/profile', payload, {
                headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
            });

            setSaveStatus('success');
            // Refresh profile
            const res = await axios.get('/api/profile', { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } });
            setProfile(res.data);

            // Clear success message after 3s
            setTimeout(() => setSaveStatus('idle'), 3000);
        } catch (err: any) {
            console.error(err);
            const msg = err.response?.data?.detail || "Failed to save settings. Please try again.";
            setSaveStatus(msg); // Storing message in status state for simplicity, or we can separate
        }
    };

    const copyLink = () => {
        if (!bookingUrl) return;
        navigator.clipboard.writeText(bookingUrl);
        alert('Link copied to clipboard!');
    };

    // ... Availability Helpers ...
    const isDayActive = (day: string) => {
        return !!settingsForm.day_schedules?.[day];
    };

    const toggleDay = (day: string) => {
        const newSchedules = { ...settingsForm.day_schedules };
        if (newSchedules[day]) {
            delete newSchedules[day];
        } else {
            // Add default schedule
            newSchedules[day] = [{ type: 'window', start: '09:00', end: '17:00' }];
        }
        setSettingsForm({ ...settingsForm, day_schedules: newSchedules });
    };

    const addSlot = (day: string) => {
        const newSchedules = { ...settingsForm.day_schedules };
        if (!newSchedules[day]) newSchedules[day] = [];

        // Add a default window
        newSchedules[day].push({ type: 'window', start: '12:00', end: '14:00' });
        setSettingsForm({ ...settingsForm, day_schedules: newSchedules });
    };

    const removeSlot = (day: string, index: number) => {
        const newSchedules = { ...settingsForm.day_schedules };
        newSchedules[day] = newSchedules[day].filter((_: any, i: number) => i !== index);
        if (newSchedules[day].length === 0) delete newSchedules[day];
        setSettingsForm({ ...settingsForm, day_schedules: newSchedules });
    };

    const updateSlot = (day: string, index: number, field: string, value: any) => {
        const newSchedules = { ...settingsForm.day_schedules };
        newSchedules[day][index] = { ...newSchedules[day][index], [field]: value };
        setSettingsForm({ ...settingsForm, day_schedules: newSchedules });
    };

    if (status === 'loading') return <div className="flex justify-center p-12"><Loader2 className="animate-spin" /></div>;

    if (status === 'error') return (
        <div className="flex flex-col items-center justify-center min-h-screen p-6 text-center">
            <div className="bg-red-50 text-red-600 p-6 rounded-xl border border-red-200 max-w-md w-full">
                <h2 className="text-xl font-bold mb-2">Failed to load dashboard</h2>
                <p className="text-sm text-gray-600 mb-6">We couldn't fetch your profile data. Please check your connection.</p>
                <button
                    onClick={fetchData}
                    className="bg-red-600 text-white px-6 py-2 rounded-lg font-bold hover:bg-red-700 flex items-center justify-center gap-2 w-full"
                >
                    <RefreshCw size={20} /> Retry
                </button>
            </div>
            <button
                onClick={() => { localStorage.clear(); window.location.href = '/login'; }}
                className="text-gray-400 hover:text-gray-600 text-sm mt-8 underline"
            >
                Back to Login
            </button>
        </div>
    );

    return (
        <div className="min-h-screen bg-gray-50 p-6">
            <div className="max-w-6xl mx-auto space-y-6">

                {/* Helper Header */}
                <div className="bg-white p-6 rounded-xl shadow flex flex-col md:flex-row justify-between items-center gap-4">
                    <div className="flex items-center gap-4">
                        {profile?.logo_url ? (
                            <img src={profile.logo_url} alt="Logo" className="w-16 h-16 rounded-full object-cover border" />
                        ) : (
                            <div className="w-16 h-16 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-bold text-xl border">
                                {profile?.business_name.substring(0, 2).toUpperCase()}
                            </div>
                        )}
                        <div>
                            <h1 className="text-2xl font-bold mb-1">{profile?.business_name}</h1>
                            <p className="text-gray-500 flex items-center gap-2">Provider Dashboard <span className="bg-green-100 text-green-700 text-xs px-2 py-0.5 rounded-full">Live</span></p>
                        </div>
                    </div>
                    <div className="flex flex-wrap items-center gap-3">
                        <button onClick={fetchData} className="p-2 text-gray-400 hover:text-gray-700" title="Refresh"><RefreshCw size={20} /></button>

                        {bookingUrl ? (
                            <div className="bg-blue-50 px-4 py-2 rounded-lg flex items-center gap-2 border border-blue-100">
                                <span className="text-sm text-blue-800 font-mono truncate max-w-[200px]">
                                    {bookingUrl}
                                </span>
                                <button onClick={copyLink} className="text-blue-600 hover:text-blue-800"><Copy size={16} /></button>
                                <a href={bookingUrl} target="_blank" className="text-blue-600 hover:text-blue-800"><ExternalLink size={16} /></a>
                            </div>
                        ) : (
                            <div className="bg-gray-100 px-4 py-2 rounded-lg text-sm text-gray-400">
                                Generating Link...
                            </div>
                        )}

                        <button
                            onClick={() => { localStorage.clear(); window.location.href = '/login'; }}
                            className="text-red-500 hover:underline text-sm ml-4"
                        >
                            Logout
                        </button>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex gap-4 border-b border-gray-200 overflow-x-auto">
                    <button
                        onClick={() => setActiveTab('bookings')}
                        className={`pb-3 px-1 font-medium text-sm whitespace-nowrap ${activeTab === 'bookings' ? 'text-black border-b-2 border-black' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        Bookings
                    </button>
                    <button
                        onClick={() => setActiveTab('details')}
                        className={`pb-3 px-1 font-medium text-sm whitespace-nowrap ${activeTab === 'details' ? 'text-black border-b-2 border-black' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        Business Details
                    </button>
                    <button
                        onClick={() => setActiveTab('availability')}
                        className={`pb-3 px-1 font-medium text-sm whitespace-nowrap ${activeTab === 'availability' ? 'text-black border-b-2 border-black' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        Availability
                    </button>
                    <button
                        onClick={() => setActiveTab('rules')}
                        className={`pb-3 px-1 font-medium text-sm whitespace-nowrap ${activeTab === 'rules' ? 'text-black border-b-2 border-black' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        Booking Rules
                    </button>
                </div>

                {/* Content */}
                {activeTab === 'bookings' && (
                    <div className="bg-white rounded-xl shadow overflow-hidden">
                        <div className="p-6 border-b">
                            <h2 className="text-lg font-bold">Recent Bookings</h2>
                        </div>
                        {bookings.length === 0 ? (
                            <div className="p-12 text-center text-gray-500">No bookings yet. Share your link!</div>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="w-full text-left">
                                    <thead className="bg-gray-50 text-gray-600 text-sm uppercase">
                                        <tr>
                                            <th className="p-4">Customer</th>
                                            <th className="p-4">Time</th>
                                            <th className="p-4">Status</th>
                                            <th className="p-4">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y">
                                        {bookings.map(booking => {
                                            const isPending = booking.status === 'pending' || booking.status === 'awaiting_payment';
                                            return (
                                                <tr key={booking.id} className="hover:bg-gray-50">
                                                    <td className="p-4">
                                                        <div className="font-medium">{booking.customer_name}</div>
                                                        <div className="text-sm text-gray-500">{booking.customer_email}</div>
                                                        {booking.customer_comment && <div className="text-xs text-gray-400 mt-1">"{booking.customer_comment}"</div>}
                                                    </td>
                                                    <td className="p-4">
                                                        <div className="flex items-center gap-2">
                                                            <Calendar size={16} className="text-gray-400" />
                                                            <span>{new Date(booking.start_time).toLocaleString()}</span>
                                                        </div>
                                                    </td>
                                                    <td className="p-4">
                                                        <span className={`px-2 py-1 rounded text-xs font-bold uppercase
                                                ${booking.status === 'confirmed' ? 'bg-green-100 text-green-700' : ''}
                                                ${booking.status === 'declined' ? 'bg-red-100 text-red-700' : ''}
                                                ${isPending ? 'bg-yellow-100 text-yellow-700' : ''}
                                                ${booking.status === 'expired' ? 'bg-gray-100 text-gray-500' : ''}
                                            `}>
                                                            {booking.status}
                                                        </span>
                                                    </td>
                                                    <td className="p-4">
                                                        {isPending && (
                                                            <div className="flex gap-2">
                                                                <button
                                                                    onClick={() => openModal(booking, 'confirm')}
                                                                    className="p-2 bg-green-50 text-green-600 rounded hover:bg-green-100 border border-green-200"
                                                                    title="Confirm"
                                                                >
                                                                    <Check size={16} />
                                                                </button>
                                                                <button
                                                                    onClick={() => openModal(booking, 'decline')}
                                                                    className="p-2 bg-red-50 text-red-600 rounded hover:bg-red-100 border border-red-200"
                                                                    title="Decline"
                                                                >
                                                                    <X size={16} />
                                                                </button>
                                                            </div>
                                                        )}
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                )}

                {/* Settings Form Wrapper */}
                {activeTab !== 'bookings' && (
                    <form onSubmit={saveSettings} className="space-y-6">
                        {/* Success/Error Banner */}
                        {saveStatus === 'success' && (
                            <div className="bg-green-100 border border-green-300 text-green-800 px-4 py-3 rounded relative animate-fade-in flex items-center gap-2">
                                <CheckCircle size={20} />
                                <span className="font-bold">Settings saved successfully!</span>
                            </div>
                        )}
                        {saveStatus !== 'idle' && saveStatus !== 'saving' && saveStatus !== 'success' && (
                            <div className="bg-red-100 border border-red-300 text-red-800 px-4 py-3 rounded relative animate-fade-in flex items-center gap-2">
                                <X size={20} />
                                <span className="font-bold">{saveStatus}</span>
                            </div>
                        )}

                        {activeTab === 'details' && (
                            <div className="bg-white rounded-xl shadow p-6 space-y-8 animate-fade-in">
                                <div className="space-y-6">
                                    <h3 className="text-lg font-bold text-gray-900 border-b pb-2">Business Identity</h3>

                                    {/* Logo Upload */}
                                    <div>
                                        <label className="block text-sm font-bold text-gray-700 mb-2">Business Logo</label>
                                        <div className="flex items-center gap-6">
                                            {settingsForm.logo_url ? (
                                                <img src={settingsForm.logo_url} alt="Logo" className="w-24 h-24 rounded-lg object-cover border" />
                                            ) : (
                                                <div className="w-24 h-24 bg-gray-100 rounded-lg border border-dashed border-gray-300 flex items-center justify-center text-gray-400">
                                                    No Logo
                                                </div>
                                            )}
                                            <div className="flex-1">
                                                <input
                                                    type="file"
                                                    accept="image/*"
                                                    onChange={(e) => {
                                                        const file = e.target.files?.[0];
                                                        if (file) {
                                                            const reader = new FileReader();
                                                            reader.onloadend = () => {
                                                                setSettingsForm({ ...settingsForm, logo_url: reader.result as string });
                                                            };
                                                            reader.readAsDataURL(file);
                                                        }
                                                    }}
                                                    className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-bold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                                                />
                                                <p className="text-xs text-gray-500 mt-2">Recommended: Square JPG/PNG, max 1MB.</p>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div>
                                            <label className="block text-sm font-bold text-gray-700 mb-1">Business Name</label>
                                            <input type="text" value={settingsForm.business_name} onChange={e => setSettingsForm({ ...settingsForm, business_name: e.target.value })} className="w-full border rounded-lg p-2.5 bg-gray-50 border-gray-300 focus:ring-2 focus:ring-blue-500 outline-none transition-all" />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-bold text-gray-700 mb-1">Category</label>
                                            <input type="text" value={settingsForm.business_category} onChange={e => setSettingsForm({ ...settingsForm, business_category: e.target.value })} className="w-full border rounded-lg p-2.5 bg-gray-50 border-gray-300 focus:ring-2 focus:ring-blue-500 outline-none transition-all" />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-bold text-gray-700 mb-1">City/Service Area</label>
                                            <input type="text" value={settingsForm.service_area} onChange={e => setSettingsForm({ ...settingsForm, service_area: e.target.value })} className="w-full border rounded-lg p-2.5 bg-gray-50 border-gray-300 focus:ring-2 focus:ring-blue-500 outline-none transition-all" />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-bold text-gray-700 mb-1">Country</label>
                                            <input type="text" value={settingsForm.country || ''} onChange={e => setSettingsForm({ ...settingsForm, country: e.target.value })} className="w-full border rounded-lg p-2.5 bg-gray-50 border-gray-300 focus:ring-2 focus:ring-blue-500 outline-none transition-all" />
                                        </div>
                                    </div>

                                    <div>
                                        <label className="block text-sm font-bold text-gray-700 mb-1">Booking Link Slug (../book/<b>slug</b>)</label>
                                        <input type="text" value={settingsForm.slug || ''} onChange={e => setSettingsForm({ ...settingsForm, slug: e.target.value })} className="w-full border rounded-lg p-2.5 bg-gray-50 border-gray-300 focus:ring-2 focus:ring-blue-500 outline-none transition-all" />
                                    </div>
                                </div>

                                {/* Security Section */}
                                <div className="space-y-4 pt-6 border-t">
                                    <h3 className="text-lg font-bold text-gray-900">Security / Change Password</h3>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div>
                                            <label className="block text-sm font-bold text-gray-700 mb-1">New Password</label>
                                            <input type="password" placeholder="••••••••" value={settingsForm.new_password || ''} onChange={e => setSettingsForm({ ...settingsForm, new_password: e.target.value })} className="w-full border rounded-lg p-2.5 bg-gray-50 border-gray-300 focus:ring-2 focus:ring-blue-500 outline-none transition-all" />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeTab === 'availability' && (
                            <div className="bg-white rounded-xl shadow p-6 space-y-6 animate-fade-in">
                                <h2 className="text-lg font-bold mb-4 flex items-center gap-2"><Clock size={20} /> Flexible Availability</h2>

                                <div className="space-y-4">
                                    <div className="flex justify-between items-center mb-2">
                                        <label className="text-sm font-medium">Slot Duration</label>
                                        <select className="border rounded p-1 text-sm"
                                            value={settingsForm.slot_duration}
                                            onChange={e => setSettingsForm({ ...settingsForm, slot_duration: e.target.value })}>
                                            <option value="15">15 min</option>
                                            <option value="30">30 min</option>
                                            <option value="45">45 min</option>
                                            <option value="60">60 min</option>
                                            <option value="0">Custom / Window</option>
                                        </select>
                                    </div>

                                    <div className="border-t pt-4 space-y-6">
                                        {DAYS.map(day => {
                                            const isActive = isDayActive(day);
                                            const schedules = settingsForm.day_schedules?.[day] || [];

                                            return (
                                                <div key={day} className={`border-b border-gray-100 pb-4 last:border-0 ${!isActive ? 'opacity-50' : ''}`}>
                                                    <div className="flex items-center justify-between mb-2">
                                                        <div className="flex items-center gap-3">
                                                            <button
                                                                type="button"
                                                                onClick={() => toggleDay(day)}
                                                                className={`w-10 h-6 rounded-full flex items-center transition-colors ${isActive ? 'bg-black justify-end' : 'bg-gray-300 justify-start'}`}
                                                            >
                                                                <div className="w-4 h-4 bg-white rounded-full mx-1" />
                                                            </button>
                                                            <span className="font-bold w-12">{day}</span>
                                                        </div>

                                                        {isActive && (
                                                            <button
                                                                type="button"
                                                                onClick={() => addSlot(day)}
                                                                className="text-xs flex items-center gap-1 bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded"
                                                            >
                                                                <Plus size={14} /> Add Pattern
                                                            </button>
                                                        )}
                                                    </div>

                                                    {isActive && schedules.map((slot: SlotConfig, idx: number) => (
                                                        <div key={idx} className="flex flex-wrap items-center gap-2 mt-2 ml-14 animate-fade-in">
                                                            <select
                                                                value={slot.type}
                                                                onChange={e => updateSlot(day, idx, 'type', e.target.value)}
                                                                className="text-sm border rounded p-1 bg-gray-50"
                                                            >
                                                                <option value="window">Window</option>
                                                                <option value="specific">Specific Time</option>
                                                            </select>

                                                            <input
                                                                type="time"
                                                                value={slot.start}
                                                                onChange={e => updateSlot(day, idx, 'start', e.target.value)}
                                                                className="border rounded p-1 text-sm w-32"
                                                            />

                                                            {slot.type === 'window' && (
                                                                <>
                                                                    <span className="text-gray-400">-</span>
                                                                    <input
                                                                        type="time"
                                                                        value={slot.end || ''}
                                                                        onChange={e => updateSlot(day, idx, 'end', e.target.value)}
                                                                        className="border rounded p-1 text-sm w-32"
                                                                    />
                                                                </>
                                                            )}

                                                            <button
                                                                type="button"
                                                                onClick={() => removeSlot(day, idx)}
                                                                className="text-red-400 hover:text-red-600 p-1"
                                                            >
                                                                <Trash2 size={16} />
                                                            </button>
                                                        </div>
                                                    ))}

                                                    {isActive && schedules.length === 0 && (
                                                        <div className="ml-14 text-xs text-red-500">No active slots. Add one.</div>
                                                    )}
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeTab === 'rules' && (
                            <div className="bg-white rounded-xl shadow p-6 animate-fade-in">
                                <h2 className="text-lg font-bold mb-4 flex items-center gap-2"><Settings size={20} /> Booking Rules</h2>
                                <div className="space-y-6">
                                    <div className="flex items-start gap-3">
                                        <input
                                            type="checkbox"
                                            id="req_payment"
                                            checked={settingsForm.require_payment}
                                            onChange={e => setSettingsForm({ ...settingsForm, require_payment: e.target.checked })}
                                            className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                                        />
                                        <div>
                                            <label htmlFor="req_payment" className="block text-sm font-bold text-gray-900">Require Payment / Deposit</label>
                                            <p className="text-xs text-gray-500">If checked, customers will be redirected to your payment link.</p>

                                            {settingsForm.require_payment && (
                                                <div className="mt-2">
                                                    <input
                                                        type="text"
                                                        placeholder="https://buy.stripe.com/..."
                                                        value={settingsForm.payment_link}
                                                        onChange={e => setSettingsForm({ ...settingsForm, payment_link: e.target.value })}
                                                        className="w-full border rounded-lg p-2 text-sm bg-gray-50 focus:ring-2 focus:ring-blue-500 transition-all"
                                                    />
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    <div className="flex items-start gap-3 pt-4 border-t border-gray-100">
                                        <div className="pt-1">
                                            <Clock size={16} className="text-gray-400" />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-bold text-gray-900">Temporary Hold Duration</label>
                                            <p className="text-xs text-gray-500 mb-2">How long (in minutes) to hold a slot while customer pays?</p>
                                            <input
                                                type="number"
                                                value={settingsForm.hold_duration}
                                                onChange={e => setSettingsForm({ ...settingsForm, hold_duration: parseInt(e.target.value) })}
                                                className="w-24 border rounded-lg p-2 text-sm bg-gray-50 focus:ring-2 focus:ring-blue-500 transition-all"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Footer Action */}
                        <div className="flex justify-end pt-4">
                            <button
                                type="submit"
                                disabled={saveStatus === 'saving'}
                                className="px-8 py-3 bg-black text-white rounded-xl font-bold hover:bg-gray-800 flex justify-center items-center gap-2 shadow-lg"
                            >
                                {saveStatus === 'saving' ? <Loader2 className="animate-spin" /> : 'Save Configuration'}
                            </button>
                        </div>
                    </form>
                )}

            </div>

            {/* Action Modal */}
            {activeBooking && modalType && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 animate-fade-in">
                    <div className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden">
                        <div className={`p-4 border-b flex justify-between items-center ${modalType === 'confirm' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
                            }`}>
                            <h3 className="font-bold text-lg flex items-center gap-2">
                                {modalType === 'confirm' ? <CheckCircle size={20} /> : <X size={20} />}
                                {modalType === 'confirm' ? 'Confirm Booking' : 'Decline Booking'}
                            </h3>
                            <button onClick={closeModal} className="text-gray-500 hover:text-black"><X size={20} /></button>
                        </div>

                        <div className="p-6 space-y-4">
                            <div>
                                <label className="block text-sm font-bold text-gray-700 mb-1">
                                    Note to Customer (Optional)
                                </label>
                                <textarea
                                    className="w-full border rounded-lg p-3 text-sm focus:ring-2 focus:ring-black outline-none"
                                    rows={3}
                                    placeholder={modalType === 'confirm' ? "Looking forward to seeing you..." : "Sorry, I am unavailable at this time..."}
                                    value={comment}
                                    onChange={e => setComment(e.target.value)}
                                />
                                <p className="text-xs text-gray-400 mt-1 text-right">{comment.length}/500</p>
                            </div>

                            <div className="bg-gray-50 p-3 rounded-lg text-sm text-gray-600">
                                <p><strong>Customer:</strong> {activeBooking.customer_name}</p>
                                <p><strong>Time:</strong> {new Date(activeBooking.start_time).toLocaleString()}</p>
                            </div>

                            <div className="flex gap-3 pt-2">
                                <button
                                    onClick={closeModal}
                                    className="flex-1 py-2 text-gray-600 font-medium hover:bg-gray-100 rounded-lg"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={confirmAction}
                                    disabled={actionStatus === activeBooking.id}
                                    className={`flex-1 py-2 text-white font-bold rounded-lg flex justify-center gap-2 ${modalType === 'confirm' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'
                                        }`}
                                >
                                    {actionStatus === activeBooking.id ? <Loader2 className="animate-spin" /> : (modalType === 'confirm' ? 'Confirm' : 'Decline')}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
