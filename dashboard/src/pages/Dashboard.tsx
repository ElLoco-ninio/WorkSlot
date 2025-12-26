import { useQuery } from '@tanstack/react-query'
import { providerApi, bookingsApi } from '../api/client'
import { useAuthStore } from '../stores/authStore'
import { format } from 'date-fns'
import {
  CalendarDays,
  Clock,
  CheckCircle2,
  TrendingUp,
  ArrowRight,
  Loader2,
} from 'lucide-react'
import { Link } from 'react-router-dom'

export default function Dashboard() {
  const { user } = useAuthStore()

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: () => providerApi.getStats().then((r) => r.data),
  })

  const { data: subscription } = useQuery({
    queryKey: ['subscription'],
    queryFn: () => providerApi.getSubscription().then((r) => r.data),
  })

  const { data: todayBookings, isLoading: todayLoading } = useQuery({
    queryKey: ['bookings', 'today'],
    queryFn: () => bookingsApi.getToday().then((r) => r.data),
  })

  const { data: upcomingBookings } = useQuery({
    queryKey: ['bookings', 'upcoming'],
    queryFn: () => bookingsApi.getUpcoming(5).then((r) => r.data),
  })

  const statCards = [
    {
      label: "Today's Bookings",
      value: stats?.total_today || 0,
      icon: CalendarDays,
      color: 'from-blue-500 to-cyan-500',
    },
    {
      label: 'Pending Review',
      value: stats?.total_pending || 0,
      icon: Clock,
      color: 'from-amber-500 to-orange-500',
    },
    {
      label: 'Confirmed',
      value: stats?.total_confirmed || 0,
      icon: CheckCircle2,
      color: 'from-emerald-500 to-green-500',
    },
    {
      label: 'This Month',
      value: stats?.total_this_month || 0,
      icon: TrendingUp,
      color: 'from-purple-500 to-pink-500',
    },
  ]

  const getStatusClass = (status: string) => {
    const classes: Record<string, string> = {
      pending: 'status-pending',
      verified: 'status-verified',
      confirmed: 'status-confirmed',
      declined: 'status-declined',
      completed: 'status-completed',
      cancelled: 'status-cancelled',
    }
    return classes[status] || 'status-pending'
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-display font-bold text-white">
          Welcome back, {user?.business_name}
        </h1>
        <p className="text-gray-400 mt-1">
          Here's what's happening with your bookings
        </p>
      </div>

      {/* Subscription banner */}
      {subscription && subscription.plan_type === 'free' && (
        <div className="bg-gradient-to-r from-primary-500/20 to-accent-500/20 border border-primary-500/30 rounded-xl p-4 flex items-center justify-between">
          <div>
            <p className="text-white font-medium">Upgrade to unlock API access</p>
            <p className="text-gray-400 text-sm">Get your embeddable calendar widget</p>
          </div>
          <Link
            to="/settings"
            className="btn-primary px-4 py-2 text-sm flex items-center gap-2"
          >
            Upgrade Now
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      )}

      {/* Stats cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat, index) => (
          <div
            key={stat.label}
            className="bg-gray-900/50 border border-gray-800 rounded-xl p-6 card-hover"
            style={{ animationDelay: `${index * 0.1}s` }}
          >
            <div className="flex items-center justify-between mb-4">
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${stat.color} flex items-center justify-center`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
              {statsLoading ? (
                <Loader2 className="w-5 h-5 text-gray-500 animate-spin" />
              ) : (
                <span className="text-3xl font-display font-bold text-white">
                  {stat.value}
                </span>
              )}
            </div>
            <p className="text-gray-400 text-sm">{stat.label}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Today's Schedule */}
        <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-display font-semibold text-white">
              Today's Schedule
            </h2>
            <Link to="/calendar" className="text-primary-400 hover:text-primary-300 text-sm font-medium">
              View Calendar →
            </Link>
          </div>

          {todayLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
            </div>
          ) : todayBookings?.length > 0 ? (
            <div className="space-y-3">
              {todayBookings.map((booking: any) => (
                <div
                  key={booking.id}
                  className="flex items-center gap-4 p-4 bg-gray-800/50 rounded-lg"
                >
                  <div className="w-12 h-12 rounded-lg bg-primary-500/20 flex items-center justify-center">
                    <Clock className="w-5 h-5 text-primary-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-medium truncate">
                      {booking.customer_name}
                    </p>
                    <p className="text-gray-400 text-sm">
                      {format(new Date(booking.slot_start), 'h:mm a')} -{' '}
                      {format(new Date(booking.slot_end), 'h:mm a')}
                    </p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusClass(booking.status)}`}>
                    {booking.status}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <CalendarDays className="w-12 h-12 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-400">No bookings scheduled for today</p>
            </div>
          )}
        </div>

        {/* Upcoming Bookings */}
        <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-display font-semibold text-white">
              Upcoming Bookings
            </h2>
            <Link to="/bookings" className="text-primary-400 hover:text-primary-300 text-sm font-medium">
              View All →
            </Link>
          </div>

          {upcomingBookings?.length > 0 ? (
            <div className="space-y-3">
              {upcomingBookings.map((booking: any) => (
                <div
                  key={booking.id}
                  className="flex items-center gap-4 p-4 bg-gray-800/50 rounded-lg"
                >
                  <div className="text-center min-w-[48px]">
                    <p className="text-2xl font-bold text-white">
                      {format(new Date(booking.slot_start), 'd')}
                    </p>
                    <p className="text-xs text-gray-400 uppercase">
                      {format(new Date(booking.slot_start), 'MMM')}
                    </p>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-medium truncate">
                      {booking.customer_name}
                    </p>
                    <p className="text-gray-400 text-sm">
                      {format(new Date(booking.slot_start), 'EEEE, h:mm a')}
                    </p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusClass(booking.status)}`}>
                    {booking.status}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <CheckCircle2 className="w-12 h-12 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-400">No upcoming bookings</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

