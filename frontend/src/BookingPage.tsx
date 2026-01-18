import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams } from 'react-router-dom';
import { Loader2, Clock, CheckCircle } from 'lucide-react';

interface Slot {
    start: string;
    end: string;
    label: string;
}

export default function BookingPage() {
    const { slug } = useParams();
    const [profile, setProfile] = useState<any>(null);
    const [selectedDate, setSelectedDate] = useState('');
    const [slots, setSlots] = useState<Slot[]>([]);
    const [selectedSlot, setSelectedSlot] = useState<Slot | null>(null);
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        comment: ''
    });
    const [status, setStatus] = useState<'loading' | 'idle' | 'slots_loading' | 'submitting' | 'success' | 'error'>('loading');

    useEffect(() => {
        // Set default date to today or tomorrow
        const today = new Date().toISOString().split('T')[0];
        setSelectedDate(today);
    }, [slug]);

    useEffect(() => {
        if (slug) {
            fetchProfile();
        }
    }, [slug]);

    useEffect(() => {
        if (profile && selectedDate) {
            fetchSlots();
        }
    }, [profile, selectedDate]);

    const fetchProfile = async () => {
        try {
            const res = await axios.get(`/api/public/provider/${slug}`);
            setProfile(res.data);
            setStatus('idle');
        } catch (err) {
            console.error(err);
            setStatus('error');
        }
    };

    const fetchSlots = async () => {
        setStatus('slots_loading');
        try {
            const res = await axios.get(`/api/public/provider/${slug}/slots`, {
                params: { date_str: selectedDate }
            });
            setSlots(res.data);
            setStatus('idle');
        } catch (err) {
            console.error(err);
            setSlots([]); // clear slots on error layout?
            setStatus('idle');
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedSlot) return;
        setStatus('submitting');

        try {
            await axios.post('/api/public/bookings', {
                provider_id: profile.user_id, // we might need to expose user_id in profile read (Verify model)
                customer_name: formData.name,
                customer_email: formData.email,
                customer_comment: formData.comment,
                start_time: selectedSlot.start,
                end_time: selectedSlot.end
            });
            setStatus('success');
        } catch (err) {
            console.error(err);
            alert('Failed to book slot. It might be taken.');
            setStatus('idle');
        }
    };

    if (status === 'loading') return <div className="flex justify-center p-12"><Loader2 className="animate-spin" /></div>;
    if (!profile && status === 'error') return <div className="text-center p-12">Provider not found</div>;

    if (status === 'success') {
        const requirePayment = profile.booking_rules?.require_payment;
        const paymentLink = profile.booking_rules?.payment_link;

        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
                <div className="bg-white p-8 rounded-xl shadow max-w-md w-full text-center">
                    <CheckCircle className="mx-auto text-green-500 mb-4" size={48} />
                    <h1 className="text-2xl font-bold mb-2">Booking Requested!</h1>
                    <p className="text-gray-600 mb-6">
                        Your request has been sent to <strong>{profile.business_name}</strong>.
                        You will receive an email once confirmed.
                    </p>

                    {requirePayment && paymentLink ? (
                        <div className="bg-blue-50 p-4 rounded-lg mb-6 border border-blue-100">
                            <h3 className="font-bold text-blue-900 mb-2">Payment Required</h3>
                            <p className="text-sm text-blue-700 mb-4">
                                This provider requires payment or a deposit to confirm your slot.
                            </p>
                            <a
                                href={paymentLink}
                                target="_blank"
                                rel="noreferrer"
                                className="block w-full bg-blue-600 text-white py-3 rounded-lg font-bold hover:bg-blue-700 transition"
                            >
                                Proceed to Payment →
                            </a>
                            <p className="text-xs text-blue-400 mt-2">
                                Payment is handled directly by the service provider.
                            </p>
                        </div>
                    ) : (
                        <div className="bg-gray-100 p-4 rounded-lg text-sm text-gray-500 mb-6">
                            No immediate payment required. Proceed to await email confirmation.
                        </div>
                    )}

                    <a href="/" className="text-sm text-gray-400 hover:text-gray-600 underline">
                        Back to Home
                    </a>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 py-8 px-4">
            <div className="max-w-4xl mx-auto grid md:grid-cols-3 gap-8">

                {/* Left: Info */}
                <div className="md:col-span-1 space-y-6">
                    <div className="bg-white p-6 rounded-xl shadow-sm border">
                        {profile.logo_url && <img src={profile.logo_url} className="w-16 h-16 rounded mb-4 object-cover" />}
                        <h1 className="text-xl font-bold">{profile.business_name}</h1>
                        <p className="text-gray-500 text-sm mt-1">{profile.business_category} • {profile.service_area}</p>
                    </div>

                    <div className="bg-white p-6 rounded-xl shadow-sm border">
                        <h3 className="font-bold mb-2">Select Date</h3>
                        <input
                            type="date"
                            className="w-full border rounded p-2"
                            value={selectedDate}
                            min={new Date().toISOString().split('T')[0]} // Block past dates
                            onChange={e => setSelectedDate(e.target.value)}
                        />
                    </div>
                </div>

                {/* Right: Slots & Form */}
                <div className="md:col-span-2">
                    <div className="bg-white p-8 rounded-xl shadow-sm border min-h-[400px]">
                        {!selectedSlot ? (
                            <div>
                                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                                    <Clock size={20} /> Available Slots for {selectedDate}
                                </h2>

                                {status === 'slots_loading' ? (
                                    <div className="py-12 flex justify-center"><Loader2 className="animate-spin text-gray-400" /></div>
                                ) : slots.length === 0 ? (
                                    <p className="text-gray-500 text-center py-12">No slots available on this date.</p>
                                ) : (
                                    <div className="grid grid-cols-3 sm:grid-cols-4 gap-3">
                                        {slots.map((slot, i) => (
                                            <button
                                                key={i}
                                                onClick={() => setSelectedSlot(slot)}
                                                className="border border-blue-100 bg-blue-50 text-blue-700 py-3 rounded-lg hover:bg-blue-100 transition font-medium text-sm"
                                            >
                                                {slot.label}
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="space-y-6">
                                <button onClick={() => setSelectedSlot(null)} className="text-sm text-gray-500 hover:text-gray-800">
                                    ← Back to slots
                                </button>

                                <div className="bg-blue-50 p-4 rounded-lg flex justify-between items-center">
                                    <div>
                                        <div className="font-bold text-blue-900">{selectedSlot.label}</div>
                                        <div className="text-sm text-blue-700">{selectedDate}</div>
                                    </div>
                                    <div className="text-sm font-medium text-blue-800">30 min</div>
                                </div>

                                <form onSubmit={handleSubmit} className="space-y-4">
                                    <div className="grid md:grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium mb-1">Your Name *</label>
                                            <input required className="w-full border rounded p-2"
                                                value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })}
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">Email Address *</label>
                                            <input required type="email" className="w-full border rounded p-2"
                                                value={formData.email} onChange={e => setFormData({ ...formData, email: e.target.value })}
                                            />
                                        </div>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Message (Optional)</label>
                                        <textarea className="w-full border rounded p-2" rows={2}
                                            value={formData.comment} onChange={e => setFormData({ ...formData, comment: e.target.value })}
                                        />
                                    </div>

                                    <div className="flex items-center gap-2 text-sm text-gray-600">
                                        <input required type="checkbox" id="consent" />
                                        <label htmlFor="consent">I agree to be contacted about this booking.</label>
                                    </div>

                                    <div className="text-xs text-gray-400 bg-gray-50 p-2 rounded">
                                        Note: Payment is handled directly by the service provider. No payment is processed on this page.
                                    </div>

                                    <button
                                        type="submit"
                                        disabled={status === 'submitting'}
                                        className="w-full bg-black text-white py-3 rounded-lg font-bold hover:bg-gray-800 flex justify-center gap-2"
                                    >
                                        {status === 'submitting' && <Loader2 className="animate-spin" />}
                                        Confirm Booking
                                    </button>
                                </form>
                            </div>
                        )}
                    </div>
                </div>

            </div>
        </div>
    );
}
