import axios from 'axios';

import i18n from '../i18n/i18n';

interface ApiErrorPayload {
  message?: unknown;
}

function translateApiMessage(message: string): string | null {
  const trimmedMessage = message.trim();

  const exactMessageKeys: Record<string, string> = {
    'Current password is incorrect': 'api_errors.current_password_incorrect',
    'Email already exists': 'api_errors.email_already_exists',
    'Invalid credentials': 'api_errors.invalid_credentials',
    'Invalid email format': 'api_errors.invalid_email_format',
    'Invalid notification type': 'api_errors.invalid_notification_type',
    'Invalid token': 'api_errors.invalid_token',
    'Invalid user ID in token': 'api_errors.invalid_token',
    'New password must be different from current password': 'api_errors.new_password_must_differ',
    'Not authorized to add family members': 'api_errors.not_authorized_family_members',
    'Not authorized to delete this event': 'api_errors.not_authorized_delete_event',
    'Not authorized to get this family events': 'api_errors.not_authorized_family_events',
    'Not authorized to update this event': 'api_errors.not_authorized_update_event',
    'Password cannot be empty': 'api_errors.password_empty',
    'Password cannot contain your email': 'api_errors.password_contains_email',
    'Password must be at least 10 characters': 'api_errors.password_min_length',
    'Password must include a lowercase letter': 'api_errors.password_lowercase',
    'Password must include an uppercase letter': 'api_errors.password_uppercase',
    'Password must include a number': 'api_errors.password_number',
    'Password must include a special character': 'api_errors.password_special',
    'Password too long': 'api_errors.password_too_long',
    'Password too long (max 72 bytes for hashing)': 'api_errors.password_too_long_hashing',
    'Permission denied': 'api_errors.permission_denied',
    'User is already a member of this family': 'api_errors.user_already_family_member',
    'User not in family': 'api_errors.user_not_in_family',
    Unauthorized: 'api_errors.unauthorized',
  };

  const exactKey = exactMessageKeys[trimmedMessage];
  if (exactKey) {
    return i18n.t(exactKey);
  }

  const notFoundMatch = trimmedMessage.match(/^(.+) with identifier '(.+)' not found$/);
  if (notFoundMatch) {
    return i18n.t('api_errors.resource_not_found', {
      resource: i18n.t(`api_errors.resources.${notFoundMatch[1].toLowerCase().replace(/_/g, ' ')}`, {
        defaultValue: notFoundMatch[1],
      }),
      identifier: notFoundMatch[2],
    });
  }

  if (trimmedMessage.startsWith('Failed to ')) {
    return i18n.t('api_errors.operation_failed');
  }

  return null;
}

export function getApiErrorMessage(error: unknown, fallbackMessage: string): string {
  if (axios.isAxiosError<ApiErrorPayload>(error)) {
    const apiMessage = error.response?.data?.message;
    if (typeof apiMessage === 'string' && apiMessage.trim().length > 0) {
      return translateApiMessage(apiMessage) ?? fallbackMessage;
    }
  }

  return fallbackMessage;
}
