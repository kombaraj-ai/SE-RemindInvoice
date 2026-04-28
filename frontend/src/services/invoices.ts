import api from './api';
import type { Invoice, InvoiceCreate } from '@/types/invoice';

interface InvoiceListResponse {
  items: Invoice[];
  total: number;
}

export const invoicesService = {
  async list(params?: {
    status?: string;
    client_id?: number;
    skip?: number;
    limit?: number;
  }): Promise<InvoiceListResponse> {
    const res = await api.get<InvoiceListResponse>('/invoices', { params });
    return res.data;
  },

  async get(id: number): Promise<Invoice> {
    const res = await api.get<Invoice>(`/invoices/${id}`);
    return res.data;
  },

  async getPublic(token: string): Promise<Invoice> {
    const res = await api.get<Invoice>(`/invoices/public/${token}`);
    return res.data;
  },

  async create(data: InvoiceCreate): Promise<Invoice> {
    const res = await api.post<Invoice>('/invoices', data);
    return res.data;
  },

  async update(id: number, data: Partial<InvoiceCreate>): Promise<Invoice> {
    const res = await api.put<Invoice>(`/invoices/${id}`, data);
    return res.data;
  },

  async delete(id: number): Promise<void> {
    await api.delete(`/invoices/${id}`);
  },

  async send(id: number): Promise<Invoice> {
    const res = await api.post<Invoice>(`/invoices/${id}/send`);
    return res.data;
  },

  async markPaid(id: number): Promise<Invoice> {
    const res = await api.post<Invoice>(`/invoices/${id}/mark-paid`);
    return res.data;
  },

  async duplicate(id: number): Promise<Invoice> {
    const res = await api.post<Invoice>(`/invoices/${id}/duplicate`);
    return res.data;
  },
};
