# Permisos y aislamiento del núcleo

| Operación | OWNER | RECEPTION | COACH | Sin acceso vigente |
| --- | --- | --- | --- | --- |
| Descubrir workspace propio activo | Sí | Sí | Sí | No |
| Listar/crear/editar fichas | Con clients.manage | Con clients.manage | No | No |
| Cambiar roles/vincular cuentas | Sin endpoint | Sin endpoint | Sin endpoint | No |
| Borrar ficha/auditoría | No | No | No | No |
| Consultar planes y membresías | Con gym.manage | Con gym.manage | No | No |
| Crear/editar planes y promociones | Con gym.manage | No | No | No |
| Inscribir/renovar (crea cargo) | gym.manage + receivables.manage | gym.manage + receivables.manage | No | No |
| Congelar/corregir/cancelar | Con gym.manage | No | No | No |
| Consultar cargos/pagos y registrar abonos | Con receivables.manage | Con receivables.manage | No | No |
| Registrar devolución manual | Con receivables.manage | No | No | No |
| Buscar/revisar/registrar entrada vigente | Con gym.attendance | Con gym.attendance | No | No |
| Autorizar excepción o anular entrada | Con gym.attendance | No | No | No |
| Consultar vencimientos | Con gym.manage | Con gym.manage | No | No |
| Reporte agregado de asistencia | Con gym.reports | No | No | No |
| Reporte monetario y saldo actual | receivables.reports + receivables.manage | No | No | No |

La sesión identifica al usuario. Cada petición valida acceso, workspace activo, capacidad y rol.
Workspace URL no es autorización. Una ficha ajena da 404. Usuarios sin sesión reciben 403.
Identidad y workspaces no tienen RLS: sus selectores limitan el descubrimiento antes del contexto.
ClientRecord, AuditEvent y todas las tablas de gym/receivables tienen RLS USING/WITH CHECK con app.workspace_id local a transacción.
Runtime no es propietario, superusuario ni BYPASSRLS, no puede asumir rol migrator y no tiene CREATE de esquema.
RLS defiende contra consultas sin filtro, no contra toma de control completa de la aplicación/SQL arbitrario.
Auditoría append-only para runtime; ficha y evento se confirman juntos. No valores personales en eventos.
PlanVersion, MembershipChange, Freeze y los registros receivables son append-only para runtime.
Attendance y AttendanceVoid también son append-only y tienen RLS forzada. La búsqueda de asistencia sólo devuelve nombre, ID y estado activo de la ficha; no habilita acceso a sus contactos o cobros.
Plan y Membership admiten actualizaciones de servicios autorizados pero no borrado.
Los cambios conservan fechas anteriores/nuevas y motivo dentro del historial privado del cliente; AuditEvent registra sólo nombres de campos.
Las operaciones e historiales de un mismo cliente se serializan bloqueando su ficha para evitar saldos o períodos inconsistentes durante escrituras concurrentes.
Privilegios de migraciones sólo en comandos explícitos. Pruebas fallan si las credenciales evaden RLS.
No fotos, exportaciones, portales de clientes, MFA ni datos sensibles clínicos en este hito.
Desarrollo: datos ficticios, cluster y .env privados, loopback; no constituye certificación de producción.
