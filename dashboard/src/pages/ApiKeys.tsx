import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiKeysApi, providerApi } from '../api/client'
import toast from 'react-hot-toast'
import {
  Key,
  Plus,
  Copy,
  Trash2,
  RefreshCw,
  Loader2,
  AlertTriangle,
  Check,
} from 'lucide-react'
import { format, parseISO } from 'date-fns'

export default function ApiKeys() {
  const queryClient = useQueryClient()
  const [newKeyName, setNewKeyName] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [createdKey, setCreatedKey] = useState<string | null>(null)
  const [copiedKey, setCopiedKey] = useState(false)

  const { data: apiKeys, isLoading } = useQuery({
    queryKey: ['api-keys'],
    queryFn: () => apiKeysApi.list().then((r) => r.data),
  })

  const { data: subscription } = useQuery({
    queryKey: ['subscription'],
    queryFn: () => providerApi.getSubscription().then((r) => r.data),
  })

  const createMutation = useMutation({
    mutationFn: (name: string) => apiKeysApi.create(name),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] })
      setCreatedKey(response.data.key)
      setNewKeyName('')
      toast.success('API key created!')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create API key')
    },
  })

  const revokeMutation = useMutation({
    mutationFn: (id: string) => apiKeysApi.revoke(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] })
      toast.success('API key revoked')
    },
    onError: () => toast.error('Failed to revoke API key'),
  })

  const regenerateMutation = useMutation({
    mutationFn: (id: string) => apiKeysApi.regenerate(id),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] })
      setCreatedKey(response.data.key)
      toast.success('API key regenerated!')
    },
    onError: () => toast.error('Failed to regenerate API key'),
  })

  const copyToClipboard = async (text: string) => {
    await navigator.clipboard.writeText(text)
    setCopiedKey(true)
    setTimeout(() => setCopiedKey(false), 2000)
    toast.success('Copied to clipboard!')
  }

  const canCreateKey = subscription?.can_use_api && 
    (apiKeys?.length || 0) < (subscription?.api_key_limit || 0)

  const embedCode = `<div id="workslot-calendar"></div>
<script src="${window.location.origin}/widget/workslot.js"></script>
<script>
  WorkSlot.init({
    apiKey: 'YOUR_API_KEY',
    container: '#workslot-calendar',
    theme: 'light'
  });
</script>`

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-display font-bold text-white">API Keys</h1>
          <p className="text-gray-400">Manage your widget API keys</p>
        </div>
        {canCreateKey && (
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Create API Key
          </button>
        )}
      </div>

      {/* Subscription warning */}
      {!subscription?.can_use_api && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-amber-400 font-medium">Upgrade Required</p>
            <p className="text-gray-400 text-sm">
              Your current plan doesn't include API access. Upgrade to create API keys and embed the calendar widget.
            </p>
          </div>
        </div>
      )}

      {/* API Keys List */}
      <div className="bg-gray-900/50 border border-gray-800 rounded-xl overflow-hidden">
        <div className="p-6 border-b border-gray-800 flex items-center justify-between">
          <h2 className="text-xl font-display font-semibold text-white flex items-center gap-2">
            <Key className="w-5 h-5 text-primary-400" />
            Your API Keys
          </h2>
          {subscription && (
            <span className="text-gray-400 text-sm">
              {apiKeys?.length || 0} / {subscription.api_key_limit} keys
            </span>
          )}
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
          </div>
        ) : apiKeys?.length > 0 ? (
          <div className="divide-y divide-gray-800">
            {apiKeys.map((key: any) => (
              <div key={key.id} className="p-6 flex flex-wrap items-center gap-4">
                <div className="flex-1 min-w-[200px]">
                  <p className="text-white font-medium">{key.name}</p>
                  <p className="text-gray-400 text-sm font-mono">{key.key_prefix}...</p>
                </div>
                <div className="text-sm text-gray-400">
                  {key.last_used_at ? (
                    <span>Last used: {format(parseISO(key.last_used_at), 'MMM d, yyyy')}</span>
                  ) : (
                    <span>Never used</span>
                  )}
                </div>
                <div className="text-sm text-gray-400">
                  Used: {key.usage_count} times
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => regenerateMutation.mutate(key.id)}
                    disabled={regenerateMutation.isPending}
                    className="p-2 text-primary-400 hover:bg-primary-500/20 rounded-lg transition-colors"
                    title="Regenerate"
                  >
                    <RefreshCw className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => revokeMutation.mutate(key.id)}
                    disabled={revokeMutation.isPending}
                    className="p-2 text-red-400 hover:bg-red-500/20 rounded-lg transition-colors"
                    title="Revoke"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-20">
            <Key className="w-12 h-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">No API keys yet</p>
            {canCreateKey && (
              <button
                onClick={() => setShowCreateModal(true)}
                className="mt-4 btn-primary"
              >
                Create Your First API Key
              </button>
            )}
          </div>
        )}
      </div>

      {/* Embed Instructions */}
      {apiKeys?.length > 0 && (
        <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
          <h2 className="text-xl font-display font-semibold text-white mb-4">
            Embed Code
          </h2>
          <p className="text-gray-400 text-sm mb-4">
            Add this code to your website to display the booking calendar:
          </p>
          <div className="relative">
            <pre className="bg-gray-800 rounded-lg p-4 overflow-x-auto text-sm text-gray-300">
              {embedCode}
            </pre>
            <button
              onClick={() => copyToClipboard(embedCode)}
              className="absolute top-2 right-2 p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
            >
              <Copy className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 w-full max-w-md">
            <h3 className="text-xl font-display font-semibold text-white mb-4">
              Create API Key
            </h3>
            <input
              type="text"
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              placeholder="Key name (e.g., Production Website)"
              className="input mb-4"
            />
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => {
                  setShowCreateModal(false)
                  setNewKeyName('')
                }}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={() => createMutation.mutate(newKeyName || 'Default API Key')}
                disabled={createMutation.isPending}
                className="btn-primary"
              >
                {createMutation.isPending ? 'Creating...' : 'Create Key'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Created Key Modal */}
      {createdKey && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 w-full max-w-lg">
            <div className="text-center mb-6">
              <div className="w-16 h-16 rounded-full bg-emerald-500/20 flex items-center justify-center mx-auto mb-4">
                <Check className="w-8 h-8 text-emerald-400" />
              </div>
              <h3 className="text-xl font-display font-semibold text-white">
                API Key Created!
              </h3>
              <p className="text-gray-400 text-sm mt-1">
                Make sure to copy your API key now. You won't be able to see it again!
              </p>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 flex items-center gap-3 mb-6">
              <code className="flex-1 text-sm text-emerald-400 font-mono break-all">
                {createdKey}
              </code>
              <button
                onClick={() => copyToClipboard(createdKey)}
                className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors flex-shrink-0"
              >
                {copiedKey ? (
                  <Check className="w-5 h-5 text-emerald-400" />
                ) : (
                  <Copy className="w-5 h-5" />
                )}
              </button>
            </div>
            <button
              onClick={() => setCreatedKey(null)}
              className="w-full btn-primary"
            >
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

