import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { Login } from "../features/auth/Login";
import { useSession } from "../features/auth/use-session";
import { WorkspacePicker } from "../features/workspaces/WorkspacePicker";
import { Clients } from "../features/clients/Clients";
import { Plans } from "../features/gym/Plans";
import { Account } from "../features/gym/Account";
import { Attendance } from "../features/gym/Attendance";
import { Reports } from "../features/gym/Reports";

export function AppRouter() {
  const session = useSession();
  const location = useLocation();
  if (location.pathname === "/login") return <Login />;
  if (session.isPending)
    return (
      <main className="loading-page" role="status">
        Cargando tu espacio…
      </main>
    );
  if (session.isError)
    return (
      <main className="loading-page" role="alert">
        No se pudo conectar al servidor.{" "}
        <button
          className="button secondary"
          onClick={() => void session.refetch()}
        >
          Reintentar
        </button>
      </main>
    );
  if (!session.data) return <Navigate to="/login" replace />;
  return (
    <Routes>
      <Route
        path="/workspaces/:workspaceId/attendance"
        element={
          <Attendance
            key={`${session.data.id}:${location.pathname}`}
            user={session.data}
          />
        }
      />
      <Route
        path="/workspaces/:workspaceId/reports"
        element={
          <Reports
            key={`${session.data.id}:${location.pathname}`}
            user={session.data}
          />
        }
      />
      <Route
        path="/workspaces/:workspaceId/plans"
        element={
          <Plans
            key={`${session.data.id}:${location.pathname}`}
            user={session.data}
          />
        }
      />
      <Route
        path="/workspaces/:workspaceId/clients/:clientId/account"
        element={
          <Account
            key={`${session.data.id}:${location.pathname}`}
            user={session.data}
          />
        }
      />
      <Route
        path="/workspaces"
        element={<WorkspacePicker user={session.data} />}
      />
      <Route
        path="/workspaces/:workspaceId/clients"
        element={
          <Clients
            key={`${session.data.id}:${location.pathname}`}
            user={session.data}
          />
        }
      />
      <Route path="*" element={<Navigate to="/workspaces" replace />} />
    </Routes>
  );
}
