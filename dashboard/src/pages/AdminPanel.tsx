import { useEffect, useState } from 'react'
import { useAuthStore } from '../stores/authStore'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import {
  Users, ClipboardList, Key, TrendingUp, Shield, Search,
  CheckCircle, XCircle, AlertCircle, Activity, RefreshCw
} from 'lucide-react'
import toast from 'react-hot-toast'

interface Stats {
  total_users: number
  total_bookings: number
  active_subscriptions: number
  total_api_keys: number
  recent_users: number
}

interface User {
  id: string
  email: string
  business_name: string
  is_active: boolean
  is_verified: boolean
  is_admin: boolean
  created_at: string
  subscription?: {
    plan_type: string
    status: string
  }
}

interface Booking {
  id: string
  customer_name: string
  customer_email: string
  slot_start: string
  slot_end: string
  status: string
  created_at: string
}

interface SystemHealth {
  database: string
  recent_errors_24h: number
  inactive_users: number
  timestamp: string
}

type Tab = 'overview' | 'users' | 'bookings' | 'health'

export default function AdminPanel() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<Tab>('overview')
  const [stats, setStats] = useState<Stats | null>(null)
  const [users, setUsers] = useState<User[]>([])
  const [bookings, setBookings] = useState<Booking[]>([])
  const [health, setHealth] = useState<SystemHealth | null>(null)
  const [loading, setLoading] = useState(true)
  const [usersLoading, setUsersLoading] = useState(false)
  const [bookingsLoading, setBookingsLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [usersPage, setUsersPage] = useState(1)

  useEffect(() => {
    if (!user?.is_admin) {
      toast.error('Admin access required')
      navigate('/')
      return
    }

    loadStats()
    if (activeTab === 'users') loadUsers()
    if (activeTab === 'bookings') loadBookings()
    if (activeTab === 'health') loadHealth()
  }, [user, navigate, activeTab])

  const loadStats = async () => {
    try {
      const response = await api.get('/api/admin/stats')
      setStats(response.data)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to load stats')
    } finally {
      setLoading(false)
    }
  }

  const loadUsers = async () => {
    setUsersLoading(true)
    try {
      const params: any = { page: usersPage, size: 20 }
      if (searchQuery) params.search = searchQuery
      const response = await api.get('/api/admin/users', { params })
      setUsers(response.data.items || [])
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to load users')
    } finally {
      setUsersLoading(false)
    }
  }

  const loadBookings = async () => {
    setBookingsLoading(true)
    try {
      const response = await api.get('/api/admin/bookings', { params: { page: 1, size: 50 } })
      setBookings(response.data.items || [])
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to load bookings')
    } finally {
      setBookingsLoading(false)
    }
  }

  const loadHealth = async () => {
    try {
      const response = await api.get('/api/admin/health')
      setHealth(response.data)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to load system health')
    }
  }

  const toggleUserActive = async (userId: string, currentStatus: boolean) => {
    try {
      await api.patch(`/api/admin/users/${userId}/activate?is_active=${!currentStatus}`)
      toast.success(`User ${!currentStatus ? 'activated' : 'deactivated'}`)
      loadUsers()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to update user')
    }
  }

  if (!user?.is_admin) {
    return null
  }

  const tabs = [
    { id: 'overview' as Tab, label: 'Overview', icon: Shield },
    { id: 'users' as Tab, label: 'Users', icon: Users },
    { id: 'bookings' as Tab, label: 'Bookings', icon: ClipboardList },
    { id: 'health' as Tab, label: 'System Health', icon: Activity },
  ]

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Shield className="w-8 h-8 text-primary-400" />
            Admin Panel
          </h1>
          <p className="text-gray-400 mt-2">Manage your WorkSlot platform</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-700">
        {tabs.map((tab) => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${activeTab === tab.id
                  ? 'border-primary-500 text-primary-400'
                  : 'border-transparent text-gray-400 hover:text-white'
                }`}
            >
              <Icon className="w-4 h-4" />
              <span className="font-medium">{tab.label}</span>
            </button>
          )
        })}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <>
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
            </div>
          ) : stats && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-primary-500/20 rounded-lg">
                    <Users className="w-6 h-6 text-primary-400" />
                  </div>
                </div>
                <h3 className="text-gray-400 text-sm font-medium mb-1">Total Users</h3>
                <p className="text-3xl font-bold text-white">{stats.total_users}</p>
                {stats.recent_users > 0 && (
                  <p className="text-xs text-green-400 mt-1">+{stats.recent_users} this week</p>
                )}
              </div>

              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-accent-500/20 rounded-lg">
                    <ClipboardList className="w-6 h-6 text-accent-400" />
                  </div>
                </div>
                <h3 className="text-gray-400 text-sm font-medium mb-1">Total Bookings</h3>
                <p className="text-3xl font-bold text-white">{stats.total_bookings}</p>
              </div>

              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-green-500/20 rounded-lg">
                    <TrendingUp className="w-6 h-6 text-green-400" />
                  </div>
                </div>
                <h3 className="text-gray-400 text-sm font-medium mb-1">Active Subscriptions</h3>
                <p className="text-3xl font-bold text-white">{stats.active_subscriptions}</p>
              </div>

              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-purple-500/20 rounded-lg">
                    <Key className="w-6 h-6 text-purple-400" />
                  </div>
                </div>
                <h3 className="text-gray-400 text-sm font-medium mb-1">Total API Keys</h3>
                <p className="text-3xl font-bold text-white">{stats.total_api_keys}</p>
              </div>

              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-blue-500/20 rounded-lg">
                    <Activity className="w-6 h-6 text-blue-400" />
                  </div>
                </div>
                <h3 className="text-gray-400 text-sm font-medium mb-1">System Status</h3>
                <p className="text-lg font-bold text-green-400">Healthy</p>
              </div>
            </div>
          )}
        </>
      )}

      {/* Users Tab */}
      {activeTab === 'users' && (
        <div className="space-y-4">
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search users by email or business name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && loadUsers()}
                className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-primary-500"
              />
            </div>
            <button
              onClick={loadUsers}
              className="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
          </div>

          {usersLoading ? (
            <div className="flex items-center justify-center py-20">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
            </div>
          ) : (
            <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-900">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Email</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Business</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Plan</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Created</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {users.map((u) => (
                      <tr key={u.id} className="hover:bg-gray-700/50">
                        <td className="px-6 py-4 text-sm text-white">{u.email}</td>
                        <td className="px-6 py-4 text-sm text-gray-300">{u.business_name}</td>
                        <td className="px-6 py-4 text-sm text-gray-300">
                          {u.subscription?.plan_type?.toUpperCase() || 'N/A'}
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            {u.is_active ? (
                              <CheckCircle className="w-4 h-4 text-green-400" />
                            ) : (
                              <XCircle className="w-4 h-4 text-red-400" />
                            )}
                            <span className={`text-sm ${u.is_active ? 'text-green-400' : 'text-red-400'}`}>
                              {u.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-400">
                          {new Date(u.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4">
                          <button
                            onClick={() => toggleUserActive(u.id, u.is_active)}
                            className={`px-3 py-1 rounded text-xs font-medium ${u.is_active
                                ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                                : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
                              }`}
                          >
                            {u.is_active ? 'Deactivate' : 'Activate'}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Bookings Tab */}
      {activeTab === 'bookings' && (
        <div className="space-y-4">
          <button
            onClick={loadBookings}
            className="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>

          {bookingsLoading ? (
            <div className="flex items-center justify-center py-20">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
            </div>
          ) : (
            <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-900">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Customer</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Email</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Date & Time</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Created</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {bookings.map((b) => (
                      <tr key={b.id} className="hover:bg-gray-700/50">
                        <td className="px-6 py-4 text-sm text-white">{b.customer_name}</td>
                        <td className="px-6 py-4 text-sm text-gray-300">{b.customer_email}</td>
                        <td className="px-6 py-4 text-sm text-gray-300">
                          {new Date(b.slot_start).toLocaleString()}
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${b.status === 'confirmed' ? 'bg-green-500/20 text-green-400' :
                              b.status === 'pending' ? 'bg-yellow-500/20 text-yellow-400' :
                                'bg-gray-500/20 text-gray-400'
                            }`}>
                            {b.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-400">
                          {new Date(b.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Health Tab */}
      {activeTab === 'health' && (
        <div className="space-y-4">
          <button
            onClick={loadHealth}
            className="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>

          {health && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <div className="flex items-center gap-3 mb-4">
                  <Activity className="w-6 h-6 text-blue-400" />
                  <h3 className="text-lg font-semibold text-white">Database</h3>
                </div>
                <p className={`text-sm ${health.database === 'healthy' ? 'text-green-400' : 'text-red-400'}`}>
                  {health.database}
                </p>
              </div>

              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <div className="flex items-center gap-3 mb-4">
                  <AlertCircle className="w-6 h-6 text-yellow-400" />
                  <h3 className="text-lg font-semibold text-white">Recent Errors (24h)</h3>
                </div>
                <p className={`text-2xl font-bold ${health.recent_errors_24h > 0 ? 'text-red-400' : 'text-green-400'}`}>
                  {health.recent_errors_24h}
                </p>
              </div>

              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <div className="flex items-center gap-3 mb-4">
                  <Users className="w-6 h-6 text-gray-400" />
                  <h3 className="text-lg font-semibold text-white">Inactive Users</h3>
                </div>
                <p className="text-2xl font-bold text-gray-300">{health.inactive_users}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
