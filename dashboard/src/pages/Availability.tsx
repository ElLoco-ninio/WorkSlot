import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { availabilityApi } from '../api/client'
import toast from 'react-hot-toast'
import { Clock, Loader2, Save, RotateCcw, CalendarX, Trash2 } from 'lucide-react'
import { format, parseISO } from 'date-fns'

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

export default function Availability() {
  const queryClient = useQueryClient()
  const [schedule, setSchedule] = useState<any[]>([])
  const [newBlockedDate, setNewBlockedDate] = useState('')
  const [blockedReason, setBlockedReason] = useState('')

  const { isLoading } = useQuery({
    queryKey: ['availability'],
    queryFn: async () => {
      const response = await availabilityApi.getWeekly()
      const data = response.data
      if (data?.schedule) {
        setSchedule(data.schedule)
      }
      return data
    },
  })

  const { data: blockedDates } = useQuery({
    queryKey: ['blocked-dates'],
    queryFn: () => availabilityApi.getBlocked().then((r) => r.data),
  })

  const updateMutation = useMutation({
    mutationFn: (dayData: any) => availabilityApi.updateDay(dayData.day_of_week, dayData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['availability'] })
      toast.success('Schedule updated')
    },
    onError: () => toast.error('Failed to update schedule'),
  })

  const resetMutation = useMutation({
    mutationFn: () => availabilityApi.reset(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['availability'] })
      toast.success('Schedule reset to default')
    },
    onError: () => toast.error('Failed to reset schedule'),
  })

  const addBlockedMutation = useMutation({
    mutationFn: (data: { date: string; reason?: string }) => availabilityApi.addBlocked(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blocked-dates'] })
      setNewBlockedDate('')
      setBlockedReason('')
      toast.success('Date blocked')
    },
    onError: () => toast.error('Failed to block date'),
  })

  const removeBlockedMutation = useMutation({
    mutationFn: (id: string) => availabilityApi.removeBlocked(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blocked-dates'] })
      toast.success('Blocked date removed')
    },
    onError: () => toast.error('Failed to remove blocked date'),
  })

  const handleScheduleChange = (dayIndex: number, field: string, value: any) => {
    const newSchedule = [...schedule]
    const dayData = newSchedule.find((s) => s.day_of_week === dayIndex)
    if (dayData) {
      dayData[field] = value
      setSchedule(newSchedule)
    }
  }

  const handleSaveDay = (dayIndex: number) => {
    const dayData = schedule.find((s) => s.day_of_week === dayIndex)
    if (dayData) {
      updateMutation.mutate(dayData)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-display font-bold text-white">Availability</h1>
          <p className="text-gray-400">Configure your working hours</p>
        </div>
        <button
          onClick={() => resetMutation.mutate()}
          disabled={resetMutation.isPending}
          className="btn-secondary flex items-center gap-2"
        >
          <RotateCcw className="w-4 h-4" />
          Reset to Default
        </button>
      </div>

      {/* Weekly Schedule */}
      <div className="bg-gray-900/50 border border-gray-800 rounded-xl overflow-hidden">
        <div className="p-6 border-b border-gray-800">
          <h2 className="text-xl font-display font-semibold text-white flex items-center gap-2">
            <Clock className="w-5 h-5 text-primary-400" />
            Weekly Schedule
          </h2>
        </div>
        <div className="divide-y divide-gray-800">
          {DAYS.map((dayName, index) => {
            const dayData = schedule.find((s) => s.day_of_week === index) || {
              day_of_week: index,
              start_time: '09:00:00',
              end_time: '17:00:00',
              slot_duration_minutes: 60,
              is_available: true,
            }

            return (
              <div key={dayName} className="p-6">
                <div className="flex flex-wrap items-center gap-4">
                  <div className="w-28">
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={dayData.is_available}
                        onChange={(e) =>
                          handleScheduleChange(index, 'is_available', e.target.checked)
                        }
                        className="w-5 h-5 rounded border-gray-600 bg-gray-800 text-primary-500 focus:ring-primary-500"
                      />
                      <span className="text-white font-medium">{dayName}</span>
                    </label>
                  </div>

                  {dayData.is_available && (
                    <>
                      <div className="flex items-center gap-2">
                        <input
                          type="time"
                          value={dayData.start_time?.slice(0, 5) || '09:00'}
                          onChange={(e) =>
                            handleScheduleChange(index, 'start_time', e.target.value + ':00')
                          }
                          className="input w-32"
                        />
                        <span className="text-gray-400">to</span>
                        <input
                          type="time"
                          value={dayData.end_time?.slice(0, 5) || '17:00'}
                          onChange={(e) =>
                            handleScheduleChange(index, 'end_time', e.target.value + ':00')
                          }
                          className="input w-32"
                        />
                      </div>

                      <div className="flex items-center gap-2">
                        <span className="text-gray-400 text-sm">Slot:</span>
                        <select
                          value={dayData.slot_duration_minutes || 60}
                          onChange={(e) =>
                            handleScheduleChange(
                              index,
                              'slot_duration_minutes',
                              parseInt(e.target.value)
                            )
                          }
                          className="input w-24"
                        >
                          <option value={15}>15 min</option>
                          <option value={30}>30 min</option>
                          <option value={45}>45 min</option>
                          <option value={60}>1 hour</option>
                          <option value={90}>1.5 hours</option>
                          <option value={120}>2 hours</option>
                        </select>
                      </div>

                      <button
                        onClick={() => handleSaveDay(index)}
                        disabled={updateMutation.isPending}
                        className="p-2 text-primary-400 hover:bg-primary-500/20 rounded-lg transition-colors"
                      >
                        <Save className="w-5 h-5" />
                      </button>
                    </>
                  )}

                  {!dayData.is_available && (
                    <span className="text-gray-500 text-sm">Unavailable</span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Blocked Dates */}
      <div className="bg-gray-900/50 border border-gray-800 rounded-xl overflow-hidden">
        <div className="p-6 border-b border-gray-800">
          <h2 className="text-xl font-display font-semibold text-white flex items-center gap-2">
            <CalendarX className="w-5 h-5 text-red-400" />
            Blocked Dates
          </h2>
          <p className="text-gray-400 text-sm mt-1">
            Block specific dates when you're unavailable (holidays, vacations, etc.)
          </p>
        </div>

        <div className="p-6">
          {/* Add blocked date form */}
          <div className="flex flex-wrap gap-4 mb-6">
            <input
              type="date"
              value={newBlockedDate}
              onChange={(e) => setNewBlockedDate(e.target.value)}
              className="input w-48"
              min={format(new Date(), 'yyyy-MM-dd')}
            />
            <input
              type="text"
              value={blockedReason}
              onChange={(e) => setBlockedReason(e.target.value)}
              placeholder="Reason (optional)"
              className="input flex-1 min-w-[200px]"
            />
            <button
              onClick={() =>
                addBlockedMutation.mutate({ date: newBlockedDate, reason: blockedReason })
              }
              disabled={!newBlockedDate || addBlockedMutation.isPending}
              className="btn-primary"
            >
              Block Date
            </button>
          </div>

          {/* Blocked dates list */}
          {blockedDates?.length > 0 ? (
            <div className="space-y-2">
              {blockedDates.map((blocked: any) => (
                <div
                  key={blocked.id}
                  className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg"
                >
                  <div>
                    <p className="text-white font-medium">
                      {format(parseISO(blocked.date), 'EEEE, MMMM d, yyyy')}
                    </p>
                    {blocked.reason && (
                      <p className="text-gray-400 text-sm">{blocked.reason}</p>
                    )}
                  </div>
                  <button
                    onClick={() => removeBlockedMutation.mutate(blocked.id)}
                    disabled={removeBlockedMutation.isPending}
                    className="p-2 text-red-400 hover:bg-red-500/20 rounded-lg transition-colors"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No blocked dates</p>
          )}
        </div>
      </div>
    </div>
  )
}

