# Registro de implementación

Plan: docs/superpowers/plans/core.md

- Aprobación del usuario: implementar primer hito y preparar entorno necesario.
- Diagnóstico: carpeta vacía, sin Git; Python 3.13.4, Node 22.16.0, npm 10.9.2, Git 2.51.2; PostgreSQL no detectado.
- Ruling: repositorio nuevo en feat/core dentro de carpeta autorizada, sin worktree adicional ni commit inicial: no hay trabajo previo que aislar ni autorización específica para commits.
- Ruling: registro persistente en docs, adaptando scripts de habilidades basados en commits/Bash a PowerShell y repositorio sin commits.
- Pre-flight: User -> WorkspaceAccess -> autorización -> servicios clients -> audit; contexto RLS envuelve servicios y consultas; API -> UI. Sin interfaces incompatibles detectadas.
- Preparación: Git local feat/core, .venv y dependencias bloqueadas, Node/npm existentes.
- Ruling: PostgreSQL 17.11 portable dentro de .local/pg17, sólo loopback 55432 y sin servicio global.
  Archivo oficial EDB fijado por versión y SHA256. Descompresión PowerShell completa fue lenta;
  extracción selectiva Python de bin/lib/share resolvió la preparación sin cambiar arquitectura.
- Ruling: provisión de roles mediante scripts/provision_local.py en lugar de SQL con contraseñas pegadas;
  genera secretos aleatorios, aplica ACL y admite reejecución sin borrar bases.
- Ruling: mantuvimos Python 3.13.4 y Node 22.16.0 detectados y compatibles; no actualizaciones globales innecesarias.
  Revisar parches de intérpretes antes de producción. Chromium se descargó en caché de Playwright del usuario.
- Task 1: identidad implementada. RED rutas ausentes; GREEN 7 pruebas auth inicialmente.
  Límites PostgreSQL: cuenta 5/origen 30 en 900 s, HMAC, locks ordenados, expiración comprobada.
- Task 2: workspaces implementados. RED API inexistente 404; GREEN descubrimiento, revocación y roles.
- Task 3: fichas/auditoría implementadas. RED alta 404; GREEN validación, inyección, límites,
  desactivación, igualdad de correos sin vínculos, auditoría y rollback.
- Task 4: RLS implementado. RED inserciones sin/cross contexto permitidas y anidamiento no rechazado;
  GREEN USING/WITH CHECK, FORCE RLS, runtime no propietario/BYPASSRLS, commit/rollback/reuso.
  scripts/verify_role_guard.py acepta runtime real y rechaza credenciales migrator reales.
- Ruling: runtime SELECT sobre django_migrations es necesario para comprobación de runserver;
  sin permisos para escribir esa tabla ni cambiar esquema. Primer arranque detectó este permiso faltante.
- Task 5: frontend implementado, responsive español, Router/Query/Tailwind y API real.
  RED validaciones y pantalla login ausente; GREEN formularios, dos workspaces y sesiones reales.
- Bug encontrado por E2E: QueryClient.clear dejaba observador de auth con valor anterior tras logout.
  Regresión Vitest RED -> notificar me=null antes de purgar consultas privadas -> GREEN.
- Revisión independiente review_core: sin bypass backend concreto; dos hallazgos importantes de sesión.
  1. Logout con sesión ya expirada: E2E RED -> verificar me tras 403 y limpiar sólo si no hay sesión -> GREEN.
  2. Cambio owner->coach sin BroadcastChannel conservaba formulario: E2E RED -> reconciliar identidad,
     cancelar/purgar solicitudes/caché y clave React por usuario -> GREEN.
  También se oculta formulario cuando se confirma denegación. Revisión posterior sin hallazgos importantes pendientes.
- Task 6: demo idempotente no destructiva y pruebas añadidas. Tres bases exclusivas: dev/test/e2e.
  npm ci ejecutado: 199 paquetes, auditoría npm 0 vulnerabilidades informadas.
- Verificación intermedia: suite backend 46 passed; regresión concurrente adicional 1 passed;
  Vitest 5 passed; TypeScript/build/ESLint/Ruff/pip check/Django check/OpenAPI sin errores.
  Migraciones sin cambios pendientes. Navegador 5 passed en ejecución previa completa.
- No commits, push, repositorio remoto, compras, LAN ni despliegue. Archivos privados excluidos de Git verificados.
- Verificación final backend: `python -m pytest --tb=short` -> 47 passed, 72.96 s, PostgreSQL real.
- Verificación final frontend: ESLint limpio, Vitest 5 passed, TypeScript + Vite build exitosos.
- Revisión visual real desktop/mobile: nombres comprimidos en tabla móvil. Regresión Playwright RED
  (nombre de 144px de altura) -> filas móviles como tarjetas -> GREEN. Playwright completo: 6 passed, 17.6 s.
- `start-dev.ps1` arrancó backend/UI en loopback y confirmó health; `stop-dev.ps1` detuvo procesos propios.
  Guardia de puerto ocupado comprobada: rechaza arranque sin detener procesos ajenos.
- Contexto OpenAPI validado sin warnings, sin migraciones pendientes; pip check y Ruff limpios.
- Documentación de continuidad y matriz de 14 criterios en docs/operations/acceptance.md.
- Tareas 1-6 implementadas y verificadas dentro del alcance de desarrollo. Validación del instalador comercial
  y de una instalación limpia en otra computadora no realizada; no forma parte de este hito.
- `setup-dev.ps1` reejecutado completo: dependencias reproducidas, checksum PostgreSQL verificado,
  provisión/migraciones/demo no destructivas y Chromium disponible. Exit 0.
- Cierre: repositorio nuevo sin base/commits; conservar feat/core y archivos locales según alcance autorizado.
  Se marcó intención de añadir archivos para revisar diff completo; no se creó commit.
- Reinicio verificado: stop-dev.ps1 -Database -> arranque start-dev.ps1 -> health {status:ok}, UI HTTP 200.
  Se deja backend, frontend y PostgreSQL funcionando en loopback para revisión del usuario.
- Captura móvil corregida inspeccionada: nombres y edición legibles; capturas privadas en .local/ui-*.png.
- Resultado del hito: 58 pruebas aprobadas (47 backend + 5 Vitest + 6 Playwright), sin pruebas omitidas
  en estas suites. Diff completo sin errores de whitespace; archivos privados ignorados.
- Siguiente hito propuesto, no ejecutado: Gym operativo. Resolver reglas de duración/renovación,
  congelaciones/cancelaciones, pagos parciales y devoluciones antes de implementar membresías/cobros.
- Continuación: el usuario confirma planes por días o meses calendario, elegibles por plan, y
  solicita que cada gimnasio pueda editar su oferta para promociones y otras necesidades.
  Decisiones confirmadas y propuesta restante registradas en docs/superpowers/specs/gym-business-rules.md.
  Edición versionada, permisos y reglas de vigencia/cobros todavía son propuestas; no se presentan como aprobadas.

## Hito Gym operativo — 2026-09-30

- El usuario aprueba las reglas propuestas y autoriza contrastar referencias web. Consultadas documentación oficial de Gymdesk (pausas/pagos) y Glofox (membresías); URLs y diferencias explícitas en gym-operations.md.
- Diseño y plan: docs/superpowers/specs/gym-operations.md y docs/superpowers/plans/gym-operations.md. Ejecución inline, sin commits ni servicios externos. Se conserva feat/core (repo inicial sin commits); no crear worktree requiere inventar un commit base, fuera de autorización.
- Ruling: usar registro durable aquí en lugar de scripts de ledger basados en commits inexistentes. No se borra el núcleo ni se rehacen tareas previas.
- Ruling: congelar desplaza períodos futuros por igual, pero rechaza si ya tienen congelaciones/cancelaciones; evita cambiar silenciosamente condiciones comunicadas. Cancelar no condona deuda. Devolver resta aplicación y restaura deuda, con advertencia explícita en UI.
- Tarea 1: catálogo versionado, días/meses, fechas de venta, promociones y permisos. RED 404/import ausente -> GREEN 5 pruebas; migraciones PostgreSQL reales, sin nuevas dependencias.
- Tareas 2-3: inscripción/cargo atómicos, renovación, snapshots, congelación/cancelación/corrección, pagos parciales/multicargo y devoluciones. RED endpoints inexistentes -> GREEN suites; fallo de cargo inyectado revierte membresía y auditoría.
- RLS ampliada a 11 tablas nuevas de negocio. Runtime sin DELETE; sólo Plan/Membership admiten UPDATE. Guard de arranque verifica todas las tablas nuevas. Historial y escrituras toman bloqueo de cliente; utilidades comunes en modules/shared, sin dependencia receivables -> gym.
- Concurrencia probada con commits reales y conexiones runtime distintas: inscripción repetida única, cobros simultáneos no exceden deuda, devoluciones no exceden pago. Historial ficticio queda en workspaces exclusivos desactivados de mygym_test. Test demo ajustado para contar sus dos espacios, sin asumir que no existe otro historial de pruebas.
- Colisión de request_id concurrente entre clientes distintos: RED UniqueViolation -> lock transaccional por workspace/modelo/request_id en replay -> GREEN rechazo de validación. Claves de reintento se conservan en el formulario; no se persisten en localStorage.
- Tarea 4: catálogo, edición/promoción, cuenta del cliente, previsualización/inscripción, ajustes, abonos/devoluciones e historial. Prueba navegador real pasó; inspección de screenshots desktop y 390px confirma legibilidad/sin overflow. UI saldos separada de vigencia; dinero no se transfiere desde MyGym.
- Primer E2E iniciado antes de migrar e2e detectó esquema pendiente; se migraron dev/test/e2e y se repitió. Otro fallo era espera de prueba antes de completar refetch; corregida espera observable de ficha. Altas saltan a última página para mostrar el nuevo registro.
- Revisión independiente review_gym: tres Important. (1) Cancelación futura de duración efectiva cero retrasaba nueva inscripción: RED fecha desplazada -> excluir período sin servicio -> GREEN. (2) Confirmación con 403 dejaba controles: RED Playwright -> ocultar preview/form y refrescar autorizaciones -> GREEN. (3) UI exigía ambas capacidades para todo: RED Playwright -> queries/secciones/acciones independientes, ambas sólo para inscribir -> GREEN.
- Minor de revisión resuelto: catálogo distingue Inactivo/Programado/Disponible/Venta finalizada según fechas del workspace; 2 pruebas RED->GREEN, suite frontend 7/7.
- Reglas de auth core, SQL arbitrario comprometido, facturación fiscal/pasarela/condonación fuera del alcance revisado; no se prometen. UI aplica un abono a un cargo; la API admite distribución multicargo.
- Verificación completa y segunda revisión final en curso; aún no se registra resultado final de este hito.
- Segunda revisión: tres Important y disponibilidad de catálogo resueltos. Residual: clave de MembershipChange limitada a una membresía permitía reuso en otra; RED segundo cancel devolvía 200 -> replay por workspace -> GREEN 3 pruebas de ajustes. Revisor confirmó la corrección y no dejó hallazgos importantes pendientes.
- Última pasada de navegador detectó alta con >25 fichas que usaba un recuento capturado antes de completar consulta. Se calcula la página desde caché recién invalidada/refrescada; aplicado también al catálogo. Regresión E2E real con más de 25 fichas pasó. Helpers de navegador recorren páginas de planes para no depender de una base e2e vacía.
- Verificación final después de las correcciones: backend **63 passed en 131.75s**, Vitest **7 passed**, Playwright completo **10 passed en 40.4s**. Total **80 pruebas**, sin omisiones. ESLint, TypeScript/build, Ruff, OpenAPI --validate --fail-on-warn y ausencia de migraciones pendientes confirmados.
- `verify.ps1 -Browser` detectó el fallo de paginación; después se repitieron las suites afectadas y todos los componentes de verificación quedaron en verde. No se presenta aquella ejecución inicial como exitosa.
- Rol runtime real aceptado y migrator real rechazado por la guardia; RLS forzada en las tablas protegidas. Diff sin errores de whitespace; archivos nuevos añadidos sólo con intención de seguimiento (`git add -N`), sin commit ni push.
- `start-dev.ps1` completado tras cerrar pruebas. Backend/UI disponibles en http://127.0.0.1:5173 y PostgreSQL en loopback. Se mantiene la contraseña privada existente.
- Hito Gym implementado en desarrollo. Pendientes de otros hitos: asistencia/reportes, Coach, fotos/portal, fiscal/pasarela, instalador comercial y controles productivos. No se implementa condonación ni se envían fondos desde una devolución manual.

## Continuación: asistencia, vencimientos y reportes — 2026-10-02

- El usuario autoriza continuar con el hito propuesto: asistencia, vencimientos y reportes básicos.
- Revisados contexto, especificación/plan del núcleo, servicios de membresías/cobros y soporte de claves de reintento. No se han modificado modelos ni aplicado migraciones para este hito.
- Borrador técnico en docs/superpowers/specs/gym-attendance-reports.md. Las consultas financieras distinguirán movimiento del período de saldo actual y no agregarán monedas diferentes. La vista de vencimientos evitará contar como vencido a quien ya tiene renovación vigente.
- Se consultaron dos reglas de asistencia: excepciones cuando no hay servicio habilitado y visitas repetidas durante el día. Respuestas pendientes; no asumir que las opciones preseleccionadas equivalen a una respuesta.
- Respuestas recibidas: vigente entra con deuda; vencida/sin servicio admite excepción OWNER con motivo; congelada/inactiva bloqueada. Segunda visita requiere confirmación explícita y recuento previo. Diseño actualizado con ambas respuestas.
- Se usa superpowers:executing-plans, TDD y revisión independiente final. Continúa feat/core sin commits; se conserva el trabajo anterior.
- Ruling: conservar registro de ejecución en este archivo y revisar archivos locales, sin scripts basados en commits ni nuevo worktree; el repositorio no tiene commit base y el usuario prohíbe crear commits sin instrucción específica. Coste: revisión sin comparación con una revisión Git previa.
- Ruling: una sentencia SQL por reporte en lugar de REPEATABLE READ de toda la petición. PostgreSQL ofrece una instantánea común a sus agregados y página; evita cambiar aislamiento después de consultas previas. Coste: futuros agregados deben permanecer dentro de esa sentencia o diseñar otro límite transaccional.
- Ruling: la vista operativa muestra días calendario de cobertura contigua; el cálculo de días de servicio permanece en la cuenta del cliente. Coste: consultar la cuenta para descontar congelaciones del contador de servicio.
- Tarea 1: Attendance/AttendanceVoid, snapshot de actor/estado/fecha, excepciones, visitas repetidas, anulación, búsqueda y paginación; RLS y privilegios append-only. Primera ejecución falló porque PostgreSQL estaba detenido: no fue RED funcional válido. Tras iniciar PostgreSQL y migrar, los tres casos iniciales pasaron. Regresión adicional de medianoche sí RED (instante y fecha diferentes) -> capturar un solo instante -> GREEN.
- Tarea 2: RED por módulo y rutas inexistentes -> implementar SQL parametrizado y rangos locales -> GREEN. Pruebas adicionales de renovaciones contiguas/brechas, monedas, múltiples aplicaciones/devoluciones y permisos independientes. Los relojes simulados de pruebas de fecha inicialmente expiraban la sesión; se usa autenticación de prueba para esos casos, conservando pruebas HTTP de sesión reales en el resto.
- Migraciones 0005/0006/0007 aplicadas a dev/test/e2e con migrator; pruebas ejecutan runtime restringido. Capacidades demo agregadas sin restablecer contraseñas ni permisos existentes.
- Tarea 3: Playwright RED por enlace Asistencia ausente -> interfaz completa -> GREEN recorrido real. Un intento previo a migrar e2e falló en alta de ficha y no se contó como RED de la interfaz. TypeScript/build correctos; capturas de asistencia y reportes a 390px inspeccionadas, sin desbordamiento horizontal.
- Revisión independiente read-only `review_attendance` (gpt-6-astra): Important por desmontar el intento de entrada durante refetch y perder su clave de reintento; sin defectos críticos ni importantes adicionales en backend. Dos observaciones de fechas clasificadas inicialmente Minor.
- Final: Ruling: la fecha de cobertura anterior ausente en filas vencidas se eleva a Important: una lista de vencimientos debe permitir saber cuándo terminó el servicio para priorizar la atención. Se corrige con regresión de navegador. Coste de omitirlo: decisiones operativas sin fecha de referencia del cliente.
- Final: minor (deferred): mostrar la fecha de término también dentro del diálogo de entrada. La revisión muestra estado y fecha actual; el servidor valida vigencia. El dato contractual sigue disponible en la cuenta con gym.manage. No afecta la regla de admisión.
- Final: Ruling: instalación/despliegue comercial, revisión general del núcleo previo, SQL arbitrario desde una aplicación comprometida, exportaciones/control físico/conciliación/fiscalidad se mantienen fuera de esta revisión. Son límites ya documentados; no se afirman garantías productivas ni controles de esos módulos. Coste: requieren hitos y revisiones específicas antes de ofrecer esas funciones.
- Verificación completa intermedia: backend 76/76 y Vitest 7/7, lint/build/RLS/OpenAPI correctos. Playwright 11/13: fallo del nuevo test de enfoque por emitir evento en document en lugar de window (corregida simulación); otro fallo reprodujo cierre tardío del diálogo anterior al abrir una segunda visita. Ambos se tratan antes de la entrega; esta ejecución no se declara exitosa.
- Final: fixed intento perdido al refrescar — regresión real commit + respuesta HTTP perdida + cambio de pestaña RED (motivo borrado) -> instantánea de revisión independiente del refetch y diálogo estable -> GREEN (misma request_id, una sola entrada). Cierre de diálogo ocurre tras completar refresco; ya no cierra por carrera la siguiente revisión.
- Final: fixed fecha de vencimiento ausente — Playwright RED (fecha no visible) -> mostrar previous_end menos un día como último día cubierto -> GREEN. Suite focal de navegador 4/4, ESLint limpio. Pendiente verificación completa posterior a esta única pasada de correcciones.
- Verificación final posterior a correcciones: `scripts/verify.ps1 -Browser` exit 0. **76 backend passed en 110.24s + 7 Vitest + 14 Playwright en 1.2m = 97 pruebas**, sin omisiones. pip check, runtime real aceptado/migrator rechazado, Ruff, Django check, migraciones sin pendientes, OpenAPI --validate --fail-on-warn, ESLint y TypeScript/Vite aprobados.
- Tareas 1–3 completas con la evidencia y limitación de RED inicial descritas arriba. Revisión final completada con una mejora menor diferida. Diff sin errores de whitespace; archivos nuevos con intención de seguimiento, sin commits/push/despliegue. .env/.local y capturas privadas siguen ignorados.
- Cierre con superpowers:finishing-a-development-branch: se conserva feat/core y el directorio compartido conforme a autorización existente; no se solicita una nueva decisión de integración ni se limpia trabajo ajeno.
- `scripts/start-dev.ps1` exit 0: backend/UI disponibles en http://127.0.0.1:5173, health y UI comprobados por el script, PostgreSQL disponible y runtime restringido. Contraseña demo existente conservada. Tarea 4 completa dentro del alcance de desarrollo.

## Mejora de calidad autorizada — 2026-10-02

- Petición: «mejora todo lo que tengas que mejorar». Revisión y mejoras acotadas a flujos existentes; se conserva monolito modular, reglas de negocio y PostgreSQL/RLS. Sin dependencias ni migraciones nuevas. Se resuelve la mejora menor diferida del hito anterior.
- Diseño aplicado: revisión de entrada con fechas contractuales mínimas (período actual, cobertura anterior y próximo inicio), navegación según capacidades, historial de anulaciones con autor/instante, y recuperación explícita de consultas fallidas.
- RED backend: faltaban last_day y void_actor/voided_at. GREEN tras selector de fechas con cancelación/fin exclusivo, metadatos de anulación y contrato OpenAPI ampliado. Se verifica exclusión de períodos futuros cancelados al inicio y acceso a fechas con gym.manage/clients.manage deshabilitados.
- RED navegador: landing siempre dirigía a clientes, menús mostraban opciones sin capacidad, revisión no mostraba fechas y faltaba Reintentar búsqueda. Implementados destino según capacidades, menús coherentes, fechas y botón reutilizable para búsqueda/historial/vencimientos.
- Pruebas de navegación inicialmente encontraron una carrera en sus interceptores asíncronos durante cierre. Se toma respuesta real de workspaces antes de instalar fixture estática de capacidades; no se ocultan errores ni se altera autorización del backend. El fallo de red se mantiene hasta el reintento explícito para evitar que un refetch previo invalide la simulación.
- Revisión independiente read-only `review_polish`, según superpowers:requesting-code-review: sin Critical/Important. Observación menor de cobertura atendida: prueba visual de fechas restringe también capacidades a gym.attendance. Prueba backend usa capacidades reales deshabilitadas.
- Verificación completa y reapertura de demo pendientes; no se declara todavía este ciclo terminado.
- Cierre de calidad: `scripts/verify.ps1 -Browser` exit 0, **77 backend en 136.21s + 7 Vitest + 18 Playwright en 1.2m = 102 pruebas**, sin omisiones. Ruff, ESLint, tipos/build, OpenAPI, guardia runtime restringida y migraciones sin pendientes aprobados. Diff sin errores de whitespace.
- Captura `.local/attendance-dates-mobile.png` inspeccionada a 390px: fechas y acciones legibles, sin desbordamiento. El test de fechas usa sólo gym.attendance en la navegación; backend verifica también con capacidades de membresías/fichas deshabilitadas.
- `scripts/start-dev.ps1` exit 0: demo disponible en http://127.0.0.1:5173, conservando credenciales y datos ficticios. No quedan hallazgos pendientes de esta revisión. No commits, push, despliegue productivo ni módulos nuevos del roadmap.

## Publicación inicial en GitHub — 2026-10-05

- Usuario autoriza commit y push del proyecto a https://github.com/HenryFerOZ-2000/mygym.git.
- Repositorio local sin commits previos y remoto sin referencias. Se conserva README existente y se prepara rama main con todos los archivos del proyecto.
- Revisados archivos candidatos, exclusiones de .env/.local/dependencias/bases/certificados y patrones de claves; sin secretos detectados en los archivos candidatos. .env.example contiene únicamente marcadores.
- Publicación de código; sin cambios funcionales ni despliegue. No se repite la suite de aplicación para esta operación de Git; su evidencia anterior permanece registrada arriba.
- Comprobación de publicación: git push -u origin main y comparación de HEAD con refs/heads/main del remoto.
