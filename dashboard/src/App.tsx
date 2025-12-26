import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Bookings from './pages/Bookings'
import Calendar from './pages/Calendar'
import Availability from './pages/Availability'
import ApiKeys from './pages/ApiKeys'
import Settings from './pages/Settings'
import VerifyBooking from './pages/VerifyBooking'
import AdminPanel from './pages/AdminPanel'
import PublicBooking from './pages/PublicBooking'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user } = useAuthStore()
  if (!isAuthenticated) {
    return <Navigate to="/login" />
  }
  if (!user?.is_admin) {
    return <Navigate to="/" />
  }
  return <>{children}</>
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  return !isAuthenticated ? <>{children}</> : <Navigate to="/" />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
        <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />
        <Route path="/verify-booking" element={<VerifyBooking />} />
        <Route path="/book/:providerId" element={<PublicBooking />} />

        {/* Protected routes */}
        <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
          <Route index element={<Dashboard />} />
          <Route path="bookings" element={<Bookings />} />
          <Route path="calendar" element={<Calendar />} />
          <Route path="availability" element={<Availability />} />
          <Route path="api-keys" element={<ApiKeys />} />
          <Route path="settings" element={<Settings />} />
        </Route>

        {/* Admin routes */}
        <Route path="/admin-panel" element={<AdminRoute><Layout /></AdminRoute>}>
          <Route index element={<AdminPanel />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

