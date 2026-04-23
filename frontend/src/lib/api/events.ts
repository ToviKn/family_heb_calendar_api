import { apiClient } from './axios';
import type { ApiMessageResponse, EventCreate, EventListResponse, EventResponse, EventUpdate } from './types';

export interface EventsByDateParams {
  year: number;
  month: number;
  day: number;
}

export interface UpcomingEventsParams {
  days?: number;
  family_id?: number;
}

export interface FamilyEventsParams {
  page?: number;
  per_page?: number;
}

export async function createEvent(payload: EventCreate): Promise<EventResponse> {
  const { data } = await apiClient.post<EventResponse>('/events/', payload);
  return data;
}

export async function getEventsByDate(params: EventsByDateParams): Promise<EventListResponse> {
  const { data } = await apiClient.get<EventListResponse>('/events/', { params });
  return data;
}

export async function getTodayEvents(): Promise<EventListResponse> {
  const { data } = await apiClient.get<EventListResponse>('/events/today');
  return data;
}

export async function getUpcomingEvents(params: UpcomingEventsParams = {}): Promise<EventListResponse> {
  const { data } = await apiClient.get<EventListResponse>('/events/upcoming', { params });
  return data;
}

export async function getFamilyEvents(familyId: number, params: FamilyEventsParams = {}): Promise<EventListResponse> {
  const { data } = await apiClient.get<EventListResponse>(`/events/family/${familyId}`, { params });
  return data;
}

export async function getEventById(eventId: number): Promise<EventResponse> {
  const { data } = await apiClient.get<EventResponse>(`/events/${eventId}`);
  return data;
}

export async function updateEvent(eventId: number, payload: EventUpdate): Promise<EventResponse> {
  const { data } = await apiClient.put<EventResponse>(`/events/${eventId}`, payload);
  return data;
}

export async function deleteEvent(eventId: number): Promise<ApiMessageResponse> {
  const { data } = await apiClient.delete<ApiMessageResponse>(`/events/${eventId}`);
  return data;
}
