import { Settings } from 'lucide-react'

export default function SettingsPage() {
  return (
    <div className="p-8 max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Settings className="text-navy-500" />
          Platform Settings
        </h1>
        <p className="text-sm text-gray-500 mt-1">Configuration overview — edit via .env or Azure Key Vault</p>
      </div>

      <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200 space-y-4">
        {[
          ['API URL',                   import.meta.env.VITE_API_URL || 'http://localhost:8001/api/v1'],
          ['App Environment',           import.meta.env.VITE_APP_ENV || 'development'],
          ['OCR Confidence Threshold',  '85% (BRD FR-D2)'],
          ['LLM Confidence Threshold',  '75% (BRD FR-A3)'],
          ['Risk Scoring',              'Deterministic — no LLM (BRD FR-R3)'],
          ['Sanctions Engine',          'OFAC + UN + EU + HMT (BRD FR-R2)'],
          ['PII Tokenisation',          'Enabled (BRD FR-D5)'],
          ['Audit Retention',           '7 years (BRD FR-AU3)'],
          ['STP Mode',                  'All-or-nothing (BRD FR-R4)'],
          ['Human Review Rules',        'FR-H1 to FR-H4'],
        ].map(([key, val]) => (
          <div key={key} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
            <span className="text-sm font-medium text-gray-700">{key}</span>
            <code className="text-xs bg-slate-100 rounded px-2 py-1 text-gray-700 font-mono">{val}</code>
          </div>
        ))}
      </div>
    </div>
  )
}
