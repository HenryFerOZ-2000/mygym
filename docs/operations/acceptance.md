# Matriz de aceptación del hito 1

Sólo datos ficticios. PostgreSQL 17.11 real; pruebas de aplicación con mygym_runtime restringido.

Última evidencia: 47 pruebas backend, 5 Vitest y 6 Playwright aprobadas; lint, tipos,
build, esquema OpenAPI y privilegios aprobados. Capturas desktop/móvil revisadas visualmente.

| Criterio del contexto | Evidencia |
| --- | --- |
| 1. Login, error genérico, intentos, CSRF, logout | test_auth.py, test_login_limits.py y E2E sesión expirada |
| 2. Descubrimiento autorizado | test_workspace_access.py |
| 3. OWNER/RECEPTION y COACH denegado | test_workspace_access.py y E2E cambio a coach |
| 4. Revocación siguiente petición | test_revocation_and_capability_change_apply_next_request |
| 5. A no opera fichas B | test_clients_api.py y test_rls.py, SQL sin filtros |
| 6. Inyección de workspace/user/role | Parametrización POST/PATCH de test_clients_api.py |
| 7. Sin correo y correo repetido | test_create_edit_and_deactivate_without_contact, test_same_email_does_not_merge_or_link |
| 8. Auditoría atómica sin valores | test_client_audit.py, fallo inyectado al límite de escritura |
| 9. RLS runtime/contexto/reuso | test_rls.py, test_rls_transactions.py y verify_role_guard.py |
| 10. Dos pestañas/contextos | Playwright: alta en Titan ausente en Aurora, logout coordinado |
| 11. API real/tipos/lint/build | Playwright contra backend vivo + comandos npm |
| 12. Demo idempotente | test_demo.py preserva contraseña, cambios y recuentos |
| 13. Reproducibilidad/PowerShell | requirements.lock, package-lock.json, npm ci, scripts y guía |
| 14. Sin servicios remotos MyGym | Backend/DB/UI locales, sin correo/CDN/auth externa; bootstrap sí descarga dependencias |

Revisión independiente estática y regresiones de sus hallazgos completadas. No certifica producción.
No se ha validado el futuro instalador comercial, otra computadora, LAN/HTTPS, respaldo/restauración,
carga productiva, MFA ni normativa. No se usan datos reales, fotos ni facturación.
Los tests de login mantienen hashing real. Los de RLS no usan credenciales privilegiadas para demostrar aislamiento.
Pruebas de SQL commit/rollback adicionales abren conexiones runtime y no escriben datos de negocio persistentes.

## Continuación Gym y asistencia — 2026-10-02

Verificación completa actual: `scripts/verify.ps1 -Browser` terminó con exit 0; **76 backend + 7 Vitest + 14 Playwright = 97 pruebas**, sin omisiones. Ruff, ESLint, tipos/build, OpenAPI validado, migraciones y guardia runtime aprobados.

| Criterio nuevo | Evidencia |
| --- | --- |
| Entrada vigente con deuda y excepción exclusiva OWNER | test_attendance.py |
| Congelada/inactiva bloqueadas, límites locales y cancelación | test_frozen_cancelled_and_date_boundaries, test_attendance_timestamp_matches_decision_at_midnight |
| Repetición confirmada, reintento y anulación concurrentes | test_attendance_concurrency.py con conexiones runtime reales |
| Auditoría atómica e historial inmutable | test_attendance_audit_failure_rolls_back_and_runtime_cannot_overwrite y test_gym_security.py |
| Renovación contigua/brecha y cliente renovado no vencido | test_operational_reports.py |
| Monedas, aplicaciones/devoluciones y saldo actual | test_financial_report_currencies_allocations_refunds_and_current_balance |
| Devolución de pago anterior y saldo de ficha inactiva | test_refund_period_follows_refund_date_and_debt_includes_inactive |
| Capacidades de reportes independientes y recepción denegada | test_report_permissions_and_independent_capabilities |
| Respuesta perdida tras commit y cambio de pestaña | Playwright attendance.spec.ts: misma request_id y una sola entrada |
| Entrada/repetición/anulación/reportes, revocación y fechas vencidas | Playwright attendance.spec.ts, capturas desktop/móvil |

Revisión independiente y regresiones completadas. La mejora de fecha de término en el diálogo de entrada fue incorporada en la continuación de calidad. Las pruebas concurrentes Gym/asistencia conservan historial ficticio en workspaces exclusivos desactivados; no usan permisos de migración para borrarlo.

## Continuación de calidad — 2026-10-02

Evidencia más reciente: `scripts/verify.ps1 -Browser` exit 0, **77 backend + 7 Vitest + 18 Playwright = 102 pruebas**. Fechas de asistencia respetan cancelación y acceso mínimo, anulaciones muestran actor/instante, menús y destino del negocio respetan capacidades, y búsqueda/historial/vencimientos permiten reintentar consultas. Regresiones RED→GREEN en test_attendance.py y navigation.spec.ts; revisión independiente sin hallazgos pendientes. Captura del diálogo a 390px inspeccionada. Demo local reiniciada correctamente.
