import { api } from './api'

export interface StartPayload {
  journey_type: 'individual' | 'joint' | 'corporate' | 'trust'
  message?: string
  form_data?: Record<string, string>
}

export interface ResumePayload {
  session_id: string
  message?: string
  form_data?: Record<string, string>
}

export interface ReviewDecision {
  session_id: string
  decision: 'approve' | 'reject' | 'rfi' | 'escalate_edd'
  rationale: string
  reviewer_id: string
  senior_approval_required?: boolean
}

export const clientApi = {
  startSession: (payload: StartPayload) => api.post('/onboard/start', payload),
  resumeSession: (payload: ResumePayload) => api.post('/onboard/resume', payload),
  getSession: (session_id: string) => api.get(`/onboard/session/${session_id}`),
  getDashboardStats: () => api.get('/applications/stats'),
  uploadDocument: (session_id: string, doc_type: string, file: File) => {
    const fd = new FormData()
    fd.append('session_id', session_id)
    fd.append('doc_type', doc_type)
    fd.append('file', file)
    return api.post('/documents/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  getDocuments: (session_id: string) => api.get(`/documents/session/${session_id}`),
  submitReviewDecision: (data: ReviewDecision) => api.post('/review/decide', data),
  getComplianceQueue: () => api.get('/review/queue'),
  listApplications: () => api.get('/applications/'),
}
