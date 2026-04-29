import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';

import { login as loginRequest } from '../../lib/api/auth';
import { setApiAuthToken } from '../../lib/api/axios';
import { createUser } from '../../lib/api/users';
import { clearStoredToken, getStoredToken, storeToken } from '../../lib/auth/tokenStorage';

interface RegisterPayload {
  email: string;
  name: string;
  password: string;
}

interface LoginPayload {
  username: string;
  password: string;
}

interface AuthContextValue {
  token: string | null;
  userId: number | null;
  isAuthenticated: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const initialStoredToken = getStoredToken();
setApiAuthToken(initialStoredToken ?? undefined);

function decodeBase64Url(value: string): string {
  const normalized = value.replace(/-/g, '+').replace(/_/g, '/');
  const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=');
  return atob(padded);
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
  const [token, setToken] = useState<string | null>(initialStoredToken);

  useEffect(() => {
    if (token) {
      setApiAuthToken(token);
      return;
    }

    setApiAuthToken(undefined);
  }, [token]);

  const login = useCallback(async (payload: LoginPayload): Promise<void> => {
    const response = await loginRequest({ username: payload.username, password: payload.password });
    storeToken(response.access_token);
    setApiAuthToken(response.access_token);
    setToken(response.access_token);
  }, []);

  const register = useCallback(async (payload: RegisterPayload): Promise<void> => {
    await createUser(payload);
  }, []);

  const logout = useCallback((): void => {
    clearStoredToken();
    setApiAuthToken(undefined);
    setToken(null);
  }, []);

  const userId = useMemo(() => decodeUserIdFromToken(token), [token]);

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      userId,
      isAuthenticated: Boolean(token),
      login,
      register,
      logout,
    }),
    [token, userId, login, register, logout]
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
