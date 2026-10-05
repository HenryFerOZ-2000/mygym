import type { Charge, Membership, Payment } from "./types";
import { OperationDialog } from "./ui";
import { displayDate, shiftDate } from "./format";

export type Action =
  | { kind: "pay"; charge: Charge }
  | { kind: "refund"; payment: Payment }
  | { kind: "freeze" | "correct" | "cancel"; membership: Membership };
export function AccountDialog({
  action,
  base,
  onClose,
  onSaved,
}: {
  action: Action;
  base: string;
  onClose: () => void;
  onSaved: () => Promise<void>;
}) {
  if (action.kind === "pay") {
    const charge = action.charge;
    return (
      <OperationDialog
        title="Registrar abono"
        submitLabel="Confirmar cobro"
        onClose={onClose}
        onSubmit={async (form, send) => {
          await send(base + "receivables/payments/", {
            amount: form.get("amount"),
            currency: charge.currency,
            method: form.get("method"),
            allocations: [{ charge_id: charge.id, amount: form.get("amount") }],
          });
          await onSaved();
        }}
      >
        <p>
          {charge.label} · Pendiente: {charge.currency} {charge.balance}
        </p>
        <p>Registra únicamente dinero que ya recibiste.</p>
        <label>
          Importe a cobrar
          <input
            type="number"
            name="amount"
            required
            min="0.01"
            max={charge.balance}
            step="0.01"
            defaultValue={charge.balance}
          />
        </label>
        <label>
          Método
          <select name="method">
            <option value="CASH">Efectivo</option>
            <option value="TRANSFER">Transferencia</option>
          </select>
        </label>
      </OperationDialog>
    );
  }
  if (action.kind === "refund") {
    const payment = action.payment;
    return (
      <OperationDialog
        title="Registrar devolución"
        submitLabel="Confirmar devolución"
        onClose={onClose}
        onSubmit={async (form, send) => {
          await send(base + `receivables/payments/${payment.id}/refunds/`, {
            reason: form.get("reason"),
            allocations: [
              { charge_id: form.get("charge"), amount: form.get("amount") },
            ],
          });
          await onSaved();
        }}
      >
        <p>
          Este registro no transfiere dinero. La devolución vuelve a aumentar el
          saldo pendiente del cargo y no cancela la membresía.
        </p>
        <label>
          Aplicación del pago
          <select name="charge">
            {payment.allocations
              .filter((a) => Number(a.refundable) > 0)
              .map((a, index) => (
                <option value={a.charge_id} key={a.charge_id}>
                  Cargo {index + 1}: disponible {payment.currency}{" "}
                  {a.refundable}
                </option>
              ))}
          </select>
        </label>
        <label>
          Importe a devolver
          <input type="number" name="amount" min="0.01" step="0.01" required />
        </label>
        <label>
          Motivo
          <textarea name="reason" maxLength={300} required />
        </label>
        <label className="gym-check">
          <input type="checkbox" required />
          Confirmo que devolví el dinero fuera de MyGym
        </label>
      </OperationDialog>
    );
  }
  const membership = action.membership;
  const title =
    action.kind === "freeze"
      ? "Congelar membresía"
      : action.kind === "cancel"
        ? "Cancelar membresía"
        : "Corregir fechas";
  return (
    <OperationDialog
      title={title}
      submitLabel={`Confirmar ${action.kind === "freeze" ? "congelación" : action.kind === "cancel" ? "cancelación" : "corrección"}`}
      onClose={onClose}
      onSubmit={async (form, send) => {
        const fields =
          action.kind === "cancel"
            ? { effective_date: form.get("effective_date") }
            : {
                start_date: form.get("start_date"),
                end_date: shiftDate(String(form.get("last_day")), 1),
              };
        await send(base + `gym/memberships/${membership.id}/${action.kind}/`, {
          reason: form.get("reason"),
          ...fields,
        });
        await onSaved();
      }}
    >
      <p>
        {membership.name}: {displayDate(membership.start_date)} —{" "}
        {displayDate(membership.last_day)}
      </p>
      <p>
        {action.kind === "freeze"
          ? "Se suspende el servicio durante estos días. Se extiende la vigencia y se desplazan las renovaciones futuras por la misma cantidad de días."
          : action.kind === "cancel"
            ? "El servicio termina al comenzar la fecha indicada. No se devuelve dinero ni se elimina deuda. Las renovaciones futuras se conservan."
            : "Se conservan las fechas anteriores en el historial. El cargo y los pagos no cambian."}
      </p>
      {action.kind === "cancel" ? (
        <label>
          Fecha efectiva de cancelación
          <input name="effective_date" type="date" required />
        </label>
      ) : (
        <>
          <label>
            Primer día
            <input
              name="start_date"
              type="date"
              required
              defaultValue={
                action.kind === "correct" ? membership.start_date : ""
              }
            />
          </label>
          <label>
            Último día incluido
            <input
              name="last_day"
              type="date"
              required
              defaultValue={
                action.kind === "correct" ? (membership.last_day ?? "") : ""
              }
            />
          </label>
        </>
      )}
      <label>
        Motivo
        <textarea name="reason" maxLength={300} required />
      </label>
    </OperationDialog>
  );
}
