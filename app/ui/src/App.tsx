import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import AppShell from './components/layout/AppShell'
import DashboardPage from './pages/DashboardPage'
import OnboardPage from './pages/OnboardPage'
import CompliancePage from './pages/CompliancePage'
import ApplicationDetailPage from './pages/ApplicationDetailPage'
import AuditTrailPage from './pages/AuditTrailPage'
import AgentsPage from './pages/AgentsPage'
import SettingsPage from './pages/SettingsPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppShell />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard"                element={<DashboardPage />} />
          <Route path="onboard"                  element={<OnboardPage />} />
          <Route path="compliance"               element={<CompliancePage />} />
          <Route path="applications/:sessionId"  element={<ApplicationDetailPage />} />
          <Route path="audit"                    element={<AuditTrailPage />} />
          <Route path="agents"                   element={<AgentsPage />} />
          <Route path="settings"                 element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
