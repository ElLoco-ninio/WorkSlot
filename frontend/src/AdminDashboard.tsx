import { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Loader2, UserPlus } from 'lucide-react';

interface AccessRequest {
    id: number;
    email: string;
    phone: string;
    business_category: string;
    city: string;
    description: string;
    created_at: string;
}

interface User {
    id: number;
    email: string;
    is_active: boolean;
    onboarding_completed: boolean;
    trial_ends_at: string;
}

export default function AdminDashboard() {
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState<'requests' | 'users'>('requests');
    const [requests, setRequests] = useState<AccessRequest[]>([]);
    const [users, setUsers] = useState<User[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    // User Creation State
    const [newUserEmail, setNewUserEmail] = useState('');
    const [isCreating, setIsCreating] = useState(false);

    useEffect(() => {
        fetchData();
    }, [activeTab]);

    const fetchData = async () => {
        setIsLoading(true);
        try {
            const token = localStorage.getItem('token');
            const config = { headers: { Authorization: `Bearer ${token}` } };

            if (activeTab === 'requests') {
                const res = await axios.get('/api/admin/access-requests', config);
                setRequests(res.data);
            } else {
                const res = await axios.get('/api/admin/users', config);
                setUsers(res.data);
            }
        } catch (err) {
            console.error(err);
            if (axios.isAxiosError(err) && err.response?.status === 401) {
                navigate('/login');
            }
        } finally {
            setIsLoading(false);
        }
    };

    const handleCreateUser = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsCreating(true);
        try {
            const token = localStorage.getItem('token');
            await axios.post('/api/admin/users', null, {
                params: { email: newUserEmail },
                headers: { Authorization: `Bearer ${token}` }
            });
            setNewUserEmail('');
            alert('User created! Check backend console for temp password.');
            fetchData(); // Refresh list
        } catch (err) {
            alert('Failed to create user');
        } finally {
            setIsCreating(false);
        }
    };

    const toggleUserStatus = async (id: number, currentStatus: boolean) => {
        try {
            const token = localStorage.getItem('token');
            await axios.put(`/api/admin/users/${id}/status`, null, {
                params: { active: !currentStatus },
                headers: { Authorization: `Bearer ${token}` }
            });
            fetchData();
        } catch (err) {
            alert('Failed to update status');
        }
    };

    const handleLogout = () => {
        localStorage.clear();
        navigate('/login');
    };

    return (
        <div className="min-h-screen bg-gray-100 p-8">
            <div className="max-w-6xl mx-auto">
                <div className="flex justify-between items-center mb-8">
                    <h1 className="text-3xl font-bold">Admin Dashboard</h1>
                    <button onClick={handleLogout} className="text-red-600 hover:text-red-800 font-medium">Logout</button>
                </div>

                {/* Tabs */}
                <div className="flex gap-4 mb-6 border-b pb-1">
                    <button
                        onClick={() => setActiveTab('requests')}
                        className={`pb-2 px-4 font-medium ${activeTab === 'requests' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'}`}
                    >
                        Access Requests
                    </button>
                    <button
                        onClick={() => setActiveTab('users')}
                        className={`pb-2 px-4 font-medium ${activeTab === 'users' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'}`}
                    >
                        Users
                    </button>
                </div>

                {/* Content */}
                {isLoading ? (
                    <div className="flex justify-center py-12"><Loader2 className="animate-spin" /></div>
                ) : (
                    <div className="bg-white rounded-xl shadow overflow-hidden">
                        {activeTab === 'requests' && (
                            <table className="w-full">
                                <thead className="bg-gray-50 border-b">
                                    <tr>
                                        <th className="text-left p-4">Date</th>
                                        <th className="text-left p-4">Email</th>
                                        <th className="text-left p-4">Category</th>
                                        <th className="text-left p-4">City</th>
                                        <th className="text-left p-4">Description</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {requests.map(r => (
                                        <tr key={r.id} className="border-b last:border-0 hover:bg-gray-50">
                                            <td className="p-4 text-sm text-gray-500">{new Date(r.created_at).toLocaleDateString()}</td>
                                            <td className="p-4 font-medium">{r.email}</td>
                                            <td className="p-4">{r.business_category}</td>
                                            <td className="p-4">{r.city}</td>
                                            <td className="p-4 text-sm text-gray-600 max-w-md truncate">{r.description}</td>
                                        </tr>
                                    ))}
                                    {requests.length === 0 && (
                                        <tr><td colSpan={5} className="p-8 text-center text-gray-500">No requests yet.</td></tr>
                                    )}
                                </tbody>
                            </table>
                        )}

                        {activeTab === 'users' && (
                            <div>
                                <div className="p-4 border-b bg-gray-50 flex gap-4 items-center">
                                    <h3 className="font-bold">Create New User</h3>
                                    <form onSubmit={handleCreateUser} className="flex gap-2 flex-1 max-w-md">
                                        <input
                                            type="email"
                                            required
                                            placeholder="User Email"
                                            className="flex-1 border rounded px-3 py-1"
                                            value={newUserEmail}
                                            onChange={e => setNewUserEmail(e.target.value)}
                                        />
                                        <button
                                            type="submit"
                                            disabled={isCreating}
                                            className="bg-green-600 text-white px-4 py-1 rounded hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
                                        >
                                            {isCreating ? <Loader2 size={16} className="animate-spin" /> : <UserPlus size={16} />}
                                            Create
                                        </button>
                                    </form>
                                </div>
                                <table className="w-full">
                                    <thead className="bg-gray-50 border-b">
                                        <tr>
                                            <th className="text-left p-4">ID</th>
                                            <th className="text-left p-4">Email</th>
                                            <th className="text-left p-4">Trial Ends</th>
                                            <th className="text-left p-4">Onboarded</th>
                                            <th className="text-left p-4">Status</th>
                                            <th className="text-left p-4">Action</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {users.map(u => (
                                            <tr key={u.id} className="border-b last:border-0 hover:bg-gray-50">
                                                <td className="p-4">{u.id}</td>
                                                <td className="p-4 font-medium">{u.email}</td>
                                                <td className="p-4">{new Date(u.trial_ends_at).toLocaleDateString()}</td>
                                                <td className="p-4">
                                                    {u.onboarding_completed
                                                        ? <span className="text-green-600 text-xs px-2 py-1 bg-green-100 rounded">Yes</span>
                                                        : <span className="text-yellow-600 text-xs px-2 py-1 bg-yellow-100 rounded">No</span>
                                                    }
                                                </td>
                                                <td className="p-4">
                                                    {u.is_active
                                                        ? <span className="text-green-600 font-bold">Active</span>
                                                        : <span className="text-red-500 font-bold">Disabled</span>
                                                    }
                                                </td>
                                                <td className="p-4">
                                                    <button
                                                        onClick={() => toggleUserStatus(u.id, u.is_active)}
                                                        className={`text-xs px-3 py-1 rounded text-white ${u.is_active ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600'}`}
                                                    >
                                                        {u.is_active ? 'Disable' : 'Enable'}
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
