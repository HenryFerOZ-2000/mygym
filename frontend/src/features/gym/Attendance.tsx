import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api, ApiError } from "../../shared/api/client";
import { queryClient } from "../../app/query-client";
import { useWorkspaces } from "../workspaces/use-workspaces";
import type { User } from "../auth/use-session";
import type { Page } from "./types";
import { GymLayout, OperationDialog, Pager, RetryError } from "./ui";
import { displayDate, localDate, message } from "./format";
import { operationAccess } from "./access";
import {
  serviceLabels,
  type Entry,
  type EntryPreview,
} from "./attendance-types";

function ServiceDates({ entry }: { entry: EntryPreview }) {
  return (
    <>
      {entry.last_day && (
        <p>Último día del período vigente: {displayDate(entry.last_day)}</p>
      )}
      {!entry.last_day && entry.previous_last_day && (
        <p>Último día cubierto: {displayDate(entry.previous_last_day)}</p>
      )}
      {entry.next_start && (
        <p>Próximo período: {displayDate(entry.next_start)}</p>
      )}
    </>
  );
}

export function Attendance({ user }: { user: User }) {
  const { workspaceId = "" } = useParams();
  const spaces = useWorkspaces(user.id);
  const workspace = spaces.data?.find((w) => w.id === workspaceId);
  const access = operationAccess(spaces.isError ? undefined : workspace);
  const base = `workspaces/${workspaceId}/`;
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [historyPage, setHistoryPage] = useState(1);
  const [date, setDate] = useState("");
  const day = date || localDate(workspace?.timezone ?? "America/Guayaquil");
  const [selected, setSelected] = useState("");
  const [review, setReview] = useState<EntryPreview | null>(null);
  const [voidEntry, setVoidEntry] = useState<Entry | null>(null);
  const [notice, setNotice] = useState("");
  const searchQuery = useQuery({
    queryKey: [user.id, workspaceId, "attendance-search", search, page],
    queryFn: ({ signal }) =>
      api<Page<{ id: string; full_name: string; is_active: boolean }>>(
        `${base}attendance/clients/?q=${encodeURIComponent(search)}&page=${page}`,
        { signal },
      ),
    enabled: access.attendance,
  });
  const history = useQuery({
    queryKey: [
      user.id,
      workspaceId,
      "attendance-history",
      search,
      day,
      historyPage,
    ],
    queryFn: ({ signal }) =>
      api<Page<Entry>>(
        `${base}attendance/?q=${encodeURIComponent(search)}&date=${day}&page=${historyPage}`,
        { signal },
      ),
    enabled: access.attendance,
  });
  const preview = useQuery({
    queryKey: [user.id, workspaceId, "attendance-preview", selected],
    queryFn: ({ signal }) =>
      api<EntryPreview>(`${base}clients/${selected}/attendance/preview/`, {
        signal,
      }),
    enabled: !!selected && access.attendance,
    staleTime: 0,
  });
  // Capture once per explicitly opened review. Background refetches must not
  // replace an in-flight or uncertain attempt and its idempotency key.
  if (
    selected &&
    !review &&
    preview.data &&
    !preview.isError &&
    !preview.isFetching
  ) {
    setReview(preview.data);
  }
  const entry = review?.client_id === selected ? review : undefined;
  const blocked = entry && ["FROZEN", "CLIENT_INACTIVE"].includes(entry.status);
  const exception = entry?.status !== "ACTIVE";
  async function refresh() {
    await queryClient.invalidateQueries({ queryKey: [user.id, workspaceId] });
  }
  return (
    <GymLayout workspace={workspace} title="Asistencia">
      <p className="muted">
        Registra cada visita después de revisar el servicio. Las deudas no
        bloquean una membresía vigente.
      </p>
      {spaces.isPending && <p role="status">Validando acceso…</p>}
      {spaces.isError && <p role="alert">{message(spaces.error)}</p>}
      {!spaces.isPending && !access.attendance && (
        <p role="alert">No tienes acceso a asistencia en este espacio.</p>
      )}
      {notice && (
        <p role="status" className="success-note">
          {notice}
        </p>
      )}
      {access.attendance && (
        <>
          <section className="gym-card" aria-label="Buscar personas">
            <label>
              Buscar cliente
              <input
                value={search}
                maxLength={120}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                  setHistoryPage(1);
                }}
                placeholder="Nombre del cliente"
              />
            </label>
            {searchQuery.isFetching && <p role="status">Buscando…</p>}
            {searchQuery.isError && (
              <RetryError
                error={searchQuery.error}
                label="Reintentar búsqueda"
                busy={searchQuery.isFetching}
                onRetry={() => void searchQuery.refetch()}
              />
            )}
            {!searchQuery.isError && searchQuery.data && (
              <>
                <div className="attendance-results">
                  {searchQuery.data.results.map((client) => (
                    <div className="attendance-person" key={client.id}>
                      <span>
                        <strong>{client.full_name}</strong>
                        {!client.is_active && <small> · Ficha inactiva</small>}
                      </span>
                      <button
                        className="button secondary"
                        aria-label={`Revisar entrada de ${client.full_name}`}
                        onClick={() => {
                          setNotice("");
                          setReview(null);
                          setSelected(client.id);
                        }}
                      >
                        Revisar entrada
                      </button>
                    </div>
                  ))}
                </div>
                {!searchQuery.data.count && <p>No se encontraron clientes.</p>}
                <Pager
                  number={page}
                  next={searchQuery.data.next}
                  set={setPage}
                />
              </>
            )}
          </section>
          {selected && !entry && preview.isFetching && (
            <p role="status">Revisando servicio…</p>
          )}
          {selected && preview.isError && (
            <p role="alert">
              {message(preview.error)}{" "}
              <button
                className="button secondary"
                onClick={() => void preview.refetch()}
              >
                Volver a revisar
              </button>
            </p>
          )}
          {selected && entry && (blocked || (exception && !access.owner)) && (
            <section className="gym-card" role="alert">
              <h2>{entry.full_name}</h2>
              <ServiceDates entry={entry} />
              <p>
                {serviceLabels[entry.status]}.{" "}
                {blocked
                  ? "Entrada bloqueada."
                  : "Sólo el propietario puede autorizar una excepción con motivo."}
              </p>
              <button
                className="button secondary"
                onClick={() => setSelected("")}
              >
                Cerrar revisión
              </button>
            </section>
          )}
          {selected && entry && !blocked && (!exception || access.owner) && (
            <OperationDialog
              key={selected}
              title={`Entrada de ${entry.full_name}`}
              submitLabel="Confirmar entrada"
              onClose={() => setSelected("")}
              onSubmit={async (form, send) => {
                try {
                  await send(`${base}clients/${selected}/attendance/`, {
                    expected_date: entry.local_date,
                    expected_count: entry.today_count,
                    confirm_repeat: form.get("repeat") === "on",
                    exception,
                    reason: exception ? String(form.get("reason") ?? "") : "",
                  });
                } catch (error) {
                  // A rejected operation is safe to review again; a lost response must
                  // retain the same request key so retry cannot record another visit.
                  if (
                    error instanceof ApiError &&
                    [400, 403, 404].includes(error.status)
                  ) {
                    setNotice(message(error));
                    setSelected("");
                    void refresh();
                  }
                  throw error;
                }
                setNotice("Entrada registrada.");
                await refresh();
              }}
            >
              <p>
                {serviceLabels[entry.status]} · {displayDate(entry.local_date)}{" "}
                · {entry.timezone}
              </p>
              <p>Entradas válidas hoy: {entry.today_count}</p>
              <ServiceDates entry={entry} />
              {entry.today_count > 0 && (
                <label>
                  <input type="checkbox" name="repeat" required /> Confirmo otra
                  visita hoy
                </label>
              )}
              {exception && (
                <>
                  <p>Autorización excepcional del propietario.</p>
                  <label>
                    Motivo de excepción
                    <textarea name="reason" required maxLength={300} />
                  </label>
                </>
              )}
            </OperationDialog>
          )}
          <section className="gym-card" aria-label="Historial de entradas">
            <h2>Entradas del día</h2>
            <label>
              Fecha del historial
              <input
                type="date"
                value={day}
                onChange={(e) => {
                  setDate(e.target.value);
                  setHistoryPage(1);
                }}
              />
            </label>
            <p className="muted">
              Fecha local guardada en cada entrada. Una anulación corrige el
              registro; no representa una salida.
            </p>
            {history.isFetching && <p role="status">Cargando entradas…</p>}
            {history.isError && (
              <RetryError
                error={history.error}
                label="Reintentar historial"
                busy={history.isFetching}
                onRetry={() => void history.refetch()}
              />
            )}
            {!history.isError && history.data && (
              <>
                <div className="attendance-results">
                  {history.data.results.map((item) => (
                    <article className="attendance-person" key={item.id}>
                      <div>
                        <strong>{item.full_name}</strong>
                        <p>
                          {new Date(item.created_at).toLocaleTimeString(
                            "es-EC",
                            { timeZone: item.timezone },
                          )}{" "}
                          ·{" "}
                          {item.decision === "EXCEPTION"
                            ? "Excepción"
                            : "Entrada normal"}{" "}
                          · {item.actor}
                        </p>
                        {item.reason && <p>{item.reason}</p>}
                        {item.voided && (
                          <>
                            <span className="badge">Anulada</span>
                            <p>{item.void_reason}</p>
                            <p>
                              Anulada por {item.void_actor}
                              {item.voided_at &&
                                ` · ${new Date(item.voided_at).toLocaleString("es-EC", { timeZone: item.timezone })}`}
                            </p>
                          </>
                        )}
                      </div>
                      {!item.voided && access.owner && (
                        <button
                          className="button secondary"
                          aria-label={`Anular entrada de ${item.full_name}`}
                          onClick={() => setVoidEntry(item)}
                        >
                          Anular
                        </button>
                      )}
                    </article>
                  ))}
                </div>
                {!history.data.count && (
                  <p>No hay entradas para esta fecha y búsqueda.</p>
                )}
                <Pager
                  number={historyPage}
                  next={history.data.next}
                  set={setHistoryPage}
                />
              </>
            )}
          </section>
        </>
      )}
      {voidEntry && access.attendance && access.owner && (
        <OperationDialog
          title={`Anular entrada de ${voidEntry.full_name}`}
          submitLabel="Confirmar anulación"
          onClose={() => setVoidEntry(null)}
          onSubmit={async (form, send) => {
            await send(`${base}attendance/${voidEntry.id}/void/`, {
              reason: form.get("reason"),
            });
            setNotice("Entrada anulada.");
            await refresh();
          }}
        >
          <p>El registro original se conserva en el historial.</p>
          <label>
            Motivo de anulación
            <textarea name="reason" required maxLength={300} />
          </label>
        </OperationDialog>
      )}
    </GymLayout>
  );
}
