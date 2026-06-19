export interface MaxHelper {
  id: number
  username: string
  full_name: string
  sector: string
  is_active: boolean
  active_requests_count: number
}

export interface MaxHelpRequest {
  id: number
  from: string
  theme: string
  priority: string
  text: string
  created_at: string
}

export interface MaxHelperLinkResult {
  detail?: string
  helper?: MaxHelper
}