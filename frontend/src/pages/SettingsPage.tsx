import axios from 'axios';
import { FormEvent, useState } from 'react';

import { ErrorMessage, SuccessMessage } from '../components/Feedback';
import { changePassword } from '../lib/api';

interface ChangePasswordFormState {
  currentPassword: string;
  newPassword: string;
  confirmNewPassword: string;
}

const initialFormState: ChangePasswordFormState = {
  currentPassword: '',
  newPassword: '',
  confirmNewPassword: '',
};

function getChangePasswordErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const apiMessage = error.response?.data?.message;
    if (typeof apiMessage === 'string' && apiMessage.trim().length > 0) {
      return apiMessage;
    }
  }

  return 'Unable to change password. Please verify your current password and try again.';
}

export function SettingsPage() {
  const [form, setForm] = useState<ChangePasswordFormState>(initialFormState);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const passwordsMatch = form.newPassword === form.confirmNewPassword;

  function updateField(field: keyof ChangePasswordFormState, value: string): void {
    setForm((previous) => ({ ...previous, [field]: value }));
    if (error) {
      setError(null);
    }
    if (success) {
      setSuccess(null);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!passwordsMatch) {
      setError('New password and confirmation do not match.');
      setSuccess(null);
      return;
    }

    setError(null);
    setSuccess(null);
    setIsSubmitting(true);

    try {
      const response = await changePassword({
        current_password: form.currentPassword,
        new_password: form.newPassword,
      });
      setForm(initialFormState);
      setSuccess(response.message || 'Password updated successfully.');
    } catch (caughtError) {
      setError(getChangePasswordErrorMessage(caughtError));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="space-y-6">
      <header className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Settings</h1>
        <p className="mt-2 text-slate-600">Manage your account security settings.</p>
      </header>

      <article className="max-w-xl rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Change password</h2>
        <p className="mt-2 text-sm text-slate-600">
          Enter your current password and choose a new password for your account.
        </p>

        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <label className="block text-sm font-medium text-slate-700">
            Current password
            <input
              autoComplete="current-password"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-blue-500"
              type="password"
              value={form.currentPassword}
              onChange={(event) => updateField('currentPassword', event.target.value)}
              required
            />
          </label>

          <label className="block text-sm font-medium text-slate-700">
            New password
            <input
              autoComplete="new-password"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-blue-500"
              type="password"
              value={form.newPassword}
              onChange={(event) => updateField('newPassword', event.target.value)}
              required
            />
          </label>

          <label className="block text-sm font-medium text-slate-700">
            Confirm new password
            <input
              autoComplete="new-password"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-blue-500"
              type="password"
              value={form.confirmNewPassword}
              onChange={(event) => updateField('confirmNewPassword', event.target.value)}
              required
            />
          </label>

          {!passwordsMatch && form.confirmNewPassword ? (
            <p className="text-sm text-red-600">New password and confirmation must match.</p>
          ) : null}

          {error ? <ErrorMessage message={error} /> : null}
          {success ? <SuccessMessage message={success} /> : null}

          <button
            className="rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Updating password...' : 'Update password'}
          </button>
        </form>
      </article>
    </section>
  );
}
