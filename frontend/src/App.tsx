import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './LandingPage';
import Login from './Login';
import AdminDashboard from './AdminDashboard';
import ProviderDashboard from './ProviderDashboard';
import BookingPage from './BookingPage';

// Admin Guard
const ProtectedAdminRoute = ({ children }: { children: React.ReactNode }) => {
    const token = localStorage.getItem('token');
    const isAdmin = localStorage.getItem('is_admin') === 'true';
    if (!token) return <Navigate to="/login" />;
    if (!isAdmin) return <Navigate to="/dashboard" />;
    return <>{children}</>;
};

// Protected Guard for Providers
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
    const token = localStorage.getItem('token');
    const isAdmin = localStorage.getItem('is_admin') === 'true';

    if (!token) return <Navigate to="/login" />;
    if (isAdmin) return <Navigate to="/admin" />;
    return <>{children}</>;
};

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<LandingPage />} />
                <Route path="/login" element={<Login />} />

                <Route path="/admin" element={<ProtectedAdminRoute><AdminDashboard /></ProtectedAdminRoute>} />

                <Route path="/book/:slug" element={<BookingPage />} />

                <Route path="/dashboard" element={<ProtectedRoute><ProviderDashboard /></ProtectedRoute>} />
            </Routes>
        </Router>
    );
}

export default App;
