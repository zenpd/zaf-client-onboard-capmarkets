import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { clientApi } from '../services/clientApi'
import { Loader2, CheckCircle2, AlertTriangle, ArrowLeft, FileText, ShieldCheck, User } from 'lucide-react'
import Badge from '../components/ui/Badge'

const LANE_COLORS: Record<string, 'green' | 'blue' | 'yellow' | 'red' | 'purple' | 'gray' | 'zen'> = {
  stp: 'green', standard: 'zen', enhanced: 'yellow', edd: 'purple', hold: 'red', reject: 'red',
}

const JOURNEY_PILL: Record<string, string> = {
  individual: 'journey-individual',
  joint: 'journey-joint',
  corporate: 'journey-corporate',
  trust: 'journey-trust',
}

