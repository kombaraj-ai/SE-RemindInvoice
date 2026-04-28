'use client';
import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import api from '@/services/api';
import type { User } from '@/types/auth';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      const { data } = await api.get<User>('/auth/me');
      setUser(data);
    } catch {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    const AUTH_PAGES = ['/login', '/register', '/forgot-password', '/reset-password'];
    const onAuthPage = typeof window !== 'undefined' &&
      AUTH_PAGES.some(p => window.location.pathname.endsWith(p));
    if (onAuthPage) {
      setIsLoading(false);
      return;
    }
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (!token) {
      setIsLoading(false);
      return;
    }
    refreshUser().finally(() => setIsLoading(false));
  }, [refreshUser]);

  const login = useCallback(async (email: string, password: string) => {
    const params = new URLSearchParams();
    params.append('username', email);
    params.append('password', password);

    const { data } = await api.post<{ access_token: string; refresh_token: string }>(
      '/auth/login',
      params,
      { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
    );

    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);

    const { data: userData } = await api.get<User>('/auth/me');
    setUser(userData);
  }, []);

  const logout = useCallback(async () => {
    const refreshToken = typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null;
    // Revoke the refresh token server-side so it cannot be reused even if
    // it is still in the attacker's possession (e.g. via XSS or network log).
    if (refreshToken) {
      try {
        await api.post('/auth/logout', { refresh_token: refreshToken });
      } catch {
        // Best-effort — always clear local state even if the request fails.
      }
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
