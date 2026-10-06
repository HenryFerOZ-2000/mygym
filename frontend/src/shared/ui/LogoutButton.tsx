import { useState } from "react";
import { endSession } from "../../features/auth/logout";

export function LogoutButton() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);
  return (
    <div>
      <button
        className="text-button"
        disabled={busy}
        aria-busy={busy}
        onClick={async () => {
          setBusy(true);
          setError(false);
          try {
            await endSession();
          } catch {
            setError(true);
          } finally {
            setBusy(false);
          }
        }}
      >
        {busy ? "Cerrando…" : "Cerrar sesión"}
      </button>
      {error && <p role="alert">No se pudo cerrar la sesión. Reintenta.</p>}
    </div>
  );
}
