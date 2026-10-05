import { useState } from "react";
import { Navigate } from "react-router-dom";
import { api, ApiError } from "../../shared/api/client";
import { queryClient } from "../../app/query-client";
import { announceLogin, clearPrivateData, reconcileIdentity } from "./session";
import { useSession, type User } from "./use-session";

export function Login() {
  const session = useSession();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  if (session.data) return <Navigate to="/workspaces" replace />;
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setBusy(true);
    setError("");
    try {
      const user = await api<User>("auth/login/", {
        method: "POST",
        body: JSON.stringify({
          username: data.get("username"),
          password: data.get("password"),
        }),
      });
      await queryClient.cancelQueries();
      clearPrivateData(false);
      reconcileIdentity(user.id);
      queryClient.setQueryData(["me"], user);
      announceLogin();
    } catch (e) {
      setError(
        e instanceof ApiError
          ? e.message
          : "No pudimos conectar. Revisa que el servidor esté encendido.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="login-page">
      <section className="login-story">
        <a className="brand" href="/">
          mygym<span className="brand-dot">●</span>
        </a>
        <div>
          <span className="eyebrow light">MENOS GESTIÓN. MÁS PERSONAS.</span>
          <h1>
            Tu gimnasio,
            <br />
            en orden.
          </h1>
          <p>
            Un espacio para cuidar lo que más importa:
            <br />
            tu comunidad.
          </p>
        </div>
        <div className="story-footer">
          <span className="orbit" aria-hidden="true">
            ↗
          </span>
          <span>
            El siguiente paso
            <br />
            <strong>empieza aquí.</strong>
          </span>
        </div>
      </section>
      <section className="login-panel">
        <div className="login-card">
          <span className="eyebrow">BIENVENIDO A MYGYM</span>
          <h2>Qué bueno verte.</h2>
          <p className="muted">
            Entra con tu cuenta para gestionar tu negocio.
          </p>
          <form onSubmit={submit}>
            <label htmlFor="username">Usuario</label>
            <input
              id="username"
              name="username"
              autoComplete="username"
              required
              maxLength={150}
              autoFocus
              placeholder="Tu usuario"
            />
            <label htmlFor="password">Contraseña</label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              maxLength={128}
              placeholder="Tu contraseña"
            />
            {error && (
              <div role="alert" className="error-box">
                {error}
              </div>
            )}
            <button className="button primary full" disabled={busy}>
              {busy ? "Entrando…" : "Entrar"} <span aria-hidden="true">↗</span>
            </button>
          </form>
          <p className="login-note">
            Acceso privado para el equipo de tu negocio.
          </p>
        </div>
        <footer>
          MYGYM <span>Tu comunidad. Tu espacio.</span>
        </footer>
      </section>
    </main>
  );
}
