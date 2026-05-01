import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { clientApi, StartPayload } from '../services/clientApi'
import { useClientStore, JourneyType } from '../store/clientStore'
import { Send, Loader2, UserPlus, Users, Building2, Landmark } from 'lucide-react'
import clsx from 'clsx'

const JOURNEYS: { type: JourneyType; label: string; desc: string; icon: React.ElementType }[] = [
  { type: 'individual', label: 'Individual',  desc: 'Retail, HNW, UHNW clients',        icon: UserPlus },
  { type: 'joint',      label: 'Joint',       desc: 'Two or more named account holders', icon: Users },
  { type: 'corporate',  label: 'Corporate',   desc: 'Legal entities, UBO verification', icon: Building2 },
  { type: 'trust',      label: 'Trust',       desc: 'Trusts, foundations, special vehicles', icon: Landmark },
]

const STEPS = ['Journey Type', 'Client Info', 'Documents', 'Review']

export default function OnboardPage() {
  const [step, setStep] = useState(0)
  const [journeyType, setJourneyType] = useState<JourneyType>('individual')
  const [formData, setFormData] = useState<Record<string, string>>({})
  const [message, setMessage] = useState('')
  const [chatMessages, setChatMessages] = useState<{role: string; content: string}[]>([])
  const { session, setSession, loading, setLoading, setError } = useClientStore()
  const nav = useNavigate()

  const handleStart = async () => {
    setLoading(true)
    setError(null)
    try {
      const payload: StartPayload = { journey_type: journeyType, form_data: formData, message: message || undefined }
      const { data } = await clientApi.startSession(payload)
      setSession(data)
      setChatMessages([{ role: 'agent', content: data.response || 'Session started.' }])
      setStep(1)
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      setError(err.response?.data?.detail || 'Failed to start session.')
    } finally {
      setLoading(false)
    }
  }

  const handleResume = async () => {
    if (!session) return
    setLoading(true)
    const userMsg = message
    setMessage('')
    setChatMessages(prev => [...prev, { role: 'user', content: userMsg }])
    try {
      const { data } = await clientApi.resumeSession({ session_id: session.session_id, message: userMsg, form_data: formData })
      setSession(data)
      setChatMessages(prev => [...prev, { role: 'agent', content: data.response || '...' }])
    } catch (e) {
      setChatMessages(prev => [...prev, { role: 'agent', content: 'Error resuming session.' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">New Client Onboarding</h1>
        <p className="text-sm text-gray-500 mt-1">25-step AI-augmented onboarding workflow — BRD UC-01</p>
      </div>

      {/* Progress */}
      <div className="flex items-center gap-0">
        {STEPS.map((s, i) => (
          <div key={s} className="flex items-center flex-1">
            <div className="flex flex-col items-center">
              <div className={clsx(
                'w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold border-2 transition-all',
                i < step ? 'bg-navy-500 border-navy-500 text-white' :
                i === step ? 'bg-gold-500 border-gold-500 text-white' :
                'bg-white border-gray-300 text-gray-400'
              )}>{i + 1}</div>
              <p className={clsx('text-xs mt-1 whitespace-nowrap', i === step ? 'text-navy-500 font-semibold' : 'text-gray-400')}>{s}</p>
            </div>
            {i < STEPS.length - 1 && (
              <div className={clsx('flex-1 h-0.5 mb-5 mx-1', i < step ? 'bg-navy-500' : 'bg-gray-200')} />
            )}
          </div>
        ))}
      </div>

      {/* Step 0: Journey Type */}
      {step === 0 && (
        <div className="space-y-4">
          <h2 className="font-semibold text-gray-800">Select Journey Type</h2>
          <div className="grid grid-cols-2 gap-4">
            {JOURNEYS.map(({ type, label, desc, icon: Icon }) => (
              <button
                key={type}
                onClick={() => setJourneyType(type)}
                className={clsx(
                  'p-5 rounded-xl border-2 text-left transition-all hover:shadow-md',
                  journeyType === type ? 'border-navy-500 bg-navy-50' : 'border-gray-200 bg-white'
                )}
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className={clsx(
                    'w-10 h-10 rounded-lg flex items-center justify-center',
                    journeyType === type ? 'bg-navy-500 text-white' : 'bg-gray-100 text-gray-500'
                  )}>
                    <Icon size={20} />
                  </div>
                  <span className="font-semibold text-gray-800">{label}</span>
                </div>
                <p className="text-xs text-gray-500">{desc}</p>
              </button>
            ))}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Initial message (optional)</label>
            <textarea
              rows={3}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="e.g. I'd like to open a joint HNW investment account..."
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-navy-500"
            />
          </div>
          <button
            onClick={handleStart}
            disabled={loading}
            className="flex items-center gap-2 bg-navy-500 hover:bg-navy-700 text-white px-6 py-3 rounded-lg font-semibold text-sm transition-all disabled:opacity-60"
          >
            {loading ? <Loader2 size={18} className="animate-spin" /> : <UserPlus size={18} />}
            Start Onboarding
          </button>
        </div>
      )}

      {/* Step 1+: Chat interface */}
      {step >= 1 && session && (
        <div className="grid grid-cols-3 gap-6">
          {/* Chat */}
          <div className="col-span-2 bg-white rounded-xl shadow-sm border border-gray-200 flex flex-col h-[500px]">
            <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <span className="text-sm font-semibold text-gray-800">AI Onboarding Assistant</span>
              <span className="text-xs text-gray-400">Session: {session.session_id.slice(0, 8)}…</span>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {chatMessages.map((m, i) => (
                <div key={i} className={clsx('flex', m.role === 'user' ? 'justify-end' : 'justify-start')}>
                  <div className={clsx(
                    'max-w-xs rounded-xl px-4 py-2 text-sm',
                    m.role === 'user' ? 'bg-navy-500 text-white' : 'bg-slate-100 text-gray-800'
                  )}>
                    {m.content}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-slate-100 rounded-xl px-4 py-2">
                    <Loader2 size={16} className="animate-spin text-navy-500" />
                  </div>
                </div>
              )}
            </div>
            <div className="p-3 border-t border-gray-100 flex gap-2">
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !loading && handleResume()}
                placeholder="Type your response…"
                className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-navy-500"
              />
              <button
                onClick={handleResume}
                disabled={loading || !message.trim()}
                className="bg-navy-500 hover:bg-navy-700 text-white rounded-lg px-3 py-2 transition-all disabled:opacity-60"
              >
                <Send size={16} />
              </button>
            </div>
          </div>

          {/* Status Panel */}
          <div className="space-y-4">
            <div className="bg-white rounded-xl shadow-sm p-4 border border-gray-200 space-y-3">
              <h3 className="font-semibold text-sm text-gray-800">Application Status</h3>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-500">Journey</span>
                  <span className="font-medium capitalize">{session.journey_type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Current Step</span>
                  <span className="font-medium">{session.current_step || '—'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Routing Lane</span>
                  <span className="font-medium capitalize">{session.routing_lane || 'pending'}</span>
                </div>
                {session.account_number && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Account No.</span>
                    <span className="font-semibold text-green-700">{session.account_number}</span>
                  </div>
                )}
                {session.human_review_required && (
                  <p className="text-yellow-700 bg-yellow-50 rounded px-2 py-1 border border-yellow-200">
                    Awaiting compliance review
                  </p>
                )}
              </div>
            </div>

            {/* Completed Steps */}
            {session.completed_steps && session.completed_steps.length > 0 && (
              <div className="bg-white rounded-xl shadow-sm p-4 border border-gray-200">
                <h3 className="font-semibold text-sm text-gray-800 mb-2">Completed Steps</h3>
                <div className="space-y-1">
                  {session.completed_steps.map((s) => (
                    <div key={s} className="text-xs text-green-700 flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-green-500 flex-shrink-0" />
                      <span className="capitalize">{s.replace(/_/g, ' ')}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
