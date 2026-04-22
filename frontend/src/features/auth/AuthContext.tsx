import { createContext, useContext, useEffect, useMemo, useState } from 'react';

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
  email: string;
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

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getStoredToken());

  useEffect(() => {
    if (token) {
      setApiAuthToken(token);
      return;
    }

    setApiAuthToken(undefined);
  }, [token]);

  async function login(payload: LoginPayload): Promise<void> {
    const response = await loginRequest({ username: payload.email, password: payload.password });
    storeToken(response.access_token);
    setToken(response.access_token);
  }

  async function register(payload: RegisterPayload): Promise<void> {
    await createUser(payload);
  }

  function logout(): void {
    clearStoredToken();
    setApiAuthToken(undefined);
    setToken(null);
  }

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      isAuthenticated: Boolean(token),
      login,
      register,
      logout,
    }),
    [token]
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
