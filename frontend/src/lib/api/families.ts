import { apiClient } from './axios';
import type { FamilyMembershipResponse, FamilyResponse } from './types';

export async function createFamily(name: string): Promise<FamilyResponse> {
  const { data } = await apiClient.post<FamilyResponse>('/families/', null, {
    params: { name },
  });
  return data;
}

export async function addFamilyMember(familyId: number, userId: number): Promise<FamilyMembershipResponse> {
  const { data } = await apiClient.post<FamilyMembershipResponse>(`/families/${familyId}/members`, null, {
    params: { user_id: userId },
  });
  return data;
}
