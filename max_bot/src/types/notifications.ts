export type MaxNotificationType =
  | 'assigned'
  | 'called'
  | 'cancelled'
  | 'completed'
  | 'helper_request'

export interface MaxTalonNotification {
  external_user_id: string
  type: 'assigned' | 'called' | 'cancelled' | 'completed'
  talon: {
    id: number
    name: string
  }
  location?: string | null
}

export interface MaxHelperRequestNotification {
  external_user_id: string
  type: 'helper_request'
  helper_request: {
    id: number
    from: string
    theme: string
    priority: string
    text: string
    created_at: string
  }
}

export type MaxNotificationRequest =
  | MaxTalonNotification
  | MaxHelperRequestNotification