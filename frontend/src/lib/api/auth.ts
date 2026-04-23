import { apiClient } from './axios';
import type { AuthLoginRequest, AuthLoginResponse } from './types';

export async function login(payload: AuthLoginRequest): Promise<AuthLoginResponse> {
  const params = new URLSearchParams();
  params.set('username', payload.username);
  params.set('password', payload.password);

  if (payload.grant_type) params.set('grant_type', payload.grant_type);
  if (payload.scope) params.set('scope', payload.scope);
  if (payload.client_id) params.set('client_id', payload.client_id);
  if (payload.client_secret) params.set('client_secret', payload.client_secret);

  const { data } = await apiClient.post<AuthLoginResponse>('/auth/login', params, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });

  return data;
}
