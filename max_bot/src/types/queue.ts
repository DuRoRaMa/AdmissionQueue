export type TalonStatus =
  | 'Created'
  | 'Assigned'
  | 'Started'
  | 'Completed'
  | 'Cancelled'
  | 'Redirected';

export interface TalonListItem {
  id: number;
  name: string;
  status: TalonStatus;
  status_label: string;
  created_at: string;
  comment: string | null;
}

export interface TalonDetails extends TalonListItem {
  purpose: {
    id: number;
    name: string;
  };
}

export interface SubscribeResult {
  id: number;
  name: string;
  detail: string;
}
