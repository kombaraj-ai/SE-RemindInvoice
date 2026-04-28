export interface Client {
  id: number;
  user_id: number;
  name: string;
  email: string;
  phone: string | null;
  company_name: string | null;
  address_line1: string | null;
  address_line2: string | null;
  city: string | null;
  state: string | null;
  postal_code: string | null;
  country: string;
  payment_terms_days: number;
  currency: string;
  notes: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ClientCreate {
  name: string;
  email: string;
  phone?: string;
  company_name?: string;
  address_line1?: string;
  city?: string;
  country?: string;
  payment_terms_days?: number;
  currency?: string;
  notes?: string;
}

export type ClientUpdate = Partial<ClientCreate>;
