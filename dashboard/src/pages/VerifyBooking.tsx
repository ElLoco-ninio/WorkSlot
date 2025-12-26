import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { publicApi } from '../api/client'
import { CheckCircle, XCircle, Loader2 } from 'lucide-react'

export default function VerifyBooking() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!token) {
      setStatus('error')
      setMessage('Invalid verification link')
      return
    }

    publicApi
      .verifyBooking(token)
      .then(() => {
        setStatus('success')
        setMessage('Your booking has been verified! The provider will review your request and send you a confirmation.')
      })
      .catch((error) => {
        setStatus('error')
        setMessage(error.response?.data?.detail || 'Failed to verify booking. The link may have expired.')
      })
  }, [token])

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary-500/20 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-accent-500/20 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-md">
        <div className="bg-gray-900/50 backdrop-blur-xl border border-gray-800 rounded-2xl p-8 text-center">
          {status === 'loading' && (
            <>
              <Loader2 className="w-16 h-16 text-primary-500 animate-spin mx-auto mb-6" />
              <h1 className="text-2xl font-display font-bold text-white mb-2">
                Verifying Your Booking
              </h1>
              <p className="text-gray-400">Please wait...</p>
            </>
          )}

          {status === 'success' && (
            <>
              <div className="w-20 h-20 rounded-full bg-emerald-500/20 flex items-center justify-center mx-auto mb-6">
                <CheckCircle className="w-10 h-10 text-emerald-400" />
              </div>
              <h1 className="text-2xl font-display font-bold text-white mb-2">
                Booking Verified!
              </h1>
              <p className="text-gray-400 mb-6">{message}</p>
              <div className="text-sm text-gray-500">
                You can close this window now.
              </div>
            </>
          )}

          {status === 'error' && (
            <>
              <div className="w-20 h-20 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-6">
                <XCircle className="w-10 h-10 text-red-400" />
              </div>
              <h1 className="text-2xl font-display font-bold text-white mb-2">
                Verification Failed
              </h1>
              <p className="text-gray-400 mb-6">{message}</p>
              <p className="text-sm text-gray-500">
                Please try booking again or contact the service provider.
              </p>
            </>
          )}
        </div>

        {/* Logo */}
        <div className="text-center mt-8">
          <div className="inline-flex items-center gap-2 text-gray-500">
            <span className="text-sm">Powered by</span>
            <span className="font-display font-bold gradient-text">WorkSlot</span>
          </div>
        </div>
      </div>
    </div>
  )
}

