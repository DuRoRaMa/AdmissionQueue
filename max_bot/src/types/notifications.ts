export type MaxNotificationType =
  | 'assigned'
  | 'called'
  | 'cancelled'
  | 'completed';

export interface MaxNotificationRequest {
  external_user_id: string;
  type: MaxNotificationType;
  talon: {
    id: number;
    name: string;
  };
  location?: string | null;
}
