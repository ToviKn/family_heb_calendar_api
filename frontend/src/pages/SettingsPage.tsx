import { useState } from 'react';
import type { FormEvent } from 'react';
import { useTranslation } from 'react-i18next';

import { ErrorMessage, LoadingMessage, SuccessMessage } from '../components/Feedback';
import { changePassword, getApiErrorMessage } from '../lib/api';

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

export function SettingsPage() {
  const { t } = useTranslation();

  const [form, setForm] = useState<ChangePasswordFormState>(initialFormState);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const passwordsMatch = form.newPassword === form.confirmNewPassword;
  const showPasswordMismatch = Boolean(form.confirmNewPassword) && !passwordsMatch;
  const isSubmitDisabled = isSubmitting || showPasswordMismatch;

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
      setError(t('settings.messages.password_mismatch'));
      setSuccess(null);
      return;
    }

    setError(null);
    setSuccess(null);
    setIsSubmitting(true);

    try {
      await changePassword({
        current_password: form.currentPassword,
        new_password: form.newPassword,
      });
      setForm(initialFormState);
      setSuccess(t('settings.messages.password_updated'));
    } catch (caughtError) {
      setError(
        getApiErrorMessage(caughtError, t('settings.messages.change_password_failed'))
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="space-y-6">
      <header className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">{t('settings.title')}</h1>
        <p className="mt-2 text-slate-600">{t('settings.description')}</p>
      </header>

      <article className="max-w-xl rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">{t('settings.change_password.title')}</h2>
        <p className="mt-2 text-sm text-slate-600">
          {t('settings.change_password.description')}
        </p>

        <form aria-busy={isSubmitting} className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <label className="block text-sm font-medium text-slate-700" htmlFor="current-password">
            {t('settings.fields.current_password')}
            <input
              id="current-password"
              autoComplete="current-password"
              disabled={isSubmitting}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-blue-500 disabled:bg-slate-100"
              type="password"
              value={form.currentPassword}
              onChange={(event) => updateField('currentPassword', event.target.value)}
              required
            />
          </label>

          <label className="block text-sm font-medium text-slate-700" htmlFor="new-password">
            {t('settings.fields.new_password')}
            <input
              id="new-password"
              autoComplete="new-password"
              aria-describedby="password-policy"
              disabled={isSubmitting}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-blue-500 disabled:bg-slate-100"
              type="password"
              value={form.newPassword}
              onChange={(event) => updateField('newPassword', event.target.value)}
              required
            />
          </label>

          <label className="block text-sm font-medium text-slate-700" htmlFor="confirm-new-password">
            {t('settings.fields.confirm_password')}
            <input
              id="confirm-new-password"
              autoComplete="new-password"
              aria-invalid={showPasswordMismatch}
              disabled={isSubmitting}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-blue-500 disabled:bg-slate-100"
              type="password"
              value={form.confirmNewPassword}
              onChange={(event) => updateField('confirmNewPassword', event.target.value)}
              required
            />
          </label>

          <p id="password-policy" className="text-sm text-slate-600">
            {t('settings.password_policy')}
          </p>

          {showPasswordMismatch ? (
            <p className="text-sm text-red-600">{t('settings.messages.password_mismatch')}</p>
          ) : null}

          {isSubmitting ? <LoadingMessage message={t('settings.messages.updating_password')} /> : null}
          {error ? <ErrorMessage message={error} /> : null}
          {success ? <SuccessMessage message={success} /> : null}

          <button
            className="rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
            type="submit"
            disabled={isSubmitDisabled}
          >
            {isSubmitting ? t('settings.messages.updating_password') : t('settings.actions.update')}
          </button>
        </form>
      </article>
    </section>
  );
}
