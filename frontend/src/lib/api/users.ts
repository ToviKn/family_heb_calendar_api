import { apiClient } from './axios';
import type { UserCreateRequest, UserResponse } from './types';

export async function createUser(payload: UserCreateRequest): Promise<UserResponse> {
  const { data } = await apiClient.post<UserResponse>('/users/', payload);
  return data;
}
