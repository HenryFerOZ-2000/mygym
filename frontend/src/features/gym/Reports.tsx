import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../shared/api/client";
import { useWorkspaces } from "../workspaces/use-workspaces";
import type { User } from "../auth/use-session";
import type { Page } from "./types";
import { GymLayout, Pager, RetryError } from "./ui";
import { displayDate, localDate, message, shiftDate } from "./format";
import { operationAccess } from "./access";
import { serviceLabels } from "./attendance-types";

type Expiry = {
  client_id: string;
  full_name: string;
  status: string;
  last_day: string | null;
  previous_end: string | null;
  next_start: string | null;
  calendar_days_remaining: number | null;
};
type Expiries = Page<Expiry> & { reference_date: string; timezone: string };
type AttendanceTotals = {
  entries: number;
  clients: number;
  exceptions: number;
  voided: number;
  as_of: string;
};
type FinancialTotals = {
  as_of: string;
  timezone: string;
  currencies: {
    currency: string;
    payments: string;
    refunds: string;
    net: string;
    outstanding_now: string;
  }[];
};

export function Reports({ user }: { user: User }) {
  const { workspaceId = "" } = useParams();
  const spaces = useWorkspaces(user.id);
  const workspace = spaces.data?.find((w) => w.id === workspaceId);
  const access = operationAccess(spaces.isError ? undefined : workspace);
  const base = `workspaces/${workspaceId}/`;
  const today = localDate(workspace?.timezone ?? "America/Guayaquil");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const start = from || today,
    end = to || today;
  const range = `from_date=${start}&to_date=${end}`;
  const [status, setStatus] = useState("EXPIRING");
  const [horizon, setHorizon] = useState("7");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const expiry = useQuery({
    queryKey: [user.id, workspaceId, "expiries", status, horizon, search, page],
    queryFn: ({ signal }) =>
      api<Expiries>(
        `${base}gym/expiries/?status=${status}&horizon=${horizon}&q=${encodeURIComponent(search)}&page=${page}`,
        { signal },
      ),
    enabled: access.expiries,
  });
  const attendance = useQuery({
    queryKey: [user.id, workspaceId, "attendance-report", start, end],
    queryFn: ({ signal }) =>
      api<AttendanceTotals>(`${base}reports/attendance/?${range}`, { signal }),
    enabled: access.attendanceReport,
  });
  const financial = useQuery({
    queryKey: [user.id, workspaceId, "financial-report", start, end],
    queryFn: ({ signal }) =>
      api<FinancialTotals>(`${base}reports/financial/?${range}`, { signal }),
    enabled: access.financialReport,
  });
  return (
    <GymLayout workspace={workspace} title="Vencimientos y reportes">
      {spaces.isPending && <p role="status">Validando acceso…</p>}
      {spaces.isError && <p role="alert">{message(spaces.error)}</p>}
      {!spaces.isPending &&
        !access.expiries &&
        !access.attendanceReport &&
        !access.financialReport && (
          <p role="alert">No tienes acceso a estos reportes en este espacio.</p>
        )}
      {access.expiries && (
        <section className="gym-card">
          <h2>Vencimientos</h2>
          <p className="muted">
            La cobertura incluye renovaciones contiguas. Los días mostrados son
            calendario hasta el último día contratado.
          </p>
          <div className="report-filters">
            <label>
              Estado del servicio
              <select
                value={status}
                onChange={(e) => {
                  setStatus(e.target.value);
                  setPage(1);
                }}
              >
                {Object.entries(serviceLabels).map(([key, label]) => (
                  <option value={key} key={key}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Horizonte
              <select
                value={horizon}
                onChange={(e) => {
                  setHorizon(e.target.value);
                  setPage(1);
                }}
              >
                {[7, 15, 30, 60, 90].map((n) => (
                  <option value={n} key={n}>
                    {n} días
                  </option>
                ))}
              </select>
            </label>
            <label>
              Filtrar cliente
              <input
                maxLength={120}
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
              />
            </label>
          </div>
          {expiry.isFetching && <p role="status">Consultando vencimientos…</p>}
          {expiry.isError && (
            <RetryError
              error={expiry.error}
              label="Reintentar vencimientos"
              busy={expiry.isFetching}
              onRetry={() => void expiry.refetch()}
            />
          )}
          {!expiry.isError && expiry.data && (
            <>
              <p>
                Referencia: {displayDate(expiry.data.reference_date)} ·{" "}
                {expiry.data.timezone}
              </p>
              <div className="attendance-results">
                {expiry.data.results.map((row) => (
                  <article className="attendance-person" key={row.client_id}>
                    <div>
                      <strong>{row.full_name}</strong>
                      <p>{serviceLabels[row.status]}</p>
                      {row.last_day && (
                        <p>
                          Último día: {displayDate(row.last_day)} ·{" "}
                          {row.calendar_days_remaining} días calendario
                        </p>
                      )}
                      {row.status === "EXPIRED" && row.previous_end && (
                        <p>
                          Último día cubierto:{" "}
                          {displayDate(shiftDate(row.previous_end, -1))}
                        </p>
                      )}
                      {row.next_start && (
                        <p>Próximo período: {displayDate(row.next_start)}</p>
                      )}
                    </div>
                    <Link
                      className="button secondary"
                      to={`/workspaces/${workspaceId}/clients/${row.client_id}/account`}
                    >
                      Ver membresías
                    </Link>
                  </article>
                ))}
              </div>
              {!expiry.data.count && <p>No hay clientes para estos filtros.</p>}
              <Pager number={page} next={expiry.data.next} set={setPage} />
            </>
          )}
        </section>
      )}
      {(access.attendanceReport || access.financialReport) && (
        <section className="gym-card">
          <h2>Período de consulta</h2>
          <p>
            Fechas inclusivas, hasta 366 días. Zona horaria:{" "}
            {workspace?.timezone}.
          </p>
          <div className="report-filters">
            <label>
              Desde
              <input
                type="date"
                value={start}
                onChange={(e) => setFrom(e.target.value)}
              />
            </label>
            <label>
              Hasta
              <input
                type="date"
                value={end}
                onChange={(e) => setTo(e.target.value)}
              />
            </label>
            <button
              className="button secondary"
              onClick={() => {
                if (access.attendanceReport) void attendance.refetch();
                if (access.financialReport) void financial.refetch();
              }}
            >
              Actualizar reportes
            </button>
          </div>
        </section>
      )}
      {access.attendanceReport && (
        <section className="gym-card">
          <h2>Asistencia del período</h2>
          <p className="muted">
            Por fecha local de entrada. Las anulaciones se reflejan sobre esa
            fecha; las visitas repetidas cuentan como entradas adicionales.
          </p>
          {attendance.isFetching && <p role="status">Calculando asistencia…</p>}
          {attendance.isError && (
            <p role="alert">{message(attendance.error)}</p>
          )}
          {!attendance.isError && attendance.data && (
            <>
              <div className="report-metrics">
                {[
                  ["Entradas válidas", attendance.data.entries],
                  ["Clientes distintos", attendance.data.clients],
                  ["Excepciones válidas", attendance.data.exceptions],
                  ["Entradas anuladas", attendance.data.voided],
                ].map(([label, value]) => (
                  <div key={label}>
                    <span>{label}</span>
                    <strong>{value}</strong>
                  </div>
                ))}
              </div>
              <p className="muted">
                Consultado:{" "}
                {new Date(attendance.data.as_of).toLocaleString("es-EC", {
                  timeZone: workspace?.timezone,
                })}
              </p>
            </>
          )}
        </section>
      )}
      {access.financialReport && (
        <section className="gym-card">
          <h2>Movimientos manuales</h2>
          <p className="muted">
            Pagos y devoluciones registrados en el período, separados por
            moneda. El saldo pendiente es actual y no corresponde al cierre
            histórico del rango.
          </p>
          {financial.isFetching && <p role="status">Calculando movimientos…</p>}
          {financial.isError && <p role="alert">{message(financial.error)}</p>}
          {!financial.isError && financial.data && (
            <>
              <div className="gym-grid">
                {financial.data.currencies.map((row) => (
                  <article className="gym-card" key={row.currency}>
                    <h3>{row.currency}</h3>
                    <dl className="money-summary">
                      <dt>Pagos del período</dt>
                      <dd>{row.payments}</dd>
                      <dt>Devoluciones del período</dt>
                      <dd>{row.refunds}</dd>
                      <dt>Movimiento neto</dt>
                      <dd>{row.net}</dd>
                      <dt>Saldo pendiente actual</dt>
                      <dd>{row.outstanding_now}</dd>
                    </dl>
                  </article>
                ))}
              </div>
              {!financial.data.currencies.length && (
                <p>No hay cargos ni movimientos para mostrar.</p>
              )}
              <p className="muted">
                Saldo actual consultado:{" "}
                {new Date(financial.data.as_of).toLocaleString("es-EC", {
                  timeZone: financial.data.timezone,
                })}{" "}
                · {financial.data.timezone}
              </p>
            </>
          )}
        </section>
      )}
    </GymLayout>
  );
}
