import { FormEvent, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router-dom';

import { useAuth } from '../features/auth/AuthContext';

export function RegisterPage() {
  const { t } = useTranslation();

  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { register } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await register({ email, name, password });
      navigate('/login', { replace: true });
    } catch (err: any) {
      const message = err?.response?.data?.message;

      switch (message) {
        case 'Email already exists':
          setError(t('auth.errors.Email_exists'));
          break;

        case 'Invalid email format':
          setError(t('auth.errors.invalid_email'));
          break;

        case 'Password must be at least 10 characters':
          setError(t('auth.errors.least'));
          break;

        case 'Password must include a lowercase letter':
          setError(t('auth.errors.lowercase'));
          break;

        case 'Password must include an uppercase letter':
          setError(t('auth.errors.uppercase'));
          break;

        case 'Password must include a number':
          setError(t('auth.errors.number'));
          break;

        case 'Password must include a special character':
          setError(t('auth.errors.special'));
          break;

        default:
          setError(t('auth.errors.register_failed'));
      }
    }
     finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="mx-auto mt-16 w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <h1 className="text-2xl font-semibold text-slate-900">
        {t('auth.register')}</h1>
      <p className="mt-1 text-sm text-slate-600">
        {t('auth.register_description')}</p>

      <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
        <label className="block text-sm font-medium text-slate-700">
          {t('auth.name')}
          <input
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-blue-500"
            placeholder={t('auth.name_placeholder')}
            value={name}
            onChange={(event) => setName(event.target.value)}
            required
          />
        </label>

        <label className="block text-sm font-medium text-slate-700">
          {t('auth.email')}
          <input
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-blue-500"
            type="email"
            placeholder={t('auth.email_placeholder')}
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </label>

        <label className="block text-sm font-medium text-slate-700">
          {t('auth.password')}
          <input
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-blue-500"
            type="password"
            placeholder={t('auth.password_placeholder')}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>

        <ul className="mt-2 text-sm text-slate-600">
          <li>{password.length >= 10 ? '✓' : '•'} {t('auth.least')}</li>
          <li>{/[a-z]/.test(password) ? '✓' : '•'} {t('auth.lowercase')}</li>
          <li>{/[A-Z]/.test(password) ? '✓' : '•'} {t('auth.uppercase')}</li>
          <li>{/\d/.test(password) ? '✓' : '•'} {t('auth.number')}</li>
          <li>{/[^A-Za-z0-9]/.test(password) ? '✓' : '•'} {t('auth.special')}</li>
        </ul>

        <p id="password-policy" className="text-sm text-slate-600">
            {t('auth.password_policy')}
          </p>

        {error ? <p className="text-sm text-red-600">{error}</p> : null}

        <button
          className="w-full rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
          type="submit"
          disabled={isSubmitting}
        >
          {isSubmitting ? t('auth.creating_account') : t('auth.create_account')}
        </button>
      </form>

      <p className="mt-4 text-sm text-slate-600">
        {t('auth.already_have_account')}{' '}
        <Link className="text-blue-600 hover:text-blue-700" to="/login">
          {t('auth.sign_in')}
        </Link>
      </p>
    </section>
  );
}
