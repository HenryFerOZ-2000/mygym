# Core Implementation Plan

Goal: entregar el recorrido aprobado contra PostgreSQL real en Windows.
Architecture: monolito modular, autorización por petición, contexto RLS transaccional, SPA con sesiones.
Tech Stack: Python 3.13, Django 5.2 LTS, DRF, PostgreSQL 17, React, TypeScript, Vite, Query, Router, Tailwind.
Spec: ../specs/core.md. Ejecución inline con superpowers:executing-plans y TDD. Sin commits automáticos.

## Restricciones globales
No datos reales. No SQLite. No módulos fuera del hito. No cambios a otros proyectos.
No despliegues/compras/push. Dependencias aisladas, versiones exactas. Sólo loopback en desarrollo.

## Review focus
Respuesta tardía tras logout; dos pestañas y cambio de identidad; contexto SQL residual;
revocación tras login; pruebas ejecutadas con privilegios inválidos. Cubrir en tareas 2, 4, 5 y 6.

## 1. Identidad y configuración
- [x] Configuración backend/config/settings, manage.py, dependencias bloqueadas.
- [x] RED backend/tests/test_auth.py: CSRF, login/logout, me, cookies, límites, errores.
- [x] identity/models.py User y LoginAttempt; services.py/login_limits.py/api.py/urls.py.
- [x] GREEN autenticación contra PostgreSQL. Produce User y sesiones para tarea 2.

## 2. Workspaces
- [x] RED tests/test_workspace_access.py: descubrimiento, roles, estados y revocación.
- [x] workspaces/models.py/selectors.py/policies.py/api.py/urls.py y migración.
- [x] require_client_management(user, workspace_id) -> contexto validado.
- [x] GREEN descubrimiento y políticas. Depende de User; produce contexto para 3/4.

## 3. Fichas y auditoría
- [x] RED tests/test_clients_api.py y test_client_audit.py: contactos, límites, inyección, rollback.
- [x] clients/models.py/serializers.py/selectors.py/services.py/api.py y audit/models.py/services.py.
- [x] create_client(context,data), update_client(context,id,changes), record_event(...).
- [x] GREEN escritura + auditoría atómicas, paginación y controles por objeto. Depende de 2 y aceptación final de 4.

## 4. RLS
- [x] RED tests/test_rls.py: runtime, contexto ausente, cross tenant, commit/rollback/reuso/anidamiento.
- [x] tenancy/context.py/checks.py y migraciones de políticas. Scripts de roles exclusivos.
- [x] GREEN conexión runtime restringida real, sin SET ROLE al propietario. Depende de modelos 3.

## 5. Interfaz
- [x] RED Vitest (validación/caché) y Playwright (recorrido, dos pestañas, logout).
- [x] frontend/src/app, shared/api, features/auth, workspaces, clients; estilos Tailwind y componentes.
- [x] GREEN API real, accesibilidad básica, responsive, caché aislada y logout coordinado.
- [x] Tipos, lint y build. Depende de contrato 1-4.

## 6. Demo y verificación
- [x] RED tests/test_demo.py: doble ejecución, preservación de datos/claves, sólo desarrollo.
- [x] seed_demo, scripts verificables PowerShell, OpenAPI y guía de operación.
- [x] Suite PostgreSQL + frontend + E2E, revisión independiente final y correcciones.
- [x] Registrar evidencia de los 14 criterios y límites. Depende de todas las anteriores.
