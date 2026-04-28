export type TriggerType = 'before_due' | 'on_due' | 'after_due';
export type ReminderStatus = 'sent' | 'failed';

export interface ReminderRule {
  id: number;
  user_id: number;
  name: string;
  trigger_type: TriggerType;
  days_offset: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ReminderLog {
  id: number;
  invoice_id: number;
  rule_id: number | null;
  sent_at: string;
  status: ReminderStatus;
  email_to: string;
  subject: string;
  error_message: string | null;
}
