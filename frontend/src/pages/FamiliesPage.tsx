import { EmptyMessage, ErrorMessage, LoadingMessage, SuccessMessage } from '../components/Feedback';
import { FormEvent, useState } from 'react';

import {
  approveFamilyJoinRequest,
  createFamily,
  getApiErrorMessage,
  getFamilyEvents,
  listFamilyJoinRequests,
  rejectFamilyJoinRequest,
  requestFamilyJoin,
  type EventResponse,
  type FamilyJoinRequestDetailResponse,
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

interface JoinRequestsForm {
  familyId: string;
}

function parsePositiveFamilyId(value: string): number | null {
  const familyId = Number(value);
  return Number.isInteger(familyId) && familyId > 0 ? familyId : null;
}

export function FamiliesPage() {
  const [createForm, setCreateForm] = useState<CreateFamilyForm>({ name: '' });
  const [createdFamily, setCreatedFamily] = useState<FamilyResponse | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);
  const [isCreatingFamily, setIsCreatingFamily] = useState(false);

  const [joinForm, setJoinForm] = useState<JoinFamilyForm>({ familyId: '' });
  const [joinResultMessage, setJoinResultMessage] = useState<string | null>(null);
  const [pendingJoinFamilyId, setPendingJoinFamilyId] = useState<number | null>(null);
  const [joinError, setJoinError] = useState<string | null>(null);
  const [isJoining, setIsJoining] = useState(false);

  const [joinRequestsForm, setJoinRequestsForm] = useState<JoinRequestsForm>({ familyId: '' });
  const [joinRequests, setJoinRequests] = useState<FamilyJoinRequestDetailResponse[]>([]);
  const [hasLoadedJoinRequests, setHasLoadedJoinRequests] = useState(false);
  const [joinRequestsError, setJoinRequestsError] = useState<string | null>(null);
  const [joinRequestsSuccess, setJoinRequestsSuccess] = useState<string | null>(null);
  const [isLoadingJoinRequests, setIsLoadingJoinRequests] = useState(false);
  const [activeRequestId, setActiveRequestId] = useState<number | null>(null);

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
      setJoinRequestsForm((prev) => ({ ...prev, familyId: String(family.id) }));
      setEventsForm((prev) => ({ ...prev, familyId: String(family.id) }));
    } catch (error) {
      setCreateError(getApiErrorMessage(error, 'Unable to create family. Please try a different name.'));
    } finally {
      setIsCreatingFamily(false);
    }
  }

  async function handleJoinFamily(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setJoinError(null);
    setJoinResultMessage(null);

    const familyId = parsePositiveFamilyId(joinForm.familyId);
    if (familyId === null) {
      setJoinError('Enter a valid family ID.');
      return;
    }

    setIsJoining(true);

    try {
      const result = await requestFamilyJoin(familyId);
      if (result.status === 'pending') {
        setPendingJoinFamilyId(familyId);
        return;
      }
      setPendingJoinFamilyId(null);
      setJoinResultMessage(result.message);
    } catch (error) {
      setJoinError(getApiErrorMessage(error, 'Unable to request family access. Verify family ID and try again.'));
    } finally {
      setIsJoining(false);
    }
  }

  async function handleLoadJoinRequests(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault();
    setJoinRequestsError(null);
    setJoinRequestsSuccess(null);

    const familyId = parsePositiveFamilyId(joinRequestsForm.familyId);
    if (familyId === null) {
      setJoinRequests([]);
      setHasLoadedJoinRequests(false);
      setJoinRequestsError('Enter a valid family ID to load join requests.');
      return;
    }

    setJoinRequests([]);
    setHasLoadedJoinRequests(false);
    setIsLoadingJoinRequests(true);

    try {
      const result = await listFamilyJoinRequests(familyId);
      setJoinRequests(result.requests);
      setHasLoadedJoinRequests(true);
    } catch (error) {
      setJoinRequests([]);
      setHasLoadedJoinRequests(false);
      setJoinRequestsError(getApiErrorMessage(error, 'Unable to load join requests. Verify family ID and admin permissions.'));
    } finally {
      setIsLoadingJoinRequests(false);
    }
  }

  async function handleJoinRequestAction(requestId: number, action: 'approve' | 'reject') {
    setJoinRequestsError(null);
    setJoinRequestsSuccess(null);

    const familyId = parsePositiveFamilyId(joinRequestsForm.familyId);
    if (familyId === null) {
      setJoinRequestsError('Enter a valid family ID before reviewing requests.');
      return;
    }

    setActiveRequestId(requestId);

    try {
      if (action === 'approve') {
        const membership = await approveFamilyJoinRequest(familyId, requestId);
        setJoinRequestsSuccess(`Approved user ${membership.user_id} for family ${membership.family_id}.`);
      } else {
        await rejectFamilyJoinRequest(familyId, requestId);
        setJoinRequestsSuccess('Join request rejected.');
      }
      setJoinRequests((prev) => prev.filter((request) => request.id !== requestId));
    } catch (error) {
      setJoinRequestsError(getApiErrorMessage(error, `Unable to ${action} join request. Please try again.`));
    } finally {
      setActiveRequestId(null);
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
    } catch (error) {
      setFamilyEvents([]);
      setEventsTotal(0);
      setEventsError(getApiErrorMessage(error, 'Unable to load family events. Verify family ID and permissions.'));
    } finally {
      setIsLoadingEvents(false);
    }
  }

  const currentJoinFamilyId = parsePositiveFamilyId(joinForm.familyId);
  const isJoinRequestPending = currentJoinFamilyId !== null && pendingJoinFamilyId === currentJoinFamilyId;

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

          {createError ? <ErrorMessage message={createError} /> : null}

          {createdFamily ? (
            <div className="mt-3 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">
              Family &quot;{createdFamily.name}&quot; created (ID: {createdFamily.id}).
            </div>
          ) : null}
        </article>

        <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Join family</h2>
          <p className="mt-2 text-sm text-slate-600">Enter a family ID to request access from a family admin.</p>

          <form className="mt-4 space-y-3" onSubmit={handleJoinFamily}>
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2"
              type="number"
              min={1}
              placeholder="Family ID"
              value={joinForm.familyId}
              onChange={(event) => {
                setJoinForm((prev) => ({ ...prev, familyId: event.target.value }));
                setJoinResultMessage(null);
                setJoinError(null);
              }}
              required
            />

            <button
              className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:bg-blue-300"
              type="submit"
              disabled={isJoining || isJoinRequestPending}
            >
              {isJoining ? 'Sending...' : isJoinRequestPending ? 'Request pending' : 'Request to Join'}
            </button>
          </form>

          {joinError ? <ErrorMessage message={joinError} /> : null}
          {isJoinRequestPending ? <SuccessMessage message="Join request sent. Waiting for approval." /> : null}
          {joinResultMessage ? <SuccessMessage message={joinResultMessage} /> : null}
        </article>

        <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm lg:col-span-2">
          <h2 className="text-lg font-semibold text-slate-900">Join Requests</h2>
          <p className="mt-2 text-sm text-slate-600">Family admins can review pending requests for a family.</p>

          <form className="mt-4 flex flex-col gap-3 md:flex-row" onSubmit={handleLoadJoinRequests}>
            <input
              className="rounded-md border border-slate-300 px-3 py-2 md:w-64"
              type="number"
              min={1}
              placeholder="Family ID"
              value={joinRequestsForm.familyId}
              onChange={(event) => {
                setJoinRequestsForm({ familyId: event.target.value });
                setJoinRequestsError(null);
                setJoinRequestsSuccess(null);
                setHasLoadedJoinRequests(false);
                setJoinRequests([]);
              }}
              required
            />

            <button
              className="rounded-md bg-slate-800 px-4 py-2 text-white hover:bg-slate-900 disabled:bg-slate-400"
              type="submit"
              disabled={isLoadingJoinRequests}
            >
              {isLoadingJoinRequests ? 'Loading...' : 'Load join requests'}
            </button>
          </form>

          {joinRequestsError ? <ErrorMessage message={joinRequestsError} /> : null}
          {joinRequestsSuccess ? <SuccessMessage message={joinRequestsSuccess} /> : null}
          {isLoadingJoinRequests ? <LoadingMessage message="Loading join requests..." /> : null}
          {!joinRequestsError && !isLoadingJoinRequests && !hasLoadedJoinRequests ? (
            <EmptyMessage message="Load a family to review pending join requests." />
          ) : null}
          {!joinRequestsError && !isLoadingJoinRequests && hasLoadedJoinRequests && joinRequests.length === 0 ? (
            <EmptyMessage message="No pending join requests for this family." />
          ) : null}

          {!joinRequestsError && joinRequests.length > 0 ? (
            <ul className="mt-4 space-y-3">
              {joinRequests.map((request) => (
                <li key={request.id} className="rounded-md border border-slate-200 p-4">
                  <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                    <div>
                      <p className="font-medium text-slate-900">{request.user.name}</p>
                      <p className="text-sm text-slate-600">{request.user.email}</p>
                      <p className="text-xs text-slate-500">
                        Requested by {request.requested_by_user.name} on {new Date(request.created_at).toLocaleString()}
                      </p>
                    </div>

                    <div className="flex gap-2">
                      <button
                        className="rounded-md bg-emerald-600 px-3 py-2 text-sm text-white hover:bg-emerald-700 disabled:bg-emerald-300"
                        type="button"
                        disabled={activeRequestId === request.id}
                        onClick={() => void handleJoinRequestAction(request.id, 'approve')}
                      >
                        {activeRequestId === request.id ? 'Working...' : 'Approve'}
                      </button>
                      <button
                        className="rounded-md bg-red-600 px-3 py-2 text-sm text-white hover:bg-red-700 disabled:bg-red-300"
                        type="button"
                        disabled={activeRequestId === request.id}
                        onClick={() => void handleJoinRequestAction(request.id, 'reject')}
                      >
                        {activeRequestId === request.id ? 'Working...' : 'Reject'}
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
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

          {eventsError ? <ErrorMessage message={eventsError} /> : null}
          {isLoadingEvents ? <LoadingMessage message="Loading family events..." /> : null}

          {!eventsError && !isLoadingEvents && familyEvents.length === 0 ? <EmptyMessage message="No family events loaded yet." /> : null}

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
