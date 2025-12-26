import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { providerApi } from '../api/client'
import { useAuthStore } from '../stores/authStore'
import toast from 'react-hot-toast'
import {
  User,
  CreditCard,
  Crown,
  Check,
  Loader2,
  Zap,
  Globe,
  DollarSign,
  Clock,
} from 'lucide-react'

export default function Settings() {
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  // MVP: Remove subscription tab, focus on profile and booking settings
  const [activeTab, setActiveTab] = useState<'profile' | 'payment'>('profile')

  const updateSettingsMutation = useMutation({
    mutationFn: (data: any) => providerApi.updateSettings(data),
    onSuccess: (data: any) => {
      // Update local user store (mock-ish)
      // In real app, we'd refetch 'me'
      toast.success('Settings updated!')
    },
    onError: (error: any) => toast.error('Failed to update settings'),
  })

  // Local state for forms
  const [profileForm, setProfileForm] = useState({
    business_name: user?.business_name || '',
    service_category: user?.service_category || '',
    location_city: user?.location_city || ''
  })

  const [paymentForm, setPaymentForm] = useState({
    payment_link: user?.payment_link || '',
    payment_required: user?.payment_required || false,
    payment_hold_minutes: user?.payment_hold_minutes || 30
  })

  const handleProfileSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    updateSettingsMutation.mutate(profileForm)
  }

  const handlePaymentSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    updateSettingsMutation.mutate(paymentForm)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-3xl font-display font-bold text-white">Settings</h1>
        <p className="text-gray-400">Manage your profile and payment preferences</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-800">
        <button
          onClick={() => setActiveTab('profile')}
          className={`px-4 py-3 font-medium transition-colors ${activeTab === 'profile'
            ? 'text-primary-400 border-b-2 border-primary-400'
            : 'text-gray-400 hover:text-white'
            }`}
        >
          <User className="w-4 h-4 inline-block mr-2" />
          Profile
        </button>
        <button
          onClick={() => setActiveTab('payment')}
          className={`px-4 py-3 font-medium transition-colors ${activeTab === 'payment'
            ? 'text-primary-400 border-b-2 border-primary-400'
            : 'text-gray-400 hover:text-white'
            }`}
        >
          <DollarSign className="w-4 h-4 inline-block mr-2" />
          Payments & Rules
        </button>
      </div>

      {/* Profile Tab */}
      {activeTab === 'profile' && (
        <form onSubmit={handleProfileSubmit} className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
          <h2 className="text-xl font-display font-semibold text-white mb-6">
            Public Profile
          </h2>
          <div className="space-y-4 max-w-md">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Business Name
              </label>
              <input
                type="text"
                value={profileForm.business_name}
                onChange={e => setProfileForm({ ...profileForm, business_name: e.target.value })}
                className="input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Service Category
              </label>
              <input
                type="text"
                value={profileForm.service_category}
                onChange={e => setProfileForm({ ...profileForm, service_category: e.target.value })}
                className="input"
                placeholder="e.g. Consulting, Hair Salon"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                City / Location
              </label>
              <input
                type="text"
                value={profileForm.location_city}
                onChange={e => setProfileForm({ ...profileForm, location_city: e.target.value })}
                className="input"
                placeholder="e.g. New York, Online"
              />
            </div>
            <button type="submit" className="btn-primary" disabled={updateSettingsMutation.isPending}>
              Save Profile
            </button>
          </div>
        </form>
      )}

      {/* Payment Tab */}
      {activeTab === 'payment' && (
        <form onSubmit={handlePaymentSubmit} className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
          <h2 className="text-xl font-display font-semibold text-white mb-6">
            Payment & Booking Rules
          </h2>
          <div className="space-y-6 max-w-md">

            <div className="p-4 bg-gray-800/50 rounded-lg border border-gray-700">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={paymentForm.payment_required}
                  onChange={e => setPaymentForm({ ...paymentForm, payment_required: e.target.checked })}
                  className="w-5 h-5 rounded border-gray-600 bg-gray-700 text-primary-500 focus:ring-primary-500/50 focus:ring-offset-0"
                />
                <div>
                  <span className="text-white font-medium block">Require Payment Upfront</span>
                  <span className="text-gray-400 text-xs block">Redirect customers to pay before confirming.</span>
                </div>
              </label>
            </div>

            {paymentForm.payment_required && (
              <div className="animate-fade-in space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Payment Link (Stripe/PayPal URL)
                  </label>
                  <input
                    type="url"
                    value={paymentForm.payment_link}
                    onChange={e => setPaymentForm({ ...paymentForm, payment_link: e.target.value })}
                    className="input"
                    placeholder="https://buy.stripe.com/..."
                    required={paymentForm.payment_required}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Hold Duration (Minutes)
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {[15, 30, 60].map(mins => (
                      <button
                        key={mins}
                        type="button"
                        onClick={() => setPaymentForm({ ...paymentForm, payment_hold_minutes: mins })}
                        className={`py-2 rounded-lg text-sm border transition-colors ${paymentForm.payment_hold_minutes === mins
                          ? 'bg-primary-500/20 border-primary-500 text-primary-400'
                          : 'border-gray-700 text-gray-400 hover:border-gray-600'
                          }`}
                      >
                        {mins} mins
                      </button>
                    ))}
                  </div>
                  <p className="text-gray-500 text-xs mt-2">
                    Unconfirmed bookings will expire after this time.
                  </p>
                </div>
              </div>
            )}

            <button type="submit" className="btn-primary" disabled={updateSettingsMutation.isPending}>
              Save Rules
            </button>
          </div>
        </form>
      )}
    </div>
  )
}


