import { apiClient } from './axios';
import type { ChangePasswordRequest, ChangePasswordResponse, UserCreateRequest, UserResponse } from './types';

export async function createUser(payload: UserCreateRequest): Promise<UserResponse> {
  const { data } = await apiClient.post<UserResponse>('/users/', payload);
  return data;
}

export async function changePassword(payload: ChangePasswordRequest): Promise<ChangePasswordResponse> {
  const { data } = await apiClient.post<ChangePasswordResponse>('/users/change-password', payload);
  return data;
}
