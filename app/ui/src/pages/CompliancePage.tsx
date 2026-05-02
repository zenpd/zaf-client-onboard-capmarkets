import { useState, useEffect } from 'react'
import { clientApi, ReviewDecision } from '../services/clientApi'
import { ShieldCheck, Loader2, Check, X, AlertCircle, TrendingUp, Clock, Users, FileSearch } from 'lucide-react'
import clsx from 'clsx'

type QueueItem = { session_id: string; journey_type: string; risk_score?: number; routing_lane?: string; created_at?: string }

const DECISION_CONFIG = [
  { value: 'approve',      label: 'Approve',    icon: Check,        className: 'border-emerald-400 bg-emerald-50 text-emerald-700 hover:bg-emerald-100' },
  { value: 'reject',       label: 'Reject',     icon: X,            className: 'border-rose-400 bg-rose-50 text-rose-700 hover:bg-rose-100' },
  { value: 'rfi',          label: 'RFI',        icon: AlertCircle,  className: 'border-amber-400 bg-amber-50 text-amber-700 hover:bg-amber-100' },
  { value: 'escalate_edd', label: 'Escalate EDD', icon: TrendingUp, className: 'border-orange-400 bg-orange-50 text-orange-700 hover:bg-orange-100' },
] as const

