import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <section className="flex min-h-screen flex-col items-center justify-center gap-4 bg-slate-50 px-4 text-center">
      <h1 className="text-3xl font-semibold text-slate-900">Page not found</h1>
      <Link className="text-blue-600 hover:text-blue-700" to="/">
        Back to home
      </Link>
    </section>
  );
}
