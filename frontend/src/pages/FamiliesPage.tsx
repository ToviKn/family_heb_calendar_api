import { EmptyMessage, ErrorMessage, LoadingMessage, SuccessMessage } from '../components/Feedback';
import { FormEvent, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { formatEventDisplayDate, isHebrewCalendarType } from '../lib/dates/eventDateFormatter';

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
  const { t } = useTranslation();

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
      setCreateError(t('families.create.errors.name_required'));
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
      setCreateError(getApiErrorMessage(error, t('families.create.errors.failed')));
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
      setJoinError(t('families.join.errors.invalid_family_id'));
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
      setJoinResultMessage(t('families.join.messages.completed'));
    } catch (error) {
      setJoinError(getApiErrorMessage(error, t('families.join.errors.failed')));
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
      setJoinRequestsError(t('families.requests.errors.invalid_family_id'));
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
      setJoinRequestsError(getApiErrorMessage(error, t('families.requests.errors.load_failed')));
    } finally {
      setIsLoadingJoinRequests(false);
    }
  }

  async function handleJoinRequestAction(requestId: number, action: 'approve' | 'reject') {
    setJoinRequestsError(null);
    setJoinRequestsSuccess(null);

    const familyId = parsePositiveFamilyId(joinRequestsForm.familyId);
    if (familyId === null) {
      setJoinRequestsError(t('families.requests.errors.invalid_family_id_before_review'));
      return;
    }

    setActiveRequestId(requestId);

    try {
      if (action === 'approve') {
        const membership = await approveFamilyJoinRequest(familyId, requestId);
        setJoinRequestsSuccess(t('families.requests.success.approved', {userId: membership.user_id, familyId: membership.family_id,}));
      } else {
        await rejectFamilyJoinRequest(familyId, requestId);
        setJoinRequestsSuccess(t('families.requests.success.rejected'));
      }
      setJoinRequests((prev) => prev.filter((request) => request.id !== requestId));
    } catch (error) {
      setJoinRequestsError(getApiErrorMessage(error, t('families.requests.errors.action_failed', {action,})));
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
      setEventsError(getApiErrorMessage(error, t('families.events.errors.load_failed')));
    } finally {
      setIsLoadingEvents(false);
    }
  }

  const currentJoinFamilyId = parsePositiveFamilyId(joinForm.familyId);
  const isJoinRequestPending = currentJoinFamilyId !== null && pendingJoinFamilyId === currentJoinFamilyId;

  return (
    <section className="space-y-6">
      <header className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">{t('families.title')}</h1>
        <p className="mt-2 text-slate-600">{t('families.description')}</p>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">{t('families.create.title')}</h2>

          <form className="mt-4 space-y-3" onSubmit={handleCreateFamily}>
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2"
              type="text"
              minLength={1}
              maxLength={120}
              placeholder={t('families.create.form.name')}
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
              {isCreatingFamily ? t('families.create.actions.creating') : t('families.create.actions.create')}
            </button>
          </form>

          {createError ? <ErrorMessage message={createError} /> : null}

          {createdFamily ? (
            <div className="mt-3 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">
              {t('families.create.success', {name: createdFamily.name, id: createdFamily.id,})}
            </div>
          ) : null}
        </article>

        <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">{t('families.join.title')}</h2>
          <p className="mt-2 text-sm text-slate-600">{t('families.join.description')}</p>

          <form className="mt-4 space-y-3" onSubmit={handleJoinFamily}>
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2"
              type="number"
              min={1}
              placeholder={t('families.join.form.family_id')}
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
              {isJoining ? t('families.join.actions.sending') : isJoinRequestPending ? t('families.join.actions.pending') : t('families.join.actions.request')}
            </button>
          </form>

          {joinError ? <ErrorMessage message={joinError} /> : null}
          {isJoinRequestPending ? <SuccessMessage message={t('families.join.messages.pending')} /> : null}
          {joinResultMessage ? <SuccessMessage message={joinResultMessage} /> : null}
        </article>

        <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm lg:col-span-2">
          <h2 className="text-lg font-semibold text-slate-900">{t('families.requests.title')}</h2>
          <p className="mt-2 text-sm text-slate-600">{t('families.requests.description')}</p>

          <form className="mt-4 flex flex-col gap-3 md:flex-row" onSubmit={handleLoadJoinRequests}>
            <input
              className="rounded-md border border-slate-300 px-3 py-2 md:w-64"
              type="number"
              min={1}
              placeholder={t('families.join.form.family_id')}
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
              {isLoadingJoinRequests ? t('families.requests.actions.loading') : t('families.requests.actions.load')}
            </button>
          </form>

          {joinRequestsError ? <ErrorMessage message={joinRequestsError} /> : null}
          {joinRequestsSuccess ? <SuccessMessage message={joinRequestsSuccess} /> : null}
          {isLoadingJoinRequests ? <LoadingMessage message={t('families.requests.loading')} /> : null}
          {!joinRequestsError && !isLoadingJoinRequests && !hasLoadedJoinRequests ? (
            <EmptyMessage message={t('families.requests.empty.initial')} />
          ) : null}
          {!joinRequestsError && !isLoadingJoinRequests && hasLoadedJoinRequests && joinRequests.length === 0 ? (
            <EmptyMessage message={t('families.requests.empty.no_requests')} />
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
                        {t('families.requests.requested_by', {name: request.requested_by_user.name, date: new Date(request.created_at).toLocaleString(),})}
                      </p>
                    </div>

                    <div className="flex gap-2">
                      <button
                        className="rounded-md bg-emerald-600 px-3 py-2 text-sm text-white hover:bg-emerald-700 disabled:bg-emerald-300"
                        type="button"
                        disabled={activeRequestId === request.id}
                        onClick={() => void handleJoinRequestAction(request.id, 'approve')}
                      >
                        {activeRequestId === request.id ? t('families.requests.actions.working') : t('families.requests.actions.approve')}
                      </button>
                      <button
                        className="rounded-md bg-red-600 px-3 py-2 text-sm text-white hover:bg-red-700 disabled:bg-red-300"
                        type="button"
                        disabled={activeRequestId === request.id}
                        onClick={() => void handleJoinRequestAction(request.id, 'reject')}
                      >
                        {activeRequestId === request.id ? t('families.requests.actions.working') : t('families.requests.actions.reject')}
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          ) : null}
        </article>

        <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm lg:col-span-2">
          <h2 className="text-lg font-semibold text-slate-900">{t('families.events.title')}</h2>

          <form className="mt-4 grid gap-3 md:grid-cols-3" onSubmit={handleLoadFamilyEvents}>
            <input
              className="rounded-md border border-slate-300 px-3 py-2"
              type="number"
              min={1}
              placeholder={t('families.events.form.family_id')}
              value={eventsForm.familyId}
              onChange={(event) => setEventsForm((prev) => ({ ...prev, familyId: event.target.value }))}
              required
            />
            <input
              className="rounded-md border border-slate-300 px-3 py-2"
              type="number"
              min={1}
              placeholder={t('families.events.form.page')}

              value={eventsForm.page}
              onChange={(event) => setEventsForm((prev) => ({ ...prev, page: event.target.value }))}
            />
            <input
              className="rounded-md border border-slate-300 px-3 py-2"
              type="number"
              min={1}
              max={100}
              placeholder={t('families.events.form.per_page')}
              value={eventsForm.perPage}
              onChange={(event) => setEventsForm((prev) => ({ ...prev, perPage: event.target.value }))}
            />

            <div className="md:col-span-3">
              <button
                className="rounded-md bg-slate-800 px-4 py-2 text-white hover:bg-slate-900 disabled:bg-slate-400"
                type="submit"
                disabled={isLoadingEvents}
              >
                {isLoadingEvents ? t('families.events.actions.loading') : t('families.events.actions.load')}
              </button>
            </div>
          </form>

          {eventsError ? <ErrorMessage message={eventsError} /> : null}
          {isLoadingEvents ? <LoadingMessage message={t('families.events.loading')} /> : null}

          {!eventsError && !isLoadingEvents && familyEvents.length === 0 ? <EmptyMessage message={t('families.events.empty')} /> : null}

          {!eventsError && familyEvents.length > 0 ? (
            <>
              <p className="mt-4 text-sm text-slate-600">{t('families.events.total', {total: eventsTotal,})}</p>
              <ul className="mt-3 space-y-2">
                {familyEvents.map((eventItem) => (
                  <li key={eventItem.id} className="rounded-md border border-slate-200 p-3">
                    <p className="font-medium text-slate-900">{eventItem.title}</p>
                    <p className="text-sm text-slate-600">{eventItem.description || t('families.events.no_description')}</p>
                    <p className="text-xs text-slate-500" dir={isHebrewCalendarType(eventItem.calendar_type) ? 'rtl' : 'ltr'}>
                      {formatEventDisplayDate(eventItem)}
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
