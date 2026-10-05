import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../shared/api/client";
import { queryClient } from "../../app/query-client";
import { useWorkspaces } from "../workspaces/use-workspaces";
import type { User } from "../auth/use-session";
import type { ClientRecord } from "../clients/types";
import type { Page, Membership, Charge, Payment } from "./types";
import { Enrollment } from "./Enrollment";
import { AccountDialog, type Action } from "./AccountDialogs";
import { GymLayout, Pager } from "./ui";
import { displayDate, message } from "./format";

const status: Record<string, string> = {
  ACTIVE: "Vigente",
  FUTURE: "Programada",
  FROZEN: "Congelada",
  EXPIRED: "Vencida",
  CANCELLED: "Cancelada",
  CLIENT_INACTIVE: "Cliente inactivo",
};
export function Account({ user }: { user: User }) {
  const { workspaceId = "", clientId = "" } = useParams();
  const spaces = useWorkspaces(user.id);
  const workspace = spaces.data?.find((w) => w.id === workspaceId);
  const administrative =
    !!workspace && ["OWNER", "RECEPTION"].includes(workspace.role);
  const canGym =
    administrative &&
    workspace.capabilities.includes("gym.manage") &&
    workspace.kind === "GYM";
  const canMoney =
    administrative && workspace.capabilities.includes("receivables.manage");
  const canClient =
    administrative && workspace.capabilities.includes("clients.manage");
  const [memberPage, setMemberPage] = useState(1);
  const [chargePage, setChargePage] = useState(1);
  const [paymentPage, setPaymentPage] = useState(1);
  const [action, setAction] = useState<Action | null>(null);
  const [notice, setNotice] = useState("");
  const base = `workspaces/${workspaceId}/clients/${clientId}/`;
  const key = [user.id, workspaceId, clientId];
  const client = useQuery({
    enabled: canClient,
    queryKey: [...key, "client"],
    queryFn: ({ signal }) => api<ClientRecord>(base, { signal }),
  });
  const members = useQuery({
    enabled: canGym,
    queryKey: [...key, "memberships", memberPage],
    queryFn: ({ signal }) =>
      api<Page<Membership>>(base + `gym/?page=${memberPage}`, { signal }),
  });
  const charges = useQuery({
    enabled: canMoney,
    queryKey: [...key, "charges", chargePage],
    queryFn: ({ signal }) =>
      api<Page<Charge>>(base + `receivables/?page=${chargePage}`, { signal }),
  });
  const payments = useQuery({
    enabled: canMoney,
    queryKey: [...key, "payments", paymentPage],
    queryFn: ({ signal }) =>
      api<Page<Payment>>(base + `receivables/payments/?page=${paymentPage}`, {
        signal,
      }),
  });
  const queries = [
    spaces,
    ...(canClient ? [client] : []),
    ...(canGym ? [members] : []),
    ...(canMoney ? [charges, payments] : []),
  ];
  const failure = queries.find((q) => q.isError);
  const loading = queries.some((q) => q.isPending);
  const canOperate = !failure && !loading;
  const owner = administrative && workspace.role === "OWNER";
  async function saved() {
    setNotice("Operación registrada correctamente.");
    await queryClient.invalidateQueries({ queryKey: key });
  }
  return (
    <GymLayout
      workspace={workspace}
      title={
        failure
          ? "Cuenta no disponible"
          : (client.data?.full_name ?? "Cuenta del cliente")
      }
    >
      <p className="muted">
        Membresías, cargos y movimientos de este gimnasio.
      </p>
      {!spaces.isPending && !canGym && !canMoney ? (
        <p role="alert">No tienes acceso a los módulos de esta cuenta.</p>
      ) : failure ? (
        <p role="alert">{message(failure.error)}</p>
      ) : loading ? (
        <p role="status">Cargando cuenta…</p>
      ) : (
        <>
          {notice && (
            <p role="status" className="success-note">
              {notice}
            </p>
          )}
          {canOperate &&
            canGym &&
            canMoney &&
            (!canClient || client.data?.is_active) && (
              <Enrollment
                userId={user.id}
                workspaceId={workspaceId}
                clientId={clientId}
                zone={workspace!.timezone}
                onSaved={() => setNotice("Inscripción y cargo registrados.")}
              />
            )}
          {canGym && (
            <section className="gym-section">
              <h2>Membresías</h2>
              {!members.data?.count && <p>No hay membresías registradas.</p>}
              <div className="gym-grid">
                {members.data?.results.map((m) => (
                  <article className="gym-card" key={m.id}>
                    <span className="badge">{status[m.status]}</span>
                    <h3>{m.name}</h3>
                    <p>
                      {displayDate(m.start_date)} — {displayDate(m.last_day)}
                    </p>
                    <p>{m.remaining_days} días de servicio restantes</p>
                    <p>
                      Contratado: {m.currency} {m.amount} · versión {m.version}
                    </p>
                    {m.cancelled_on && (
                      <p>Cancelación efectiva: {displayDate(m.cancelled_on)}</p>
                    )}
                    {m.freezes.map((f, i) => (
                      <p key={i}>
                        Pausa desde {displayDate(f.start_date)} hasta antes del{" "}
                        {displayDate(f.end_date)}
                      </p>
                    ))}
                    {owner && !m.cancelled_on && (
                      <div className="gym-actions">
                        <button
                          className="button secondary"
                          onClick={() =>
                            setAction({ kind: "freeze", membership: m })
                          }
                        >
                          Congelar
                        </button>
                        <button
                          className="button secondary"
                          onClick={() =>
                            setAction({ kind: "correct", membership: m })
                          }
                        >
                          Corregir fechas
                        </button>
                        <button
                          className="button secondary"
                          onClick={() =>
                            setAction({ kind: "cancel", membership: m })
                          }
                        >
                          Cancelar membresía
                        </button>
                      </div>
                    )}
                    {m.changes.length > 0 && (
                      <details>
                        <summary>
                          Historial de cambios ({m.changes.length})
                        </summary>
                        {m.changes.map((c, i) => (
                          <div className="gym-history" key={i}>
                            <strong>
                              {c.kind === "SHIFT"
                                ? "Desplazamiento por congelación"
                                : c.kind === "FREEZE"
                                  ? "Congelación"
                                  : c.kind === "CANCEL"
                                    ? "Cancelación"
                                    : "Corrección"}
                            </strong>
                            <p>{c.reason}</p>
                            <p>
                              Antes: {displayDate(c.before.start_date)} →{" "}
                              {displayDate(c.before.end_date)} (fin exclusivo)
                            </p>
                            <p>
                              Después: {displayDate(c.after.start_date)} →{" "}
                              {displayDate(c.after.end_date)} (fin exclusivo)
                            </p>
                          </div>
                        ))}
                      </details>
                    )}
                  </article>
                ))}
              </div>
              {members.data && (
                <Pager
                  number={memberPage}
                  next={members.data.next}
                  set={setMemberPage}
                />
              )}
            </section>
          )}
          {canMoney && (
            <section className="gym-section">
              <h2>Cargos y saldos</h2>
              <p>El saldo pendiente no modifica automáticamente la vigencia.</p>
              <div className="gym-grid">
                {charges.data?.results.map((c) => (
                  <article className="gym-card" key={c.id}>
                    <h3>{c.label}</h3>
                    <p>
                      Importe: {c.currency} {c.amount}
                    </p>
                    <strong>
                      Saldo: {c.currency} {c.balance}
                    </strong>
                    {canOperate && Number(c.balance) > 0 && (
                      <button
                        className="button primary"
                        onClick={() => setAction({ kind: "pay", charge: c })}
                      >
                        Registrar abono
                      </button>
                    )}
                  </article>
                ))}
              </div>
              {charges.data && (
                <Pager
                  number={chargePage}
                  next={charges.data.next}
                  set={setChargePage}
                />
              )}
            </section>
          )}
          {canMoney && (
            <section className="gym-section">
              <h2>Historial de pagos</h2>
              {!payments.data?.count && <p>No hay pagos registrados.</p>}
              <div className="gym-grid">
                {payments.data?.results.map((p) => (
                  <article className="gym-card" key={p.id}>
                    <h3>
                      {p.currency} {p.amount}
                    </h3>
                    <p>
                      {p.method === "CASH" ? "Efectivo" : "Transferencia"} ·{" "}
                      {new Date(p.created_at).toLocaleString("es-EC", {
                        timeZone: workspace?.timezone,
                      })}
                    </p>
                    {p.refunds.map((r) => (
                      <p key={r.id}>
                        Devolución: {p.currency} {r.amount} · {r.reason}
                      </p>
                    ))}
                    {owner &&
                      p.allocations.some((a) => Number(a.refundable) > 0) && (
                        <button
                          className="button secondary"
                          onClick={() =>
                            setAction({ kind: "refund", payment: p })
                          }
                        >
                          Registrar devolución
                        </button>
                      )}
                  </article>
                ))}
              </div>
              {payments.data && (
                <Pager
                  number={paymentPage}
                  next={payments.data.next}
                  set={setPaymentPage}
                />
              )}
            </section>
          )}
        </>
      )}
      {action &&
        canOperate &&
        (action.kind === "pay" || action.kind === "refund"
          ? canMoney
          : canGym) &&
        (action.kind === "pay" || owner) && (
          <AccountDialog
            action={action}
            base={base}
            onClose={() => setAction(null)}
            onSaved={saved}
          />
        )}
    </GymLayout>
  );
}
