import { useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, ApiError } from "../../shared/api/client";
import { queryClient } from "../../app/query-client";
import type { Page, Plan, Preview } from "./types";
import { Pager } from "./ui";
import { displayDate, localDate, message, planAvailability } from "./format";

export function Enrollment({
  userId,
  workspaceId,
  clientId,
  zone,
  onSaved,
}: {
  userId: number;
  workspaceId: string;
  clientId: string;
  zone: string;
  onSaved: () => void;
}) {
  const [page, setPage] = useState(1);
  const [planId, setPlanId] = useState("");
  const [start, setStart] = useState(() => localDate(zone));
  const [preview, setPreview] = useState<Preview | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [denied, setDenied] = useState(false);
  function handleError(error: unknown) {
    setError(message(error));
    if (error instanceof ApiError && [403, 404].includes(error.status)) {
      setPreview(null);
      setDenied(true);
      void queryClient.invalidateQueries();
    }
  }
  const key = useRef(crypto.randomUUID());
  const plans = useQuery({
    queryKey: [userId, workspaceId, "plans", page],
    queryFn: ({ signal }) =>
      api<Page<Plan>>(`workspaces/${workspaceId}/gym/plans/?page=${page}`, {
        signal,
      }),
  });
  const base = `workspaces/${workspaceId}/clients/${clientId}/gym/`;
  async function review() {
    setBusy(true);
    setError("");
    setPreview(null);
    try {
      setPreview(
        await api<Preview>(base + "preview/", {
          method: "POST",
          body: JSON.stringify({ plan_id: planId, start_date: start }),
        }),
      );
      key.current = crypto.randomUUID();
    } catch (error) {
      handleError(error);
    } finally {
      setBusy(false);
    }
  }
  async function enroll() {
    if (!preview) return;
    setBusy(true);
    setError("");
    try {
      await api(base + "memberships/", {
        method: "POST",
        body: JSON.stringify({
          request_id: key.current,
          plan_id: planId,
          start_date: start,
          expected_version: preview.version,
          expected_start: preview.start_date,
          expected_end: preview.end_date,
        }),
      });
      setPreview(null);
      onSaved();
      await queryClient.invalidateQueries({
        queryKey: [userId, workspaceId, clientId],
      });
    } catch (error) {
      handleError(error);
    } finally {
      setBusy(false);
    }
  }
  if (denied) return <p role="alert">{error}</p>;
  return (
    <section className="gym-card">
      <h2>Inscribir o renovar</h2>
      <p>
        La renovación anticipada conserva los días contratados. El cargo se
        registra separado del pago.
      </p>
      {plans.isError ? (
        <p role="alert">{message(plans.error)}</p>
      ) : (
        <>
          <fieldset disabled={busy}>
            <label>
              Plan para inscribir
              <select
                value={planId}
                onChange={(e) => {
                  setPlanId(e.target.value);
                  setPreview(null);
                }}
              >
                <option value="">Selecciona un plan</option>
                {plans.data?.results
                  .filter(
                    (p) =>
                      planAvailability(p, localDate(zone)) === "Disponible",
                  )
                  .map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
              </select>
            </label>
            {plans.data && plans.data.count > 25 && (
              <Pager number={page} next={plans.data.next} set={setPage} />
            )}
            <label>
              Inicio solicitado
              <input
                type="date"
                value={start}
                min={localDate(zone)}
                onChange={(e) => {
                  setStart(e.target.value);
                  setPreview(null);
                }}
              />
            </label>
            <button
              className="button secondary"
              disabled={!planId || !start}
              onClick={() => void review()}
            >
              Revisar inscripción
            </button>
          </fieldset>
          {preview && (
            <div className="gym-preview">
              <strong>
                {preview.name} · versión {preview.version}
              </strong>
              <p>
                Desde {displayDate(preview.start_date)} hasta{" "}
                {displayDate(preview.last_day)}, ambos incluidos.
              </p>
              <p>Vence al comenzar el {displayDate(preview.end_date)}.</p>
              <p>
                Total del cargo: {preview.currency} {preview.amount}
              </p>
              <p>
                Saldo inicial: {preview.currency} {preview.amount}. No se
                registra un pago automáticamente.
              </p>
              <button
                className="button primary"
                disabled={busy}
                onClick={() => void enroll()}
              >
                Confirmar inscripción
              </button>
            </div>
          )}
        </>
      )}
      {error && <p role="alert">{error}</p>}
    </section>
  );
}
