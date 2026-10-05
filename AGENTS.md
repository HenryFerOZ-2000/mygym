# MyGym

Leer docs/PROJECT_CONTEXT.md, docs/superpowers/specs/core.md y docs/superpowers/plans/core.md antes de modificar.
Monolito Django/DRF + React/TypeScript. PostgreSQL 17 real. Windows nativo/PowerShell; Docker y WSL no son requisitos.
Alcance autorizado: núcleo, Gym (planes/promociones, membresías/cobros) y asistencia/vencimientos/reportes, según docs/superpowers/specs/gym-operations.md y gym-attendance-reports.md. Resto: roadmap.
Roles por workspace, capacidades independientes del despliegue. Nunca fusionar fichas por correo.
Runtime PostgreSQL restringido, separado de migraciones. Contexto tenant transaccional. No usar superusuarios para demostrar aislamiento.
No datos reales, secretos en Git, servicios remotos obligatorios, commits/push/despliegues sin instrucción específica.
Cada módulo escribe sus modelos; servicios explícitos, no coordinación mediante señales.
Prueba relevante RED -> cambio -> GREEN -> diff -> documentación. No debilitar pruebas ni reemplazar PostgreSQL por SQLite.
Registrar progreso y decisiones en docs/operations/IMPLEMENTATION_LOG.md. Comandos verificados se publican en README.md.

Comandos disponibles desde raíz: .\scripts\setup-dev.ps1, .\scripts\start-dev.ps1,
.\scripts\stop-dev.ps1 [-Database], .\scripts\verify.ps1 [-Browser].
Detener backend/frontend antes de -Browser; PostgreSQL debe permanecer disponible.
No inspeccionar ni publicar .env o .local/database.json. Credenciales demo sólo para uso local del propietario.
