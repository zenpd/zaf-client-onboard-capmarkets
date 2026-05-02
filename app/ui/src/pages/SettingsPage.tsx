import { Settings, Shield, Database, Activity, Key } from 'lucide-react'

const SETTINGS_SECTIONS = [
  {
    title: 'Platform',
    icon: Activity,
    iconBg: 'bg-zen-100 text-zen-600',
    items: [
      ['API URL',          import.meta.env.VITE_API_URL || 'http://localhost:8001/api/v1'],
      ['App Environment',  import.meta.env.VITE_APP_ENV || 'development'],
      ['Platform',         'Capital Markets Client Onboarding'],
    ],
  },
  {
    title: 'BRD Compliance',
    icon: Shield,
    iconBg: 'bg-rose-50 text-rose-600',
    items: [
      ['OCR Confidence Threshold', '85% (BRD FR-D2)'],
      ['LLM Confidence Threshold', '75% (BRD FR-A3)'],
      ['Risk Scoring',             'Deterministic — no LLM (BRD FR-R3)'],
      ['STP Mode',                 'All-or-nothing (BRD FR-R4)'],
      ['Human Review Rules',       'FR-H1 to FR-H4'],
    ],
  },
  {
    title: 'Regulatory',
    icon: Key,
    iconBg: 'bg-amber-50 text-amber-600',
    items: [
      ['Sanctions Engine',   'OFAC + UN + EU + HMT (BRD FR-R2)'],
      ['PII Tokenisation',   'Enabled (BRD FR-D5)'],
      ['Audit Retention',    '7 years (BRD FR-AU3)'],
      ['FATCA/CRS',          'Enabled (BRD FR-R5)'],
    ],
  },
  {
    title: 'Infrastructure',
    icon: Database,
    iconBg: 'bg-emerald-50 text-emerald-600',
    items: [
      ['Orchestration',  'Temporal.io workflow engine'],
      ['AI Framework',   'LangGraph supervisor-loop'],
      ['Tracing',        'Arize Phoenix'],
      ['Deployment',     'Azure Container Apps'],
    ],
  },
]

export default function SettingsPage() {
  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <Settings size={20} className="text-zen-600" />
            Platform Settings
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">Configuration overview — edit via .env or Azure Key Vault</p>
        </div>
      </div>

      <div className="space-y-4">
        {SETTINGS_SECTIONS.map(section => {
          const Icon = section.icon
          return (
            <div key={section.title} className="card p-5">
              <div className="flex items-center gap-2.5 mb-4">
                <div className={`w-8 h-8 rounded-xl flex items-center justify-center ${section.iconBg}`}>
                  <Icon size={15} />
                </div>
                <h2 className="text-sm font-semibold text-gray-800">{section.title}</h2>
              </div>
              <div className="space-y-0">
                {section.items.map(([key, val]) => (
                  <div key={key} className="flex items-center justify-between py-2.5 border-b border-gray-50 last:border-0">
                    <span className="text-xs font-medium text-gray-600">{key}</span>
                    <code className="text-xs bg-gray-100 rounded-lg px-2.5 py-1 text-gray-700 font-mono max-w-xs truncate">
                      {val}
                    </code>
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
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
