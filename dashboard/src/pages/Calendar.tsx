import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { bookingsApi } from '../api/client'
import {
  format,
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  addDays,
  addMonths,
  subMonths,
  isSameMonth,
  isSameDay,
  parseISO,
} from 'date-fns'
import { ChevronLeft, ChevronRight, Loader2 } from 'lucide-react'

export default function Calendar() {
  const [currentMonth, setCurrentMonth] = useState(new Date())
  const [selectedDate, setSelectedDate] = useState(new Date())

  const monthStart = startOfMonth(currentMonth)
  const monthEnd = endOfMonth(currentMonth)
  const calendarStart = startOfWeek(monthStart)
  const calendarEnd = endOfWeek(monthEnd)

  const { data: bookingsData, isLoading } = useQuery({
    queryKey: ['bookings', 'calendar', format(monthStart, 'yyyy-MM')],
    queryFn: () =>
      bookingsApi
        .list({
          size: 100,
        })
        .then((r) => r.data.items),
  })

  const getBookingsForDate = (date: Date) => {
    if (!bookingsData) return []
    return bookingsData.filter((booking: any) =>
      isSameDay(parseISO(booking.slot_start), date)
    )
  }

  const renderDays = () => {
    const days = []
    let day = calendarStart

    while (day <= calendarEnd) {
      const currentDay = day
      const bookings = getBookingsForDate(currentDay)
      const isCurrentMonth = isSameMonth(currentDay, currentMonth)
      const isSelected = isSameDay(currentDay, selectedDate)
      const isToday = isSameDay(currentDay, new Date())

      days.push(
        <div
          key={currentDay.toISOString()}
          onClick={() => setSelectedDate(currentDay)}
          className={`
            min-h-[100px] p-2 border-b border-r border-gray-800 cursor-pointer transition-colors
            ${isCurrentMonth ? 'bg-gray-900/30' : 'bg-gray-900/10'}
            ${isSelected ? 'ring-2 ring-primary-500 ring-inset' : ''}
            hover:bg-gray-800/50
          `}
        >
          <div className="flex items-center justify-between mb-1">
            <span
              className={`
                text-sm font-medium
                ${isToday ? 'w-7 h-7 flex items-center justify-center rounded-full bg-primary-500 text-white' : ''}
                ${isCurrentMonth ? 'text-white' : 'text-gray-600'}
              `}
            >
              {format(currentDay, 'd')}
            </span>
            {bookings.length > 0 && (
              <span className="text-xs text-primary-400">
                {bookings.length}
              </span>
            )}
          </div>
          <div className="space-y-1">
            {bookings.slice(0, 3).map((booking: any) => (
              <div
                key={booking.id}
                className={`
                  text-xs px-2 py-1 rounded truncate
                  ${booking.status === 'confirmed' ? 'bg-emerald-500/20 text-emerald-400' : ''}
                  ${booking.status === 'pending' || booking.status === 'verified' ? 'bg-amber-500/20 text-amber-400' : ''}
                  ${booking.status === 'completed' ? 'bg-purple-500/20 text-purple-400' : ''}
                  ${booking.status === 'declined' || booking.status === 'cancelled' ? 'bg-gray-500/20 text-gray-400' : ''}
                `}
              >
                {format(parseISO(booking.slot_start), 'h:mm a')} - {booking.customer_name}
              </div>
            ))}
            {bookings.length > 3 && (
              <div className="text-xs text-gray-500 px-2">
                +{bookings.length - 3} more
              </div>
            )}
          </div>
        </div>
      )

      day = addDays(day, 1)
    }

    return days
  }

  const selectedBookings = getBookingsForDate(selectedDate)

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-display font-bold text-white">Calendar</h1>
          <p className="text-gray-400">View your bookings by date</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Calendar */}
        <div className="lg:col-span-3 bg-gray-900/50 border border-gray-800 rounded-xl overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-800">
            <button
              onClick={() => setCurrentMonth(subMonths(currentMonth, 1))}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <h2 className="text-xl font-display font-semibold text-white">
              {format(currentMonth, 'MMMM yyyy')}
            </h2>
            <button
              onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>

          {/* Day headers */}
          <div className="grid grid-cols-7 border-b border-gray-800">
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
              <div
                key={day}
                className="py-3 text-center text-sm font-medium text-gray-400 border-r border-gray-800 last:border-r-0"
              >
                {day}
              </div>
            ))}
          </div>

          {/* Calendar grid */}
          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
            </div>
          ) : (
            <div className="grid grid-cols-7">{renderDays()}</div>
          )}
        </div>

        {/* Selected date details */}
        <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
          <h3 className="text-lg font-display font-semibold text-white mb-4">
            {format(selectedDate, 'EEEE, MMMM d')}
          </h3>

          {selectedBookings.length > 0 ? (
            <div className="space-y-3">
              {selectedBookings.map((booking: any) => (
                <div
                  key={booking.id}
                  className="p-4 bg-gray-800/50 rounded-lg"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-400">
                      {format(parseISO(booking.slot_start), 'h:mm a')} -{' '}
                      {format(parseISO(booking.slot_end), 'h:mm a')}
                    </span>
                    <span
                      className={`
                        px-2 py-0.5 rounded text-xs font-medium
                        ${booking.status === 'confirmed' ? 'bg-emerald-500/20 text-emerald-400' : ''}
                        ${booking.status === 'pending' || booking.status === 'verified' ? 'bg-amber-500/20 text-amber-400' : ''}
                        ${booking.status === 'completed' ? 'bg-purple-500/20 text-purple-400' : ''}
                      `}
                    >
                      {booking.status}
                    </span>
                  </div>
                  <p className="text-white font-medium">{booking.customer_name}</p>
                  <p className="text-gray-400 text-sm">{booking.customer_email}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">
              No bookings for this date
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

