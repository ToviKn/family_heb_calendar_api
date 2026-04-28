import { FormEvent, useState } from 'react';

import { useAuth } from '../features/auth/AuthContext';
import {
  addFamilyMember,
  createFamily,
  getFamilyEvents,
  type EventResponse,
  type FamilyMembershipResponse,
  type FamilyResponse,
} from '../lib/api';

interface CreateFamilyForm {
  name: string;
}

interface JoinFamilyForm {
  familyId: string;
}

interface FamilyEventsForm {
  familyId: string;
  page: string;
  perPage: string;
}

export function FamiliesPage() {
  const { userId } = useAuth();

  const [createForm, setCreateForm] = useState<CreateFamilyForm>({ name: '' });
  const [createdFamily, setCreatedFamily] = useState<FamilyResponse | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);
  const [isCreatingFamily, setIsCreatingFamily] = useState(false);

  const [joinForm, setJoinForm] = useState<JoinFamilyForm>({ familyId: '' });
  const [joinResult, setJoinResult] = useState<FamilyMembershipResponse | null>(null);
  const [joinError, setJoinError] = useState<string | null>(null);
  const [isJoining, setIsJoining] = useState(false);

  const [eventsForm, setEventsForm] = useState<FamilyEventsForm>({ familyId: '', page: '1', perPage: '20' });
  const [familyEvents, setFamilyEvents] = useState<EventResponse[]>([]);
  const [eventsTotal, setEventsTotal] = useState(0);
  const [eventsError, setEventsError] = useState<string | null>(null);
  const [isLoadingEvents, setIsLoadingEvents] = useState(false);

  async function handleCreateFamily(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedName = createForm.name.trim();
    if (!trimmedName) {
      setCreateError('Family name is required.');
      setCreatedFamily(null);
      return;
    }

    setCreateError(null);
    setCreatedFamily(null);
    setIsCreatingFamily(true);

    try {
      const family = await createFamily(trimmedName);
      setCreatedFamily(family);
      setCreateForm({ name: '' });
      setJoinForm((prev) => ({ ...prev, familyId: String(family.id) }));
      setEventsForm((prev) => ({ ...prev, familyId: String(family.id) }));
    } catch {
      setCreateError('Unable to create family. Please try a different name.');
    } finally {
      setIsCreatingFamily(false);
    }
  }

  async function handleJoinFamily(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setJoinError(null);
    setJoinResult(null);

    if (!userId) {
      setJoinError('Unable to resolve your user ID from token. Please login again.');
      return;
    }

    setIsJoining(true);

    try {
      const result = await addFamilyMember(Number(joinForm.familyId), userId);
      setJoinResult(result);
    } catch {
      setJoinError('Unable to join family. Verify family ID and your permissions.');
    } finally {
      setIsJoining(false);
    }
  }

  async function handleLoadFamilyEvents(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setEventsError(null);
    setIsLoadingEvents(true);

    try {
      const result = await getFamilyEvents(Number(eventsForm.familyId), {
        page: Number(eventsForm.page),
        per_page: Number(eventsForm.perPage),
      });

      setFamilyEvents(result.events);
      setEventsTotal(result.total);
    } catch {
      setEventsError('Unable to load family events. Verify family ID and permissions.');
    } finally {
      setIsLoadingEvents(false);
    }
  }

  return (
    <section className="space-y-6">
      <header className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Families</h1>
        <p className="mt-2 text-slate-600">Create or join a family, then view family events.</p>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Create family</h2>

          <form className="mt-4 space-y-3" onSubmit={handleCreateFamily}>
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2"
              type="text"
              minLength={1}
              maxLength={120}
              placeholder="Family name"
              value={createForm.name}
              onChange={(event) => {
                setCreateForm({ name: event.target.value });
                if (createError) {
                  setCreateError(null);
                }
                if (createdFamily) {
                  setCreatedFamily(null);
                }
              }}
              required
            />

            <button
              className="rounded-md bg-emerald-600 px-4 py-2 text-white hover:bg-emerald-700 disabled:bg-emerald-300"
              type="submit"
              disabled={isCreatingFamily}
            >
              {isCreatingFamily ? 'Creating...' : 'Create family'}
            </button>
          </form>

          {createError ? <p className="mt-3 text-sm text-red-600">{createError}</p> : null}

          {createdFamily ? (
            <div className="mt-3 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">
              Family "{createdFamily.name}" created (ID: {createdFamily.id}).
            </div>
          ) : null}
        </article>

        <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Join family</h2>
          <p className="mt-2 text-sm text-slate-600">Current user ID: {userId ?? 'unknown'}</p>

          <form className="mt-4 space-y-3" onSubmit={handleJoinFamily}>
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2"
              type="number"
              min={1}
              placeholder="Family ID"
              value={joinForm.familyId}
              onChange={(event) => setJoinForm((prev) => ({ ...prev, familyId: event.target.value }))}
              required
            />

            <button
              className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:bg-blue-300"
              type="submit"
              disabled={isJoining}
            >
              {isJoining ? 'Joining...' : 'Join family'}
            </button>
          </form>

          {joinError ? <p className="mt-3 text-sm text-red-600">{joinError}</p> : null}

          {joinResult ? (
            <div className="mt-3 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">
              Added user {joinResult.user_id} to family {joinResult.family_id}.
            </div>
          ) : null}
        </article>

        <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm lg:col-span-2">
          <h2 className="text-lg font-semibold text-slate-900">View family events</h2>

          <form className="mt-4 grid gap-3 md:grid-cols-3" onSubmit={handleLoadFamilyEvents}>
            <input
              className="rounded-md border border-slate-300 px-3 py-2"
              type="number"
              min={1}
              placeholder="Family ID"
              value={eventsForm.familyId}
              onChange={(event) => setEventsForm((prev) => ({ ...prev, familyId: event.target.value }))}
              required
            />
            <input
              className="rounded-md border border-slate-300 px-3 py-2"
              type="number"
              min={1}
              placeholder="Page"
              value={eventsForm.page}
              onChange={(event) => setEventsForm((prev) => ({ ...prev, page: event.target.value }))}
            />
            <input
              className="rounded-md border border-slate-300 px-3 py-2"
              type="number"
              min={1}
              max={100}
              placeholder="Per page"
              value={eventsForm.perPage}
              onChange={(event) => setEventsForm((prev) => ({ ...prev, perPage: event.target.value }))}
            />

            <div className="md:col-span-3">
              <button
                className="rounded-md bg-slate-800 px-4 py-2 text-white hover:bg-slate-900 disabled:bg-slate-400"
                type="submit"
                disabled={isLoadingEvents}
              >
                {isLoadingEvents ? 'Loading...' : 'Load events'}
              </button>
            </div>
          </form>

          {eventsError ? <p className="mt-3 text-sm text-red-600">{eventsError}</p> : null}

          {!eventsError && familyEvents.length > 0 ? (
            <>
              <p className="mt-4 text-sm text-slate-600">Total events: {eventsTotal}</p>
              <ul className="mt-3 space-y-2">
                {familyEvents.map((eventItem) => (
                  <li key={eventItem.id} className="rounded-md border border-slate-200 p-3">
                    <p className="font-medium text-slate-900">{eventItem.title}</p>
                    <p className="text-sm text-slate-600">{eventItem.description || 'No description'}</p>
                    <p className="text-xs text-slate-500">
                      {eventItem.month}/{eventItem.day}
                      {eventItem.year ? `/${eventItem.year}` : ''}
                    </p>
                  </li>
                ))}
              </ul>
            </>
          ) : null}
        </article>
      </div>
    </section>
  );
}
