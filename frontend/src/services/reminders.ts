import api from './api';
import type { ReminderRule, ReminderLog } from '@/types/reminder';

export const remindersService = {
  async listRules(): Promise<ReminderRule[]> {
    const res = await api.get<ReminderRule[]>('/reminders/rules');
    return res.data;
  },

  async createRule(data: {
    name: string;
    trigger_type: string;
    days_offset: number;
  }): Promise<ReminderRule> {
    const res = await api.post<ReminderRule>('/reminders/rules', data);
    return res.data;
  },

  async updateRule(id: number, data: Partial<ReminderRule>): Promise<ReminderRule> {
    const res = await api.put<ReminderRule>(`/reminders/rules/${id}`, data);
    return res.data;
  },

  async deleteRule(id: number): Promise<void> {
    await api.delete(`/reminders/rules/${id}`);
  },

  async sendManual(invoiceId: number): Promise<{ sent: boolean }> {
    const res = await api.post<{ sent: boolean }>(`/reminders/send/${invoiceId}`);
    return res.data;
  },

  async getLogs(invoiceId?: number): Promise<ReminderLog[]> {
    const url = invoiceId ? `/reminders/logs/${invoiceId}` : '/reminders/logs';
    const res = await api.get<ReminderLog[]>(url);
    return res.data;
  },
};
