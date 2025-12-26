import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { bookingsApi } from '../api/client'
import { format } from 'date-fns'
import toast from 'react-hot-toast'
import {
  CheckCircle,
  XCircle,
  Clock,
  UserCheck,
  ChevronLeft,
  ChevronRight,
  Loader2,
  DollarSign,
} from 'lucide-react'

export default function Bookings() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')
  const [selectedBooking, setSelectedBooking] = useState<any>(null)
  const [declineReason, setDeclineReason] = useState('')
  const [showDeclineModal, setShowDeclineModal] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['bookings', page, statusFilter],
    queryFn: () =>
      bookingsApi.list({ page, size: 10, status_filter: statusFilter || undefined }).then((r) => r.data),
  })

  const approveMutation = useMutation({
    mutationFn: (id: string) => bookingsApi.approve(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookings'] })
      toast.success('Booking approved!')
    },
    onError: () => toast.error('Failed to approve booking'),
  })

  const declineMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      bookingsApi.decline(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookings'] })
      setShowDeclineModal(false)
      setDeclineReason('')
      toast.success('Booking declined')
    },
    onError: () => toast.error('Failed to decline booking'),
  })

  const arriveMutation = useMutation({
    mutationFn: (id: string) => bookingsApi.arrive(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookings'] })
      toast.success('Arrival confirmed!')
    },
    onError: () => toast.error('Failed to mark arrival'),
  })

  const completeMutation = useMutation({
    mutationFn: (id: string) => bookingsApi.complete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookings'] })
      toast.success('Booking completed!')
    },
    onError: () => toast.error('Failed to complete booking'),
  })

  const confirmPaymentMutation = useMutation({
    mutationFn: (id: string) => bookingsApi.confirmPayment(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookings'] })
      toast.success('Payment confirmed!')
    },
    onError: (err: any) => toast.error(err.response?.data?.detail || 'Failed to confirm payment'),
  })

  const getStatusClass = (status: string) => {
    const classes: Record<string, string> = {
      pending: 'status-pending',
      awaiting_payment: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
      expired: 'status-cancelled',
      verified: 'status-verified',
      confirmed: 'status-confirmed',
      arrived: 'status-confirmed',
      declined: 'status-declined',
      completed: 'status-completed',
      cancelled: 'status-cancelled',
    }
    return classes[status] || 'status-pending'
  }

  const statusOptions = [
    { value: '', label: 'All Status' },
    { value: 'awaiting_payment', label: 'Awaiting Payment' },
    { value: 'pending', label: 'Pending' },
    { value: 'verified', label: 'Verified' },
    { value: 'confirmed', label: 'Confirmed' },
    { value: 'arrived', label: 'Arrived' },
    { value: 'completed', label: 'Completed' },
    { value: 'declined', label: 'Declined' },
    { value: 'cancelled', label: 'Cancelled' },
  ]

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-display font-bold text-white">Bookings</h1>
          <p className="text-gray-400">Manage your customer appointments</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4">
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value)
            setPage(1)
          }}
          className="input w-48"
        >
          {statusOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Bookings table */}
      <div className="bg-gray-900/50 border border-gray-800 rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
          </div>
        ) : data?.items?.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-800/50">
                  <tr>
                    <th className="text-left px-6 py-4 text-sm font-medium text-gray-400">
                      Customer
                    </th>
                    <th className="text-left px-6 py-4 text-sm font-medium text-gray-400">
                      Date & Time
                    </th>
                    <th className="text-left px-6 py-4 text-sm font-medium text-gray-400">
                      Status
                    </th>
                    <th className="text-right px-6 py-4 text-sm font-medium text-gray-400">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {data.items.map((booking: any) => (
                    <tr key={booking.id} className="hover:bg-gray-800/30 transition-colors">
                      <td className="px-6 py-4">
                        <div>
                          <p className="text-white font-medium">{booking.customer_name}</p>
                          <p className="text-gray-400 text-sm">{booking.customer_email}</p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div>
                          <p className="text-white">
                            {format(new Date(booking.slot_start), 'MMM d, yyyy')}
                          </p>
                          <p className="text-gray-400 text-sm">
                            {format(new Date(booking.slot_start), 'h:mm a')} -{' '}
                            {format(new Date(booking.slot_end), 'h:mm a')}
                          </p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusClass(
                            booking.status
                          )}`}
                        >
                          {booking.status}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center justify-end gap-2">
                          {(booking.status === 'pending' || booking.status === 'verified') && (
                            <>
                              <button
                                onClick={() => approveMutation.mutate(booking.id)}
                                disabled={approveMutation.isPending}
                                className="p-2 text-emerald-400 hover:bg-emerald-500/20 rounded-lg transition-colors"
                                title="Approve"
                              >
                                <CheckCircle className="w-5 h-5" />
                              </button>
                              <button
                                onClick={() => {
                                  setSelectedBooking(booking)
                                  setShowDeclineModal(true)
                                }}
                                className="p-2 text-red-400 hover:bg-red-500/20 rounded-lg transition-colors"
                                title="Decline"
                              >
                                <XCircle className="w-5 h-5" />
                              </button>
                            </>
                          )}
                          {booking.status === 'awaiting_payment' && (
                            <button
                              onClick={() => confirmPaymentMutation.mutate(booking.id)}
                              disabled={confirmPaymentMutation.isPending}
                              className="p-2 text-yellow-400 hover:bg-yellow-500/20 rounded-lg transition-colors"
                              title="Confirm Payment Received"
                            >
                              <DollarSign className="w-5 h-5" />
                            </button>
                          )}
                          {booking.status === 'confirmed' && (
                            <>
                              <button
                                onClick={() => arriveMutation.mutate(booking.id)}
                                disabled={arriveMutation.isPending}
                                className="p-2 text-blue-400 hover:bg-blue-500/20 rounded-lg transition-colors"
                                title="Mark Arrived"
                              >
                                <UserCheck className="w-5 h-5" />
                              </button>
                              <button
                                onClick={() => completeMutation.mutate(booking.id)}
                                disabled={completeMutation.isPending}
                                className="p-2 text-purple-400 hover:bg-purple-500/20 rounded-lg transition-colors"
                                title="Mark Complete"
                              >
                                <CheckCircle className="w-5 h-5" />
                              </button>
                            </>
                          )}
                          {booking.status === 'arrived' && (
                            <button
                              onClick={() => completeMutation.mutate(booking.id)}
                              disabled={completeMutation.isPending}
                              className="p-2 text-purple-400 hover:bg-purple-500/20 rounded-lg transition-colors"
                              title="Mark Complete"
                            >
                              <CheckCircle className="w-5 h-5" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {data.pages > 1 && (
              <div className="flex items-center justify-between px-6 py-4 border-t border-gray-800">
                <p className="text-gray-400 text-sm">
                  Page {data.page} of {data.pages} ({data.total} total)
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="p-2 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                    disabled={page === data.pages}
                    className="p-2 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronRight className="w-5 h-5" />
                  </button>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-20">
            <Clock className="w-12 h-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">No bookings found</p>
          </div>
        )}
      </div>

      {/* Decline Modal */}
      {showDeclineModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 w-full max-w-md">
            <h3 className="text-xl font-display font-semibold text-white mb-4">
              Decline Booking
            </h3>
            <p className="text-gray-400 mb-4">
              Please provide a reason for declining this booking. The customer will be notified.
            </p>
            <textarea
              value={declineReason}
              onChange={(e) => setDeclineReason(e.target.value)}
              className="input h-24 resize-none mb-4"
              placeholder="Enter reason..."
            />
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => {
                  setShowDeclineModal(false)
                  setDeclineReason('')
                }}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={() =>
                  declineMutation.mutate({
                    id: selectedBooking.id,
                    reason: declineReason,
                  })
                }
                disabled={!declineReason.trim() || declineMutation.isPending}
                className="px-4 py-2 rounded-lg bg-red-500 hover:bg-red-600 text-white font-medium disabled:opacity-50"
              >
                {declineMutation.isPending ? 'Declining...' : 'Decline Booking'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

