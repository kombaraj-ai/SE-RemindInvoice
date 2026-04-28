import api from './api';
import type { TokenResponse, User, RegisterRequest } from '@/types/auth';

export const authService = {
  async register(data: RegisterRequest): Promise<User> {
    const res = await api.post<User>('/auth/register', data);
    return res.data;
  },

  async login(email: string, password: string): Promise<TokenResponse> {
    const form = new URLSearchParams();
    form.append('username', email);
    form.append('password', password);
    const res = await api.post<TokenResponse>('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return res.data;
  },

  async getMe(): Promise<User> {
    const res = await api.get<User>('/auth/me');
    return res.data;
  },

  async updateProfile(data: { full_name?: string; email?: string; avatar_url?: string }): Promise<User> {
    const res = await api.put<User>('/auth/me', data);
    return res.data;
  },

  async forgotPassword(email: string): Promise<void> {
    await api.post('/auth/forgot-password', { email });
  },

  async resetPassword(token: string, new_password: string): Promise<void> {
    await api.post('/auth/reset-password', { token, new_password });
  },

  async logout(): Promise<void> {
    const refreshToken = typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null;
    if (refreshToken) {
      try {
        await api.post('/auth/logout', { refresh_token: refreshToken });
      } catch {
        // Best-effort — always clear local state regardless of server response.
      }
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },
};
