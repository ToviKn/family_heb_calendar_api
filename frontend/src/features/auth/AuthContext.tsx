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
  isAuthenticated: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getStoredToken());

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

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      isAuthenticated: Boolean(token),
      login,
      register,
      logout,
    }),
    [token, login, register, logout]
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
