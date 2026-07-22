import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';

import { login as loginRequest } from '../../lib/api/auth';
import { setApiAuthToken } from '../../lib/api/axios';
import { createUser, updateUserLanguage } from '../../lib/api/users';
import { clearStoredAuth, getStoredToken, getStoredUser, storeToken, storeUser } from '../../lib/auth/tokenStorage';
import i18n from '../../lib/i18n/i18n';

interface RegisterPayload {
  email: string;
  name: string;
  password: string;
}

interface LoginPayload {
  username: string;
  password: string;
}

type AuthUser = { id: number; email: string; name: string; language?: string };

interface AuthContextValue {
  token: string | null;
  userId: number | null;
  user: AuthUser | null;
  isAuthenticated: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  setLanguage: (language: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const initialStoredToken = getStoredToken();
const initialStoredUser = getStoredUser();
setApiAuthToken(initialStoredToken ?? undefined);

function decodeBase64Url(value: string): string {
  const normalized = value.replace(/-/g, '+').replace(/_/g, '/');
  const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=');
  return atob(padded);
}

function isTokenExpired(token: string | null): boolean {
  if (!token) {
    return true;
  }

  try {
    const [, payloadBase64] = token.split('.');
    if (!payloadBase64) {
      return true;
    }

    const payload = JSON.parse(decodeBase64Url(payloadBase64)) as { exp?: number };
    if (!payload.exp) {
      return true;
    }

    return Date.now() >= payload.exp * 1000;
  } catch {
    return true;
  }
}

function decodeUserIdFromToken(token: string | null): number | null {
  if (!token) {
    return null;
  }

  try {
    const [, payloadBase64] = token.split('.');
    if (!payloadBase64) {
      return null;
    }

    const payload = JSON.parse(decodeBase64Url(payloadBase64)) as { sub?: string | number };
    if (payload.sub === undefined || payload.sub === null) {
      return null;
    }

    const parsed = Number(payload.sub);
    return Number.isFinite(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const hasValidStoredToken = initialStoredToken && !isTokenExpired(initialStoredToken);
  const [token, setToken] = useState<string | null>(hasValidStoredToken ? initialStoredToken : null);
  const [user, setUser] = useState<AuthUser | null>(hasValidStoredToken ? initialStoredUser : null);

  useEffect(() => {
    if (user?.language && user.language !== i18n.language) {
      void i18n.changeLanguage(user.language);
    }
  }, [user?.language]);

  useEffect(() => {
    if (token) {
      setApiAuthToken(token);
      return;
    }

    setApiAuthToken(undefined);
  }, [token]);


  useEffect(() => {
    if (token && user) {
      storeToken(token);
      storeUser(user);
      return;
    }

    if (!token) {
      clearStoredAuth();
      return;
    }

    // Token exists but user is missing/corrupted in storage, clear inconsistent auth state.
    clearStoredAuth();
    setToken(null);
    setUser(null);
  }, [token, user]);
  const login = useCallback(async (payload: LoginPayload): Promise<void> => {
    const response = await loginRequest({ username: payload.username, password: payload.password });
    storeToken(response.access_token);
    storeUser(response.user);
    setApiAuthToken(response.access_token);
    setToken(response.access_token);
    setUser(response.user);
    if (response.user.language) {
      void i18n.changeLanguage(response.user.language);
    }
  }, []);

  const register = useCallback(async (payload: RegisterPayload): Promise<void> => {
    await createUser(payload);
  }, []);

  const logout = useCallback((): void => {
    clearStoredAuth();
    setApiAuthToken(undefined);
    setToken(null);
    setUser(null);
  }, []);

  const setLanguage = useCallback(async (language: string): Promise<void> => {
    await i18n.changeLanguage(language);

    if (!token || !user) {
      return;
    }

    const updatedUser = await updateUserLanguage(language);
    storeUser(updatedUser);
    setUser(updatedUser);
  }, [token, user]);

  const userId = useMemo(() => decodeUserIdFromToken(token), [token]);

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      userId,
      isAuthenticated: Boolean(token),
      user,
      login,
      register,
      setLanguage,
      logout,
    }),
    [token, userId, user, login, register, setLanguage, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider');
  }

  return context;
}
