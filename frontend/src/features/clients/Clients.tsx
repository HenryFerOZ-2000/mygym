import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api, ApiError } from "../../shared/api/client";
import { queryClient } from "../../app/query-client";
import { useWorkspaces } from "../workspaces/use-workspaces";
import { LogoutButton } from "../../shared/ui/LogoutButton";
import { ClientForm } from "./ClientForm";
import type { User } from "../auth/use-session";
import type { ClientPage, ClientRecord } from "./types";
import { operationAccess } from "../gym/access";

export function Clients({ user }: { user: User }) {
  const { workspaceId = "" } = useParams();
  const [page, setPage] = useState(1);
  const [form, setForm] = useState<ClientRecord | "new" | null>(null);
  const [notice, setNotice] = useState("");
  const workspaces = useWorkspaces(user.id);
  const workspace = workspaces.data?.find((w) => w.id === workspaceId);
  const operations = operationAccess(workspace);
  const query = useQuery({
    queryKey: [user.id, workspaceId, "clients", page],
    queryFn: ({ signal }) =>
      api<ClientPage>(`workspaces/${workspaceId}/clients/?page=${page}`, {
        signal,
      }),
  });
  const denied =
    query.error instanceof ApiError && [403, 404].includes(query.error.status);
  const canManage =
    workspace &&
    workspace.role !== "COACH" &&
    workspace.capabilities.includes("clients.manage") &&
    !denied;
  return (
    <div className="app-layout">
      <aside className="sidebar">
        <Link className="brand" to="/workspaces">
          mygym<span className="brand-dot">●</span>
        </Link>
        <div className="workspace-label">
          <span className="eyebrow light">ESPACIO ACTIVO</span>
          <strong>{workspace?.name ?? "Validando acceso…"}</strong>
          <Link to="/workspaces">
            Cambiar espacio <span aria-hidden="true">↗</span>
          </Link>
        </div>
        <nav aria-label="Principal">
          <span className="eyebrow light">TU NEGOCIO</span>
          <Link
            className="nav-active"
            to={`/workspaces/${workspaceId}/clients`}
            aria-current="page"
          >
            <span aria-hidden="true">◎</span> Clientes
          </Link>
          {workspace?.kind === "GYM" &&
            workspace.capabilities.includes("gym.manage") &&
            workspace.role !== "COACH" && (
              <Link to={`/workspaces/${workspaceId}/plans`}>
                Planes y promociones
              </Link>
            )}
        </nav>
        <nav aria-label="Operaciones">
          {operations.attendance && (
            <Link to={`/workspaces/${workspaceId}/attendance`}>Asistencia</Link>
          )}
          {(operations.expiries ||
            operations.attendanceReport ||
            operations.financialReport) && (
            <Link to={`/workspaces/${workspaceId}/reports`}>
              Vencimientos y reportes
            </Link>
          )}
        </nav>
        <div className="sidebar-bottom">
          <span className="user-avatar" aria-hidden="true">
            {user.username.slice(0, 1).toUpperCase()}
          </span>
          <div>
            <strong>{user.username}</strong>
            <LogoutButton />
          </div>
        </div>
      </aside>
      <main className="clients-main">
        <header className="topbar">
          <span>
            Tu negocio <span className="separator">/</span>{" "}
            <strong>Clientes</strong>
          </span>
          <span className="topbar-workspace">{workspace?.name}</span>
        </header>
        <section className="clients-content">
          <div className="page-heading">
            <div>
              <span className="eyebrow">PERSONAS QUE MUEVEN TU NEGOCIO</span>
              <h1>Tu comunidad</h1>
              <p className="muted">
                Cada persona cuenta. Sus datos, siempre a mano.
              </p>
            </div>
            {canManage && (
              <button
                className="button primary"
                onClick={() => {
                  setNotice("");
                  setForm("new");
                }}
              >
                <span aria-hidden="true">＋</span> Nuevo cliente
              </button>
            )}
          </div>
          {notice && (
            <p className="success-note" role="status">
              ✓ {notice}
            </p>
          )}
          <section className="clients-card" aria-label="Listado de clientes">
            <div className="card-heading">
              <div>
                <h2>
                  Clientes{" "}
                  <span className="count">
                    {!query.isError ? (query.data?.count ?? "—") : "—"}
                  </span>
                </h2>
                <p className="muted">
                  Fichas de {workspace?.name ?? "este espacio"}
                </p>
              </div>
              <span className="small-note">25 por página</span>
            </div>
            {query.isPending && (
              <div className="empty" role="status">
                Cargando clientes…
              </div>
            )}
            {query.isError && (
              <div className="empty" role="alert">
                <h2>
                  {denied
                    ? "Acceso no disponible"
                    : "No pudimos cargar las fichas"}
                </h2>
                <p>
                  {denied
                    ? "Tu acceso o los permisos de este espacio no permiten esta acción."
                    : "Comprueba la conexión e intenta de nuevo."}
                </p>
                {denied ? (
                  <Link to="/workspaces" className="button secondary">
                    Volver a mis espacios
                  </Link>
                ) : (
                  <button
                    className="button secondary"
                    onClick={() => void query.refetch()}
                  >
                    Reintentar
                  </button>
                )}
              </div>
            )}
            {!query.isError &&
              query.data &&
              (query.data.results.length ? (
                <div className="table-scroll">
                  <table>
                    <thead>
                      <tr>
                        <th>CLIENTE</th>
                        <th>CONTACTO</th>
                        <th>ESTADO</th>
                        <th>
                          <span className="sr-only">Acciones</span>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {query.data.results.map((record) => (
                        <tr key={record.id}>
                          <td>
                            <div className="person">
                              <span
                                className="person-avatar"
                                aria-hidden="true"
                              >
                                {record.full_name
                                  .split(" ")
                                  .map((s) => s[0])
                                  .slice(0, 2)
                                  .join("")
                                  .toUpperCase()}
                              </span>
                              <strong>{record.full_name}</strong>
                            </div>
                          </td>
                          <td>
                            <div className="contact">
                              {record.email && <span>{record.email}</span>}
                              {record.phone && <span>{record.phone}</span>}
                              {!record.email && !record.phone && (
                                <span className="muted">
                                  Sin contacto registrado
                                </span>
                              )}
                            </div>
                          </td>
                          <td>
                            <span
                              className={`badge ${record.is_active ? "active" : ""}`}
                            >
                              <span aria-hidden="true">●</span>{" "}
                              {record.is_active ? "Activo" : "Inactivo"}
                            </span>
                          </td>
                          <td>
                            {canManage && (
                              <button
                                className="edit-button"
                                aria-label={`Editar ${record.full_name}`}
                                onClick={() => {
                                  setNotice("");
                                  setForm(record);
                                }}
                              >
                                Editar <span aria-hidden="true">↗</span>
                              </button>
                            )}
                            {canManage &&
                              (workspace.capabilities.includes("gym.manage") ||
                                workspace.capabilities.includes(
                                  "receivables.manage",
                                )) && (
                                <Link
                                  className="edit-button"
                                  aria-label={`Membresías de ${record.full_name}`}
                                  to={`/workspaces/${workspaceId}/clients/${record.id}/account`}
                                >
                                  Membresías y cobros
                                </Link>
                              )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="empty">
                  <div className="empty-symbol" aria-hidden="true">
                    ◎
                  </div>
                  <h2>Aquí empieza tu comunidad</h2>
                  <p>
                    Crea la primera ficha de este negocio.
                    <br />
                    Solo necesitas el nombre de la persona.
                  </p>
                  {canManage && (
                    <button
                      className="button secondary"
                      onClick={() => setForm("new")}
                    >
                      Crear primera ficha
                    </button>
                  )}
                </div>
              ))}
            {!query.isError && query.data && query.data.count > 25 && (
              <div className="pagination">
                <span>
                  Página {page} de {Math.ceil(query.data.count / 25)}
                </span>
                <div>
                  <button
                    className="button secondary"
                    disabled={page === 1}
                    onClick={() => setPage((p) => p - 1)}
                  >
                    Anterior
                  </button>
                  <button
                    className="button secondary"
                    disabled={!query.data.next}
                    onClick={() => setPage((p) => p + 1)}
                  >
                    Siguiente
                  </button>
                </div>
              </div>
            )}
          </section>
          <p className="privacy-note">
            <span aria-hidden="true">◈</span> Las fichas pertenecen únicamente a
            este negocio.
          </p>
        </section>
      </main>
      {form && canManage && (
        <ClientForm
          key={form === "new" ? "new" : form.id}
          workspaceId={workspaceId}
          record={form === "new" ? undefined : form}
          onClose={() => setForm(null)}
          onSaved={async () => {
            setForm(null);
            setNotice("Ficha guardada correctamente.");
            await queryClient.invalidateQueries({
              queryKey: [user.id, workspaceId, "clients"],
            });
            const refreshed = queryClient.getQueryData<ClientPage>([
              user.id,
              workspaceId,
              "clients",
              page,
            ]);
            if (form === "new" && refreshed)
              setPage(Math.max(1, Math.ceil(refreshed.count / 25)));
          }}
        />
      )}
    </div>
  );
}
