# Especificación aprobada: núcleo

Fuente: docs/PROJECT_CONTEXT.md y aprobación del diagnóstico/plan en conversación.
Login -> workspaces autorizados -> listado/alta/edición de clientes -> logout.
User AbstractUser con username, email opcional; Workspace UUID/name/kind/timezone/is_active;
WorkspaceAccess único user/workspace con OWNER/RECEPTION/COACH; WorkspaceCapability único workspace/code.
ClientRecord UUID/workspace/user opcional/full_name/phone/email/is_active/created_at/updated_at.
AuditEvent workspace/actor/action/object_id/created_at/changed_fields (nombres, nunca valores).
OWNER y RECEPTION gestionan con clients.manage activo. COACH denegado. Revocación efectiva en siguiente petición.
Formulario sólo full_name (200), phone (32), email (254), is_active. Nombre no vacío, contactos opcionales.
Campos desconocidos/prohibidos rechazados. No DELETE. Paginación 25, máximo 100, orden created_at/id.
Rutas /api/v1/: health/, auth/csrf/, auth/login/, auth/logout/, auth/me/, me/workspaces/,
workspaces/{workspace_id}/clients/ y workspaces/{workspace_id}/clients/{client_id}/.
GET en consultas, POST login/logout/alta, PATCH edición. JSON y barra final.
400 validación/credenciales; 403 sesión/CSRF/permiso; 404 workspace ajeno/inexistente o ficha fuera de contexto.
Errores error.code/message/fields. Health mínimo. OpenAPI versionado.
Limitador login persistente por cuenta normalizada y origen, claves HMAC sin username/IP en claro:
5 intentos por cuenta y 30 por origen en 15 minutos, configurables. Respuesta 400 genérica.
Cookies HttpOnly/same-site; Secure salvo desarrollo loopback. Sin CORS universal.
Ficha + auditoría transaccionales. RLS USING/WITH CHECK, sin contexto deniega, runtime sin bypass/propiedad.
Sin contexto residual tras commit/rollback/reuso; anidamiento entre negocios prohibido.
UI española responsive/accesible, carga/vacío/error, contexto visible. Caché usuario/workspace y logout entre pestañas.
Demo dos gimnasios, identidad común y roles de prueba, idempotente no destructiva, sin claves fijas.
Aceptación: los 14 criterios de sección 21 del contexto, contra PostgreSQL real.
