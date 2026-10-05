# Gym Operations Implementation Plan

> Ejecución inline con superpowers:executing-plans y revisión independiente final. Sin commits/push.

**Goal:** planes editables, membresías y cobros manuales completos sobre PostgreSQL real.
**Architecture:** módulos gym/receivables con servicios explícitos, RLS y auditoría. La inscripción coordina vigencia y cargo atómicamente.
**Tech Stack:** stack existente Django/DRF, PostgreSQL 17, React/TypeScript.
**Spec:** ../specs/gym-operations.md

## Restricciones globales
Windows nativo, datos ficticios, aislamiento por workspace, dinero Decimal, no borrado de historial, sin dependencias nuevas ni publicación.

## Review focus
Fin de mes/año bisiesto; renovaciones concurrentes; doble clic/reintento después de respuesta perdida; devolución parcial y saldo restaurado; cambios de permisos con formularios abiertos.

## 1. Catálogo y aislamiento
Archivos: backend/modules/gym/{models,dates,serializers,services,api,urls}.py; migrations; tenancy/checks.py; scripts/migrate_local.py.
Interfaz: create_plan(context,data), revise_plan(context,id,data), period_end(start,unit,quantity).
- [x] RED tests/test_gym.py: días/meses, versiones, permisos/unknown fields, workspace ajeno.
- [x] Modelos/servicios/migraciones y permisos runtime sin UPDATE para versiones.
- [x] GREEN pytest tests/test_gym.py contra DB migrada con runtime.

## 2. Inscripciones y cargos
Archivos: gym/memberships.py; receivables/{models,services,serializers,api}.py; tests/test_memberships.py.
Interfaz: preview(context,client_id,data), enroll(context,client_id,data); create_charge(context,client,source,amount,currency).
- [x] RED fechas/instantánea/renovación/reintentos, precio versión desactualizada, cargo atómico, cliente de otro workspace.
- [x] Implementar servicios con bloqueo de cliente, huellas y paginación de historial.
- [x] GREEN pytest tests/test_memberships.py; restricciones RLS reales para todas las nuevas tablas.

## 3. Cambios y movimientos de dinero
Archivos: gym/changes.py; receivables/services.py; tests/test_gym_changes.py; tests/test_receivables.py.
Interfaz: change_membership(context,client,id,kind,data), record_payment(context,client,data), refund_payment(context,client,id,data).
- [x] RED congelar/desplazar/cancelar/corregir sin alterar dinero; pagos parciales/multicargo/reembolsos/reintentos y concurrencia.
- [x] Implementar historial inmutable y estados calculados.
- [x] GREEN suites de dominio y permisos; auditoría transaccional.

## 4. Interfaz y demo
Archivos: frontend/src/features/gym/*; router.tsx; Clients.tsx; styles.css; seed_demo.py; frontend/e2e/gym.spec.ts.
- [x] RED Playwright catálogo → edición/promoción → inscripción → abono → devolución; móvil y otro workspace.
- [x] Implementar pantallas y contratos tipados; demo idempotente conserva condiciones editadas.
- [x] GREEN npm lint/test/build y navegador con API/PostgreSQL reales.

## 5. Verificación y entrega
- [x] Regenerar OpenAPI sin warnings; ejecutar scripts/verify.ps1 -Browser y repetir las suites afectadas tras las correcciones finales (ver registro).
- [x] Revisión independiente, corregir fallos importantes con regresiones.
- [x] Documentar uso, limitaciones y evidencia en IMPLEMENTATION_LOG.md; levantar demo local.
