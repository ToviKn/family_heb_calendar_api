export type CalendarType = 'gregorian' | 'hebrew';

export type RepeatType = 'none' | 'daily' | 'yearly' | 'monthly' | 'weekly';

export type NotificationType = 'EVENT_REMINDER' | 'event reminder' | 'invite' | 'system';

export interface ApiMessageResponse {
  message: string;
}

export interface AuthLoginRequest {
  username: string;
  password: string;
}

export interface AuthLoginResponse extends Record<string, string> {
  access_token: string;
  token_type: string;
}

export interface EventCreate {
  title: string;
  month: number;
  day: number;
  family_id: number;
  start_time?: string | null;
  end_time?: string | null;
  description?: string | null;
  calendar_type?: CalendarType;
  year?: number | null;
  repeat_type?: RepeatType;
}

export interface EventUpdate {
  start_time?: string | null;
  end_time?: string | null;
  title?: string | null;
  description?: string | null;
  year?: number | null;
  month?: number | null;
  day?: number | null;
  repeat_type?: RepeatType | null;
}

export interface EventResponse {
  id: number;
  created_by: number;
  created_at: string;
  updated_at: string;
  title: string;
  month: number;
  day: number;
  family_id: number;
  start_time?: string | null;
  end_time?: string | null;
  description?: string | null;
  calendar_type?: CalendarType | null;
  year?: number | null;
  repeat_type?: RepeatType | null;
  next_occurrence?: string | null;
}

export interface EventListResponse {
  events: EventResponse[];
  total: number;
  page?: number | null;
  per_page?: number | null;
}

export interface FamilyResponse {
  id: number;
  name: string;
  created_at: string;
}

export interface FamilyMembershipResponse {
  id: number;
  user_id: number;
  family_id: number;
  role: string;
  joined_at: string;
}

export interface NotificationCreate {
  event_id: number;
}

export interface NotificationResponse {
  id: number;
  user_id: number;
  message: string;
  type: NotificationType;
  event_id?: number | null;
  created_at: string;
  is_read: boolean;
}

export interface NotificationListResponse {
  events: NotificationResponse[];
  total: number;
}

export interface UserCreateRequest {
  email: string;
  name: string;
  password: string;
}

export interface UserResponse {
  id: number;
  email: string;
  name: string;
}
