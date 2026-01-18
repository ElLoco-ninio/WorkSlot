import { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';

export default function Login() {
    const navigate = useNavigate();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [status, setStatus] = useState<'idle' | 'loading' | 'error'>('idle');

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setStatus('loading');

        try {
            const formData = new FormData();
            formData.append('username', email);
            formData.append('password', password);

            const res = await axios.post('/api/login', formData);
            const { access_token, is_admin } = res.data;

            localStorage.setItem('token', access_token);
            localStorage.setItem('is_admin', String(is_admin));

            if (is_admin) {
                navigate('/admin');
            } else {
                navigate('/dashboard');
            }
        } catch (err) {
            console.error(err);
            setStatus('error');
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
            <div className="bg-white p-8 rounded-xl shadow-sm border w-full max-w-sm">
                <h1 className="text-2xl font-bold mb-6 text-center">Login</h1>

                <form onSubmit={handleLogin} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium mb-1">Email</label>
                        <input
                            type="email"
                            required
                            className="w-full border rounded p-2"
                            value={email}
                            onChange={e => setEmail(e.target.value)}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium mb-1">Password</label>
                        <input
                            type="password"
                            required
                            className="w-full border rounded p-2"
                            value={password}
                            onChange={e => setPassword(e.target.value)}
                        />
                    </div>

                    {status === 'error' && (
                        <p className="text-red-500 text-sm">Invalid credentials or inactive account.</p>
                    )}

                    <button
                        type="submit"
                        disabled={status === 'loading'}
                        className="w-full bg-blue-600 text-white py-2 rounded font-medium hover:bg-blue-700 disabled:opacity-50 flex justify-center"
                    >
                        {status === 'loading' ? <Loader2 className="animate-spin" /> : 'Sign In'}
                    </button>
                </form>

                <div className="mt-4 text-center">
                    <a href="/" className="text-sm text-gray-500 hover:text-gray-900">← Back to Home</a>
                </div>
            </div>
        </div>
    );
}
