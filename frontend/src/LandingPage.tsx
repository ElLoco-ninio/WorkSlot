import { useState } from 'react';
import axios from 'axios';
import { ArrowRight, CheckCircle, Loader2 } from 'lucide-react';

export default function LandingPage() {
    const [isFormOpen, setIsFormOpen] = useState(false);
    const [formData, setFormData] = useState({
        email: '',
        phone: '',
        business_category: '',
        city: '',
        description: ''
    });
    const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setStatus('loading');
        try {
            await axios.post('/api/access-requests', formData);
            setStatus('success');
        } catch (err) {
            console.error(err);
            setStatus('error');
        }
    };

    return (
        <div className="min-h-screen bg-white">
            {/* Header */}
            <header className="py-6 px-4 border-b">
                <div className="max-w-6xl mx-auto flex justify-between items-center">
                    <div className="text-xl font-bold">WorkSlot</div>
                    <a href="/login" className="text-sm font-medium hover:text-blue-600">Admin Login</a>
                </div>
            </header>

            {/* Hero */}
            <section className="py-20 px-4 text-center max-w-4xl mx-auto">
                <h1 className="text-4xl md:text-5xl font-extrabold mb-6 tracking-tight">
                    The Booking Platform for Professional Service Providers
                </h1>
                <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
                    A guided, invite-only tool built for cleaners, technicians, and HVAC pros who need manual control, not automated chaos.
                </p>
                <button
                    onClick={() => setIsFormOpen(true)}
                    className="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold text-lg hover:bg-blue-700 transition flex items-center gap-2 mx-auto"
                >
                    Request Early Access <ArrowRight size={20} />
                </button>
                <p className="mt-4 text-sm text-gray-500">
                    30-day free trial • €20/month after • No credit card required yet
                </p>
            </section>

            {/* Features (Minimal) */}
            <section className="py-16 bg-gray-50">
                <div className="max-w-6xl mx-auto px-4 grid md:grid-cols-3 gap-8">
                    {[
                        { title: "Strictly Controlled", desc: "You approve every booking. No surprises." },
                        { title: "Email Only", desc: "No spammy SMS. Just clear email notifications." },
                        { title: "Manual Onboarding", desc: "We set you up personally to ensure success." }
                    ].map((f, i) => (
                        <div key={i} className="bg-white p-6 rounded-xl shadow-sm border">
                            <h3 className="font-bold text-lg mb-2">{f.title}</h3>
                            <p className="text-gray-600">{f.desc}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* Access Form Modal */}
            {isFormOpen && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-xl max-w-md w-full p-6 relative">
                        <button
                            onClick={() => setIsFormOpen(false)}
                            className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
                        >
                            ✕
                        </button>

                        <h2 className="text-2xl font-bold mb-4">Request Access</h2>

                        {status === 'success' ? (
                            <div className="text-center py-8">
                                <CheckCircle className="mx-auto text-green-500 mb-4" size={48} />
                                <h3 className="text-xl font-bold mb-2">Request Received</h3>
                                <p className="text-gray-600 mb-6">
                                    We've received your details. Our team will review your business and contact you shortly to set up your account.
                                </p>
                                <button
                                    onClick={() => setIsFormOpen(false)}
                                    className="bg-gray-100 text-gray-900 px-6 py-2 rounded-lg font-medium"
                                >
                                    Close
                                </button>
                            </div>
                        ) : (
                            <form onSubmit={handleSubmit} className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium mb-1">Email Address *</label>
                                    <input
                                        required
                                        type="email"
                                        className="w-full border rounded-lg p-2"
                                        value={formData.email}
                                        onChange={e => setFormData({ ...formData, email: e.target.value })}
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium mb-1">Phone (Optional)</label>
                                    <input
                                        type="tel"
                                        className="w-full border rounded-lg p-2"
                                        value={formData.phone}
                                        onChange={e => setFormData({ ...formData, phone: e.target.value })}
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-1">City / Area</label>
                                        <input
                                            required
                                            className="w-full border rounded-lg p-2"
                                            value={formData.city}
                                            onChange={e => setFormData({ ...formData, city: e.target.value })}
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Category</label>
                                        <select
                                            required
                                            className="w-full border rounded-lg p-2"
                                            value={formData.business_category}
                                            onChange={e => setFormData({ ...formData, business_category: e.target.value })}
                                        >
                                            <option value="">Select...</option>
                                            <option value="cleaning">Cleaning</option>
                                            <option value="hvac">HVAC / Technician</option>
                                            <option value="beauty">Beauty / Salon</option>
                                            <option value="other">Other</option>
                                        </select>
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium mb-1">Short Description</label>
                                    <textarea
                                        className="w-full border rounded-lg p-2"
                                        rows={2}
                                        placeholder="Tell us about your business..."
                                        value={formData.description}
                                        onChange={e => setFormData({ ...formData, description: e.target.value })}
                                    />
                                </div>

                                <button
                                    type="submit"
                                    disabled={status === 'loading'}
                                    className="w-full bg-blue-600 text-white py-2 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 flex justify-center gap-2"
                                >
                                    {status === 'loading' && <Loader2 className="animate-spin" />}
                                    Submit Request
                                </button>
                                {status === 'error' && (
                                    <p className="text-red-500 text-sm text-center">Something went wrong. Please try again.</p>
                                )}
                            </form>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
