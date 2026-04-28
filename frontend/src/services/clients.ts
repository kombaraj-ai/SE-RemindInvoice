import api from './api';
import type { Client, ClientCreate, ClientUpdate } from '@/types/client';
import type { Invoice } from '@/types/invoice';

interface ClientListResponse {
  items: Client[];
  total: number;
}

interface ClientDetail extends Client {
  total_invoiced: number;
  total_paid: number;
  outstanding: number;
  invoice_count: number;
}

interface ClientInvoicesResponse {
  items: Invoice[];
  total: number;
}

export const clientsService = {
  async list(params?: {
    search?: string;
    active_only?: boolean;
    skip?: number;
    limit?: number;
  }): Promise<ClientListResponse> {
    const res = await api.get<ClientListResponse>('/clients', { params });
    return res.data;
  },

  async get(id: number): Promise<ClientDetail> {
    const res = await api.get<ClientDetail>(`/clients/${id}`);
    return res.data;
  },

  async create(data: ClientCreate): Promise<Client> {
    const res = await api.post<Client>('/clients', data);
    return res.data;
  },

  async update(id: number, data: ClientUpdate): Promise<Client> {
    const res = await api.put<Client>(`/clients/${id}`, data);
    return res.data;
  },

  async delete(id: number): Promise<void> {
    await api.delete(`/clients/${id}`);
  },

  async getInvoices(id: number): Promise<ClientInvoicesResponse> {
    const res = await api.get<ClientInvoicesResponse>(`/clients/${id}/invoices`);
    return res.data;
  },
};
