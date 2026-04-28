export type InvoiceStatus = 'draft' | 'sent' | 'viewed' | 'paid' | 'overdue' | 'cancelled';

export interface InvoiceItem {
  id?: number;
  description: string;
  quantity: number;
  unit_price: number;
  amount: number;
  sort_order: number;
}

export interface Invoice {
  id: number;
  user_id: number;
  client_id: number;
  invoice_number: string;
  status: InvoiceStatus;
  issue_date: string;
  due_date: string;
  subtotal: number;
  tax_rate: number;
  tax_amount: number;
  discount_amount: number;
  total: number;
  currency: string;
  notes: string | null;
  pdf_url: string | null;
  public_token: string;
  sent_at: string | null;
  paid_at: string | null;
  created_at: string;
  updated_at: string;
  client?: import('./client').Client;
  items?: InvoiceItem[];
}

export interface InvoiceCreate {
  client_id: number;
  issue_date: string;
  due_date: string;
  tax_rate?: number;
  discount_amount?: number;
  currency?: string;
  notes?: string;
  items: Omit<InvoiceItem, 'id' | 'amount'>[];
}
