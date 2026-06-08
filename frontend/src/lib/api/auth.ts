import { apiClient } from './axios';
import type { AuthLoginRequest, AuthLoginResponse } from './types';

export async function login(payload: AuthLoginRequest): Promise<AuthLoginResponse> {
  const formBody = new URLSearchParams({
    username: payload.username,
    password: payload.password,
  });

  const { data } = await apiClient.post<AuthLoginResponse>('/auth/login', formBody, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
    },
  });

  return data;
}
