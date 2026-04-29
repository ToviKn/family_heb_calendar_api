interface MessageProps {
  message: string;
}

export function ErrorMessage({ message }: MessageProps) {
  return <p className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{message}</p>;
}

export function SuccessMessage({ message }: MessageProps) {
  return <p className="mt-3 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">{message}</p>;
}

export function LoadingMessage({ message }: MessageProps) {
  return <p className="mt-3 text-sm text-slate-600">{message}</p>;
}

export function EmptyMessage({ message }: MessageProps) {
  return <p className="mt-3 text-sm text-slate-600">{message}</p>;
}
