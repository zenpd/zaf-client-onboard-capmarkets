import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { clientApi, StartPayload } from '../services/clientApi'
import { useClientStore, JourneyType } from '../store/clientStore'
import { Send, Loader2, UserPlus, Users, Building2, Landmark, CheckCircle2, ArrowRight, AlertTriangle, ExternalLink } from 'lucide-react'
import clsx from 'clsx'

const JOURNEYS: { type: JourneyType; label: string; desc: string; pill: string; gradient: string }[] = [
  { type: 'individual', label: 'Individual / HNW',     desc: 'Retail, High Net Worth & Ultra-HNW clients',   pill: 'journey-individual', gradient: 'from-blue-50 to-white border-blue-200' },
  { type: 'joint',      label: 'Joint Account',        desc: 'Two or more named account holders',            pill: 'journey-joint',       gradient: 'from-purple-50 to-white border-purple-200' },
  { type: 'corporate',  label: 'Corporate / UBO',      desc: 'Legal entities, beneficial owner verification', pill: 'journey-corporate',   gradient: 'from-orange-50 to-white border-orange-200' },
  { type: 'trust',      label: 'Trust / Foundation',   desc: 'Trusts, foundations & special purpose vehicles',pill: 'journey-trust',       gradient: 'from-teal-50 to-white border-teal-200' },
]

const STEPS = ['Journey Type', 'AI Onboarding', 'Review']

