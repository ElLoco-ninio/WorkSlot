import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { api } from '../api/client' // Use generic api client for public calls
import toast from 'react-hot-toast'
import { Loader2, Calendar, Clock, DollarSign, CheckCircle, AlertTriangle } from 'lucide-react'

// Generic wrapper for public API calls
const publicFetch = {
    getProvider: (id: string) => api.get(`/api/public/provider/${id}`).then(r => r.data),
    createBooking: (data: any) => api.post(`/api/public/bookings`, data).then(r => r.data),
}

export default function PublicBooking() {
    const { providerId } = useParams()
    const [step, setStep] = useState<'slot' | 'intake' | 'review' | 'success'>('slot')
    const [selectedDate, setSelectedDate] = useState<Date | null>(null)
    const [selectedSlot, setSelectedSlot] = useState<string | null>(null)

    // Intake Form
    const [formData, setFormData] = useState({
        customer_name: '',
        customer_email: '',
        customer_phone: '',
        notes: ''
    })

    // Booking Result
    const [bookingResult, setBookingResult] = useState<any>(null)

    // Fetch Provider Info
    const { data: provider, isLoading } = useQuery({
        queryKey: ['public-provider', providerId],
        queryFn: () => publicFetch.getProvider(providerId!),
        enabled: !!providerId
    })

    // Create Booking Mutation
    const bookingMutation = useMutation({
        mutationFn: (data: any) => publicFetch.createBooking({
            provider_id: providerId,
            slot_start: selectedSlot, // This would needed to be full ISO string
            ...data
        }),
        onSuccess: (data) => {
            setBookingResult(data)
            if (data.redirect_url) {
                // Redirect logic would go here
                // For MVP we just show a link or simulate
                window.location.href = data.redirect_url
            } else {
                setStep('success')
            }
        },
        onError: (err: any) => toast.error('Failed to book slot. It may be taken.')
    })

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        bookingMutation.mutate(formData)
    }

    // --- Mock Slots (Since we skipped Availability logic implementation for speed) ---
    const mockSlots = [
        "2024-01-01T09:00:00",
        "2024-01-01T10:00:00",
        "2024-01-01T11:00:00",
        "2024-01-01T14:00:00"
    ]

    if (isLoading) return <div className="flex justify-center p-12"><Loader2 className="animate-spin text-primary-500" /></div>
    if (!provider) return <div className="text-center p-12 text-white">Provider not found</div>

    return (
        <div className="min-h-screen bg-gray-950 py-12 px-4 sm:px-6 lg:px-8 font-sans">
            <div className="max-w-md mx-auto bg-gray-900 border border-gray-800 rounded-xl overflow-hidden shadow-2xl">

                {/* Header */}
                <div className="bg-gray-800/50 p-6 border-b border-gray-800">
                    <h1 className="text-2xl font-bold text-white">{provider.business_name}</h1>
                    <p className="text-gray-400 text-sm mt-1">{provider.service_category} • {provider.location_city}</p>
                </div>

                {/* Content */}
                <div className="p-6">

                    {step === 'slot' && (
                        <div className="space-y-4">
                            <h2 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
                                <Calendar className="w-5 h-5 text-primary-400" />
                                Select a Time
                            </h2>
                            {/* Mock Date Picker would be here */}
                            <div className="grid grid-cols-2 gap-3">
                                {mockSlots.map(slot => (
                                    <button
                                        key={slot}
                                        onClick={() => {
                                            setSelectedSlot(slot)
                                            setStep('intake')
                                        }}
                                        className="p-3 rounded-lg border border-gray-700 bg-gray-800/50 hover:border-primary-500 hover:bg-primary-500/10 text-gray-300 hover:text-white transition-all text-sm font-medium"
                                    >
                                        {new Date(slot).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {step === 'intake' && (
                        <form onSubmit={handleSubmit} className="space-y-4 animate-fade-in">
                            <button type="button" onClick={() => setStep('slot')} className="text-sm text-gray-400 hover:text-white mb-2">← Back to slots</button>

                            <h2 className="text-lg font-medium text-white mb-4">Your Details</h2>

                            <div>
                                <label className="label">Name</label>
                                <input className="input" required value={formData.customer_name} onChange={e => setFormData({ ...formData, customer_name: e.target.value })} />
                            </div>
                            <div>
                                <label className="label">Email</label>
                                <input className="input" type="email" required value={formData.customer_email} onChange={e => setFormData({ ...formData, customer_email: e.target.value })} />
                            </div>
                            <div>
                                <label className="label">Notes (Optional)</label>
                                <textarea className="input" rows={3} value={formData.notes} onChange={e => setFormData({ ...formData, notes: e.target.value })} />
                            </div>

                            {provider.payment_required ? (
                                <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4 flex items-start gap-3 mt-4">
                                    <DollarSign className="w-5 h-5 text-yellow-500 mt-0.5" />
                                    <div>
                                        <h4 className="text-sm font-medium text-yellow-200">Payment Required</h4>
                                        <p className="text-xs text-yellow-500/80 mt-1">You will be redirected to complete payment securely.</p>
                                    </div>
                                </div>
                            ) : null}

                            <button disabled={bookingMutation.isPending} className="btn-primary w-full mt-6">
                                {bookingMutation.isPending ? <Loader2 className="animate-spin w-4 h-4 mx-auto" /> :
                                    provider.payment_required ? 'Proceed to Payment' : 'Confirm Booking'}
                            </button>
                        </form>
                    )}

                    {step === 'success' && (
                        <div className="text-center py-8 animate-fade-in">
                            <div className="w-16 h-16 bg-emerald-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
                                <CheckCircle className="w-8 h-8 text-emerald-500" />
                            </div>
                            <h2 className="text-2xl font-bold text-white mb-2">Booking Confirmed!</h2>
                            <p className="text-gray-400">Check your email for details.</p>
                            <p className="text-sm text-gray-500 mt-8">Booking ID: {bookingResult?.booking_id}</p>
                        </div>
                    )}

                </div>
            </div>
        </div>
    )
}
