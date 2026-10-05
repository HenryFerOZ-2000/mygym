# Attendance and Reports Implementation Plan

**Goal:** entrada manual auditada, vencimientos operativos y reportes por fecha/moneda.
**Architecture:** ampliar gym para asistencia/servicio y receivables para reportes monetarios. Nuevos registros append-only con RLS. Cada endpoint revalida acceso y capacidad.
**Spec:** ../specs/gym-attendance-reports.md
**Execution:** superpowers:executing-plans inline, pruebas RED/GREEN y revisión independiente final; sin commits ni despliegues.

## Restricciones y decisiones

Reglas de asistencia confirmadas el 02/10/2026: vigente entra sin bloqueo por deuda; vencida/sin servicio permite excepción sólo OWNER con motivo; congelada o ficha inactiva denegada. Repetición diaria requiere confirmación y recuento previo; doble clic/reintento no duplica.
Zona horaria del workspace; dinero Decimal y separado por moneda. Rango inclusivo máximo 366 fechas. Saldo actual separado del movimiento por período. Datos ficticios y PostgreSQL runtime restringido.

## Review focus

Cambio de medianoche entre previsualización y confirmación; anulación concurrente y reintentos; membresía futura/cancelada y excepciones; renovación contigua frente a brecha; totales monetarios multiplicados por joins o mezclados entre monedas.

## 1. Asistencia
Archivos: gym/attendance.py, attendance_api.py, attendance_serializers.py, models.py, migrations, urls.py; tests/test_attendance.py.
Interfaces: attendance_preview(context,client_id), record_attendance(context,client_id,data), void_attendance(context,attendance_id,data).
- [x] Pruebas de estados/roles/repetición/reintentos/anulación/aislamiento; RED funcional confirmado en regresión de medianoche (limitación del primer RED registrada en log).
- [x] Attendance + AttendanceVoid append-only, RLS, snapshot de decisión y actor; endpoints preview/create/list/void, búsqueda paginada.
- [x] GREEN pruebas PostgreSQL y migraciones dev/test/e2e.

## 2. Vencimientos y reportes
Archivos: gym/reports.py, report_api.py; receivables/reports.py; shared/reporting.py; tests/test_operational_reports.py.
Interfaces: expiry_report(context,query), attendance_report(context,from_date,to_date), financial_report(context,from_date,to_date).
- [x] RED inicial reportes inexistentes; GREEN renovación/brechas, rangos locales, monedas/aplicaciones/devoluciones y saldo de ficha inactiva.
- [x] Una sentencia SQL por reporte comparte instantánea entre agregados/página; paginación y permisos independientes; OpenAPI estricto.
- [x] GREEN suite relevante y aislamiento.

## 3. UI y permisos
Archivos: frontend/src/features/gym/Attendance.tsx, Reports.tsx, router.tsx, Clients.tsx, gym/ui.tsx; seed_demo.py; frontend/tests/e2e/attendance.spec.ts.
- [x] RED navegador búsqueda/primera visita/repetición/anulación/reporte.
- [x] UI española con confirmación explícita, indicadores de alcance/fechas/monedas, estados vacíos/errores y permisos actualizados.
- [x] GREEN navegador con API real, móvil, lint/tipos/build.

## 4. Entrega
- [x] Revisión independiente y correcciones con regresiones; fecha de término dentro del diálogo de entrada resuelta en continuación de calidad del 02/10/2026.
- [x] Verificación del hito original: 97 pruebas, documentación, diff sin errores y demo local levantada. Desarrollo solamente. La mejora menor diferida fue resuelta en la continuación de calidad; evidencia actual en el log.
