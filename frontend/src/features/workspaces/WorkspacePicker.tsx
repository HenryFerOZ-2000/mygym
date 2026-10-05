import { Link } from "react-router-dom";
import { useWorkspaces } from "./use-workspaces";
import type { User } from "../auth/use-session";
import { LogoutButton } from "../../shared/ui/LogoutButton";
import { workspaceStart } from "../gym/access";

export function WorkspacePicker({ user }: { user: User }) {
  const workspaces = useWorkspaces(user.id);
  return (
    <div className="picker-page">
      <header className="picker-header">
        <span className="brand dark">
          mygym<span className="brand-dot">●</span>
        </span>
        <LogoutButton />
      </header>
      <main className="picker-content">
        <span className="eyebrow">HOLA, {user.username}</span>
        <h1>Elige tu espacio</h1>
        <p className="muted">
          Cada negocio tiene su propia información. ¿Dónde trabajamos hoy?
        </p>
        {workspaces.isPending && <p role="status">Cargando tus espacios…</p>}
        {workspaces.isError && (
          <div role="alert" className="error-box">
            No pudimos cargar tus espacios.{" "}
            <button onClick={() => void workspaces.refetch()}>
              Reintentar
            </button>
          </div>
        )}
        {workspaces.data?.length === 0 && (
          <div className="empty">
            <h2>Aún no tienes espacios disponibles</h2>
            <p>Un propietario debe habilitar tu acceso al negocio.</p>
          </div>
        )}
        <div className="workspace-grid">
          {workspaces.data?.map((w, index) => (
            <Link className="workspace-card" key={w.id} to={workspaceStart(w)}>
              <span
                className={`workspace-icon tone-${index % 2}`}
                aria-hidden="true"
              >
                {w.name.slice(0, 1)}
              </span>
              <span className="eyebrow">
                {w.kind === "GYM" ? "GIMNASIO" : "COACH"}
              </span>
              <h2>{w.name}</h2>
              <div className="workspace-bottom">
                <span>
                  {w.role === "OWNER"
                    ? "Propietario"
                    : w.role === "RECEPTION"
                      ? "Recepción"
                      : "Coach"}
                </span>
                <span aria-hidden="true">↗</span>
              </div>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}
