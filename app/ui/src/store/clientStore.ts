import { create } from 'zustand'

export type JourneyType = 'individual' | 'joint' | 'corporate' | 'trust'
export type RoutingLane = 'stp' | 'standard' | 'enhanced' | 'edd' | 'hold' | 'reject'

export interface ChatMessage {
  role: 'user' | 'agent'
  content: string
  timestamp: string
}

export interface ClientSession {
  session_id: string
  journey_type: JourneyType
  current_step: string
  routing_lane?: RoutingLane
  client_type?: string
  human_review_required?: boolean
  account_number?: string
  response?: string
  completed_steps?: string[]
  messages?: ChatMessage[]
}

interface ClientStore {
  session: ClientSession | null
  loading: boolean
  error: string | null
  stats: Record<string, unknown> | null
  setSession: (s: ClientSession) => void
  clearSession: () => void
  setLoading: (v: boolean) => void
  setError: (e: string | null) => void
  setStats: (s: Record<string, unknown>) => void
}

export const useClientStore = create<ClientStore>((set) => ({
  session: null,
  loading: false,
  error: null,
  stats: null,
  setSession: (s) => set({ session: s }),
  clearSession: () => set({ session: null }),
  setLoading: (v) => set({ loading: v }),
  setError: (e) => set({ error: e }),
  setStats: (s) => set({ stats: s }),
}))
