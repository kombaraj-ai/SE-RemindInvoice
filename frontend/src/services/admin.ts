import api from './api';

export interface AdminUser {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_admin: boolean;
  is_verified: boolean;
  oauth_provider: string | null;
  created_at: string;
  invoice_count: number;
  client_count: number;
}

export interface AdminStats {
  total_users: number;
  active_users: number;
  total_invoices: number;
  total_revenue: number;
}

export const adminService = {
  async listUsers(params?: {
    search?: string;
    skip?: number;
    limit?: number;
  }): Promise<AdminUser[]> {
    const res = await api.get<AdminUser[]>('/admin/users', { params });
    return res.data;
  },

  async getUser(id: number): Promise<AdminUser> {
    const res = await api.get<AdminUser>(`/admin/users/${id}`);
    return res.data;
  },

  async setUserStatus(id: number, is_active: boolean): Promise<void> {
    await api.put(`/admin/users/${id}/status`, { is_active });
  },

  async getStats(): Promise<AdminStats> {
    const res = await api.get<AdminStats>('/admin/stats');
    return res.data;
  },
};
