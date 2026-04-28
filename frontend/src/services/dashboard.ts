import api from './api';
import type { Invoice } from '@/types/invoice';

export interface DashboardStats {
  total_billed: number;
  total_paid: number;
  outstanding: number;
  overdue_count: number;
  total_clients: number;
}

export interface RevenueDataPoint {
  month: string;
  revenue: number;
}

export const dashboardService = {
  async getStats(): Promise<DashboardStats> {
    const res = await api.get<DashboardStats>('/dashboard/stats');
    return res.data;
  },

  async getRecentInvoices(): Promise<{ items: Invoice[] }> {
    const res = await api.get<{ items: Invoice[] }>('/dashboard/recent-invoices');
    return res.data;
  },

  async getRevenueChart(): Promise<{ data: RevenueDataPoint[] }> {
    const res = await api.get<{ data: RevenueDataPoint[] }>('/dashboard/revenue-chart');
    return res.data;
  },

  async getOverdue(): Promise<{ items: Invoice[]; total: number }> {
    const res = await api.get<{ items: Invoice[]; total: number }>('/dashboard/overdue');
    return res.data;
  },
};
