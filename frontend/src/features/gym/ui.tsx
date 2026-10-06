import {
  useEffect,
  useRef,
  useState,
  type ReactNode,
  type FormEvent,
} from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../../shared/api/client";
import { message } from "./format";
import { queryClient } from "../../app/query-client";
import { LogoutButton } from "../../shared/ui/LogoutButton";
import type { Workspace } from "../workspaces/use-workspaces";
import { operationAccess } from "./access";

export function GymLayout({
  workspace,
  title,
  children,
}: {
  workspace?: Workspace;
  title: string;
  children: ReactNode;
}) {
  const access = operationAccess(workspace);
  return (
    <div className="gym-shell">
      <header className="gym-header">
        <Link className="brand" to="/workspaces">
          mygym<span className="brand-dot">●</span>
        </Link>
        <span>{workspace?.name ?? "Validando espacio…"}</span>
        <LogoutButton />
      </header>
      <nav className="gym-nav" aria-label="Principal">
        {access.clients && (
          <Link to={`/workspaces/${workspace?.id}/clients`}>Clientes</Link>
        )}
        {access.plans && (
          <Link to={`/workspaces/${workspace?.id}/plans`}>
            Planes y promociones
          </Link>
        )}
        <Link to="/workspaces">Cambiar espacio</Link>
        {access.attendance && (
          <Link to={`/workspaces/${workspace?.id}/attendance`}>Asistencia</Link>
        )}
        {(access.expiries ||
          access.attendanceReport ||
          access.financialReport) && (
          <Link to={`/workspaces/${workspace?.id}/reports`}>
            Vencimientos y reportes
          </Link>
        )}
      </nav>
      <main className="gym-main">
        <h1>{title}</h1>
        {children}
      </main>
    </div>
  );
}
export function RetryError({
  error,
  label,
  busy,
  onRetry,
}: {
  error: unknown;
  label: string;
  busy: boolean;
  onRetry: () => void;
}) {
  return (
    <div role="alert" className="error-box">
      <p>{message(error)}</p>
      <button className="button secondary" disabled={busy} onClick={onRetry}>
        {busy ? "Consultando…" : label}
      </button>
    </div>
  );
}

export function Pager({
  number,
  next,
  set,
}: {
  number: number;
  next: number | null;
  set: (value: number) => void;
}) {
  return (
    <div className="pagination">
      <span>Página {number}</span>
      <div>
        <button
          className="button secondary"
          disabled={number === 1}
          onClick={() => set(number - 1)}
        >
          Anterior
        </button>
        <button
          className="button secondary"
          disabled={!next}
          onClick={() => set(number + 1)}
        >
          Siguiente
        </button>
      </div>
    </div>
  );
}
export function OperationDialog({
  title,
  children,
  submitLabel,
  onClose,
  onSubmit,
}: {
  title: string;
  children: ReactNode;
  submitLabel: string;
  onClose: () => void;
  onSubmit: (
    form: FormData,
    send: <T>(url: string, payload: object, method?: string) => Promise<T>,
  ) => Promise<void>;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const keys = useRef(new Map<string, string>());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    dialog.current?.showModal();
  }, []);
  async function send<T>(
    url: string,
    payload: object,
    method = "POST",
  ): Promise<T> {
    const key = JSON.stringify([url, payload]);
    if (!keys.current.has(key)) keys.current.set(key, crypto.randomUUID());
    return api<T>(url, {
      method,
      body: JSON.stringify({
        ...payload,
        ...(method === "POST" && !url.endsWith("gym/plans/")
          ? { request_id: keys.current.get(key) }
          : {}),
      }),
    });
  }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      await onSubmit(new FormData(event.currentTarget), send);
      onClose();
    } catch (error) {
      setError(message(error));
      if (error instanceof ApiError && [403, 404].includes(error.status))
        void queryClient.invalidateQueries();
    } finally {
      setBusy(false);
    }
  }
  return (
    <dialog
      ref={dialog}
      className="client-dialog gym-dialog"
      aria-labelledby="operation-title"
      onCancel={(event) => {
        if (busy) event.preventDefault();
        else onClose();
      }}
    >
      <h2 id="operation-title">{title}</h2>
      <form onSubmit={submit}>
        <fieldset disabled={busy}>{children}</fieldset>
        {error && (
          <p role="alert" className="error-note">
            {error}
          </p>
        )}
        <div className="dialog-actions">
          <button
            type="button"
            className="button secondary"
            disabled={busy}
            onClick={onClose}
          >
            Cerrar
          </button>
          <button className="button primary" disabled={busy} aria-busy={busy}>
            {busy ? "Guardando…" : submitLabel}
          </button>
        </div>
      </form>
    </dialog>
  );
}
