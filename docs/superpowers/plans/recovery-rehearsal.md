# Primer flujo de recuperación ficticia

Especificación operativa: ../../operations/backup-recovery.md.

1. Leer contexto y consultar catálogo de permisos sin filas/secretos: completado; exportación completa bloqueada.
2. RED pruebas de sobre, versiones, corrupción, sobrescritura, guardias, sesiones y RLS: ausencia del módulo confirmada.
3. GREEN módulo recovery independiente de Cloud y ensayo schema-only Windows: implementar/verificar antes de publicar.
4. Regresión backend y checks; registrar resultados reales, revisar diff y exclusiones; commit/push autorizado a rama de trabajo.
5. Separado y bloqueado: aprobar identidades de respaldo/recuperación y base candidata; implementar orquestación de restore/integridad con prueba real y sin activar aplicación.

No migraciones de base activa, grant de BYPASSRLS, cuentas nuevas, datos reales ni UI de operaciones incompletas en las tareas 1–4.

Cierre de tareas 1-4: 106 pruebas backend aprobadas, 19 afectadas repetidas tras guardia final; ensayo PostgreSQL schema-only/DPAPI real aprobado, lint/checks/OpenAPI sin cambios. Tarea 5 bloqueada por autorizacion de identidades/destino; no se ejecuta restore.
