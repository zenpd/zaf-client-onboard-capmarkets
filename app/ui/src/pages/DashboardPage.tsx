import { useEffect } from 'react'
import StatsCard from '../components/ui/StatsCard'
import Badge from '../components/ui/Badge'
import { useClientStore } from '../store/clientStore'
import { clientApi } from '../services/clientApi'
import { TrendingUp, ShieldAlert, CheckCircle2, Users, AlertTriangle, BarChart3, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'

const ROUTING_COLORS: Record<string, string> = {
  stp: 'bg-emerald-500',
  standard: 'bg-zen-500',
  enhanced: 'bg-amber-500',
  edd: 'bg-orange-500',
  hold: 'bg-rose-400',
  reject: 'bg-rose-700',
}

const PHASES = [
  'Pre-Screening & Triage',
  'Document Collection & OCR',
  'KYC / AML Screening',
  'FATCA / CRS',
  'Source of Wealth',
  'Risk Scoring',
  'AI Decisioning',
  'Human-in-the-Loop',
  'Account Creation',
  'Post-Onboarding',
]

