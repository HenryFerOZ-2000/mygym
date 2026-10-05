import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../shared/api/client";
import { queryClient } from "../../app/query-client";
import { useWorkspaces } from "../workspaces/use-workspaces";
import type { User } from "../auth/use-session";
import type { Page, Plan } from "./types";
import { GymLayout, OperationDialog, Pager } from "./ui";
import { displayDate, message, localDate, planAvailability } from "./format";

export function Plans({ user }: { user: User }) {
  const { workspaceId = "" } = useParams();
  const spaces = useWorkspaces(user.id);
  const workspace = spaces.data?.find((w) => w.id === workspaceId);
  const [page, setPage] = useState(1);
  const [form, setForm] = useState<Plan | "new" | null>(null);
  const base = `workspaces/${workspaceId}/gym/plans/`;
  const query = useQuery({
    queryKey: [user.id, workspaceId, "plans", page],
    queryFn: ({ signal }) =>
      api<Page<Plan>>(`${base}?page=${page}`, { signal }),
  });
  const canEdit =
    workspace?.role === "OWNER" &&
    workspace.capabilities.includes("gym.manage") &&
    !query.isError &&
    !spaces.isError;
  const record = form && form !== "new" ? form : undefined;
  return (
    <GymLayout workspace={workspace} title="Planes y promociones">
      <p className="muted">
        Diseña la oferta de tu gimnasio. Cada inscripción conserva las
        condiciones contratadas.
      </p>
      {canEdit && (
        <button className="button primary" onClick={() => setForm("new")}>
          Nuevo plan
        </button>
      )}
      {query.isPending && <p role="status">Cargando planes…</p>}
      {query.isError && <p role="alert">{message(query.error)}</p>}
      {!query.isError && query.data && (
        <>
          <div className="gym-grid">
            {query.data.results.map((plan) => (
              <article className="gym-card" key={plan.id}>
                <span className="eyebrow">
                  {plan.is_promotion ? "PROMOCIÓN" : "PLAN"} · VERSIÓN{" "}
                  {plan.version}
                </span>
                <h2>{plan.name}</h2>
                <p className="gym-price">
                  {plan.currency} {plan.amount}
                </p>
                <p>
                  {plan.quantity}{" "}
                  {plan.unit === "DAYS" ? "días" : "meses calendario"}
                </p>
                <p className="badge">
                  {planAvailability(
                    plan,
                    localDate(workspace?.timezone ?? "America/Guayaquil"),
                  )}
                </p>
                {(plan.available_from || plan.available_until) && (
                  <p>
                    Venta:{" "}
                    {plan.available_from
                      ? displayDate(plan.available_from)
                      : "sin inicio"}{" "}
                    —{" "}
                    {plan.available_until
                      ? displayDate(plan.available_until)
                      : "sin fin"}
                  </p>
                )}
                {canEdit && (
                  <button
                    className="button secondary"
                    aria-label={`Editar ${plan.name}`}
                    onClick={() => setForm(plan)}
                  >
                    Editar plan
                  </button>
                )}
              </article>
            ))}
          </div>
          {!query.data.count && (
            <p className="empty">Crea el primer plan de este gimnasio.</p>
          )}
          <Pager number={page} next={query.data.next} set={setPage} />
        </>
      )}
      {form && canEdit && (
        <OperationDialog
          title={record ? "Editar plan" : "Nuevo plan"}
          submitLabel="Guardar plan"
          onClose={() => setForm(null)}
          onSubmit={async (data, send) => {
            const payload = {
              name: data.get("name"),
              amount: data.get("amount"),
              currency: String(data.get("currency")).toUpperCase(),
              unit: data.get("unit"),
              quantity: Number(data.get("quantity")),
              is_active: data.get("is_active") === "on",
              is_promotion: data.get("is_promotion") === "on",
              available_from: data.get("available_from") || null,
              available_until: data.get("available_until") || null,
              ...(record ? { expected_version: record.version } : {}),
            };
            await send(
              base + (record ? record.id + "/" : ""),
              payload,
              record ? "PATCH" : "POST",
            );
            await queryClient.invalidateQueries({
              queryKey: [user.id, workspaceId, "plans"],
            });
            const refreshed = queryClient.getQueryData<Page<Plan>>([
              user.id,
              workspaceId,
              "plans",
              page,
            ]);
            if (!record && refreshed)
              setPage(Math.max(1, Math.ceil(refreshed.count / 25)));
          }}
        >
          <p>
            Los cambios crean una versión nueva y no alteran inscripciones
            anteriores.
          </p>
          <label>
            Nombre del plan
            <input
              name="name"
              required
              maxLength={120}
              defaultValue={record?.name}
            />
          </label>
          <div className="gym-fields">
            <label>
              Precio
              <input
                name="amount"
                type="number"
                min="0"
                step="0.01"
                required
                defaultValue={record?.amount}
              />
            </label>
            <label>
              Moneda
              <input
                name="currency"
                pattern="[A-Za-z]{3}"
                maxLength={3}
                required
                defaultValue={record?.currency ?? "USD"}
              />
            </label>
          </div>
          <div className="gym-fields">
            <label>
              Duración
              <input
                name="quantity"
                type="number"
                min="1"
                max="3650"
                required
                defaultValue={record?.quantity ?? 30}
              />
            </label>
            <label>
              Unidad
              <select name="unit" defaultValue={record?.unit ?? "DAYS"}>
                <option value="DAYS">Días</option>
                <option value="MONTHS">Meses calendario</option>
              </select>
            </label>
          </div>
          <label className="gym-check">
            <input
              name="is_active"
              type="checkbox"
              defaultChecked={record?.is_active ?? true}
            />
            Disponible para inscribir
          </label>
          <label className="gym-check">
            <input
              name="is_promotion"
              type="checkbox"
              defaultChecked={record?.is_promotion ?? false}
            />
            Es una promoción
          </label>
          <label>
            Venta desde (opcional)
            <input
              name="available_from"
              type="date"
              defaultValue={record?.available_from ?? ""}
            />
          </label>
          <label>
            Venta hasta (opcional)
            <input
              name="available_until"
              type="date"
              defaultValue={record?.available_until ?? ""}
            />
          </label>
        </OperationDialog>
      )}
    </GymLayout>
  );
}
