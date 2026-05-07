import { apiClient } from './axios';
import type {
  FamilyJoinRequestListResponse,
  FamilyJoinRequestResponse,
  FamilyMembershipResponse,
  FamilyResponse,
} from './types';

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

export async function requestFamilyJoin(familyId: number): Promise<FamilyJoinRequestResponse> {
  const { data } = await apiClient.post<FamilyJoinRequestResponse>(`/families/${familyId}/join-requests`);
  return data;
}

export async function listFamilyJoinRequests(familyId: number): Promise<FamilyJoinRequestListResponse> {
  const { data } = await apiClient.get<FamilyJoinRequestListResponse>(`/families/${familyId}/join-requests`);
  return data;
}

export async function approveFamilyJoinRequest(familyId: number, requestId: number): Promise<FamilyMembershipResponse> {
  const { data } = await apiClient.post<FamilyMembershipResponse>(
    `/families/${familyId}/join-requests/${requestId}/approve`,
  );
  return data;
}

export async function rejectFamilyJoinRequest(familyId: number, requestId: number): Promise<FamilyJoinRequestResponse> {
  const { data } = await apiClient.delete<FamilyJoinRequestResponse>(`/families/${familyId}/join-requests/${requestId}`);
  return data;
}
