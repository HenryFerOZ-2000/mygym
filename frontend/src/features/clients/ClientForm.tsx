import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "../../shared/api/client";
import { validateClient } from "./validation";
import type { ClientRecord } from "./types";

export function ClientForm({
  workspaceId,
  record,
  onClose,
  onSaved,
}: {
  workspaceId: string;
  record?: ClientRecord;
  onClose: () => void;
  onSaved: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    const node = dialog.current;
    node?.showModal();
    return () => node?.close();
  }, []);
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const data = {
      full_name: String(form.get("full_name")).trim(),
      phone: String(form.get("phone")).trim(),
      email: String(form.get("email")).trim(),
      is_active: form.get("is_active") === "on",
    };
    const validation = validateClient(data);
    setErrors(validation);
    setError("");
    if (Object.keys(validation).length) return;
    setBusy(true);
    try {
      await api(
        `workspaces/${workspaceId}/clients/${record ? record.id + "/" : ""}`,
        { method: record ? "PATCH" : "POST", body: JSON.stringify(data) },
      );
      onSaved();
    } catch (e) {
      if (e instanceof ApiError) {
        setError(e.message);
        setErrors(
          Object.fromEntries(
            Object.entries(e.fields).map(([k, v]) => [
              k,
              Array.isArray(v) ? v.join(" ") : String(v),
            ]),
          ),
        );
      } else
        setError("No pudimos guardar. Revisa la conexión e intenta otra vez.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <dialog
      ref={dialog}
      className="client-dialog"
      onCancel={(e) => {
        if (busy) e.preventDefault();
        else onClose();
      }}
      aria-labelledby="form-title"
    >
      <div className="dialog-heading">
        <div>
          <span className="eyebrow">FICHA DE CLIENTE</span>
          <h2 id="form-title">
            {record ? "Editar cliente" : "Una nueva persona"}
          </h2>
        </div>
        <button
          className="icon-button"
          disabled={busy}
          aria-label="Cerrar formulario"
          onClick={onClose}
        >
          ×
        </button>
      </div>
      <p className="muted">
        Lo esencial para mantener el contacto con tu comunidad.
      </p>
      <form onSubmit={submit} noValidate>
        {[
          ["full_name", "Nombre completo", 200],
          ["phone", "Teléfono", 32],
          ["email", "Correo electrónico", 254],
        ].map(([key, label, max]) => (
          <div key={key}>
            <label htmlFor={String(key)}>
              {label}{" "}
              {key !== "full_name" && (
                <span className="optional">opcional</span>
              )}
            </label>
            <input
              id={String(key)}
              name={String(key)}
              type={
                key === "email" ? "email" : key === "phone" ? "tel" : "text"
              }
              maxLength={Number(max)}
              defaultValue={
                record?.[key as "full_name" | "phone" | "email"] ?? ""
              }
              required={key === "full_name"}
              autoFocus={key === "full_name"}
              aria-invalid={!!errors[key]}
              aria-describedby={errors[key] ? `${key}-error` : undefined}
            />
            {errors[key] && (
              <p id={`${key}-error`} className="field-error">
                {errors[key]}
              </p>
            )}
          </div>
        ))}
        <label className="checkbox">
          <input
            type="checkbox"
            name="is_active"
            defaultChecked={record?.is_active ?? true}
          />{" "}
          Cliente activo
        </label>
        {error && (
          <div className="error-box" role="alert">
            {error}
          </div>
        )}
        <div className="dialog-actions">
          <button
            type="button"
            className="button secondary"
            disabled={busy}
            onClick={onClose}
          >
            Cancelar
          </button>
          <button className="button primary" disabled={busy} aria-busy={busy}>
            {busy
              ? "Guardando…"
              : record
                ? "Guardar cambios"
                : "Guardar cliente"}
          </button>
        </div>
      </form>
    </dialog>
  );
}
