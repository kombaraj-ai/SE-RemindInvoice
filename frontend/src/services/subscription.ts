import api from './api';

export interface PlanStatus {
  plan: string;
  monthly_invoice_count: number;
  monthly_invoice_limit: number;
  invoices_remaining: number;
  plan_expires_at: string | null;
}

export interface CheckoutResponse {
  payment_url: string;
  plan: string;
}

export const subscriptionService = {
  async getStatus(): Promise<PlanStatus> {
    const res = await api.get<PlanStatus>('/subscription/status');
    return res.data;
  },

  async createCheckout(plan: 'silver' | 'gold'): Promise<CheckoutResponse> {
    const res = await api.post<CheckoutResponse>('/subscription/checkout', { plan });
    return res.data;
  },
};
