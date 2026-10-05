# Operación del módulo Gym

## Catálogo

El propietario administra planes/promociones propios. Precio, moneda, duración, fechas de venta y disponibilidad quedan versionados. Una pantalla desactualizada no sobrescribe una edición posterior: recarga antes de guardar. Las promociones se venden por su precio final; no hay cupones combinables. Desactivar conserva versiones e inscripciones existentes.

## Inscripción y renovación

Se requiere ficha activa y acceso a gym.manage/receivables.manage. Elegir una fecha de hoy o futura, revisar condiciones y confirmar. El servidor recalcula para detectar cambios entre revisión y confirmación. Una renovación comienza como mínimo al terminar el último período contratado, aunque tenga pagos pendientes.

La UI muestra inicio y último día incluidos. Internamente el fin es exclusivo. Un plan de 30 días desde el 1 de septiembre cubre hasta el 30; vence al comenzar el 1 de octubre. Un mes desde el 31 de enero de 2027 vence al comenzar el 28 de febrero; cubre hasta el 27. Cada renovación calcula su duración desde su nuevo inicio; no hay anclaje recurrente al día original ni cobro automático.

## Cambios de servicio

- Congelar: motivo, primer y último día incluidos, desde hoy y dentro del período. Extiende el final por esos días y desplaza por igual períodos futuros. Si un período posterior ya tiene una congelación o cancelación, se rechaza el cambio para no mover condiciones ya comunicadas.
- Cancelar: el servicio termina al comenzar la fecha efectiva. Admite cancelar una membresía futura desde su inicio. No cancela otras renovaciones ni altera deuda/pagos.
- Corregir: motivo y rango válido sin superponer otra membresía. No admite períodos con congelación o cancelación registrada. Conserva antes/después y no modifica importe contratado.

## Dinero

Cargo, pago y devolución son registros distintos. La interfaz registra un abono por cargo; la API también permite aplicar un pago a varios cargos del mismo cliente y moneda. No hay dinero sin aplicar, recargos automáticos ni cambios de moneda históricos. No registrar datos de tarjetas.

La devolución manual requiere que el propietario confirme que devolvió el dinero por fuera. No transfiere fondos ni emite comprobante fiscal. Revierte parte de la aplicación del pago y aumenta el saldo adeudado. No existe condonación/nota de crédito en este hito; no utilizar la devolución como sustituto de ese proceso.

Las cantidades usan dos decimales y código de moneda explícito. No hay conversión de divisas ni soporte específico para monedas con distinta cantidad de decimales.

## Asistencia y vencimientos

En **Asistencia**, busca por nombre y selecciona **Revisar entrada**. El servidor comprueba ficha activa y servicio según la fecha local del negocio. Una membresía vigente permite entrar aunque tenga deuda. Sin servicio actual (vencida, sin plan o inicio futuro), sólo el propietario autoriza una excepción con motivo. Ficha inactiva o congelación vigente bloquean cualquier entrada.
La revisión muestra el último día del período vigente o la última cobertura anterior, y el próximo inicio contratado cuando exista. No cuenta períodos cancelados antes de prestar servicio. Los datos mínimos de fechas están disponibles con permiso de asistencia, aunque el módulo de gestión de membresías esté deshabilitado.

La segunda visita del mismo día requiere marcar **Confirmo otra visita hoy**. Si otra persona registra una visita entre revisión y confirmación, se exige revisar otra vez. Los reintentos del mismo formulario reutilizan la clave original, incluso si se refrescan las consultas al volver a la pestaña. Ante una respuesta perdida, reintenta desde ese formulario; si lo cierras o recargas la página, consulta primero el historial.

El propietario anula entradas equivocadas con motivo. Se conservan entrada original, actor, instante, decisión, estado del servicio y evento de anulación. Una anulación no registra una salida ni modifica dinero o contratos. El resumen de asistencia cuenta las entradas válidas y muestra las anuladas por su fecha original.
El historial muestra autor, fecha y motivo de la anulación. Búsqueda, historial y vencimientos ofrecen reintento explícito si falla su consulta; reintentar una consulta no registra entradas ni movimientos.

**Vencimientos y reportes** permite filtrar estados por cliente; una renovación contigua extiende la cobertura mostrada. Una brecha deja visible el siguiente inicio. Los clientes vencidos muestran el último día cubierto. Los días calendario hasta fin de cobertura no equivalen a los días de servicio restantes que muestra la cuenta al descontar congelaciones.

Los reportes del propietario admiten 1–366 fechas inclusivas. Pagos y devoluciones corresponden a la fecha de cada movimiento en la zona del negocio. El saldo pendiente siempre es el actual al instante indicado, incluso si el rango elegido es antiguo o la ficha está inactiva. No se suman monedas distintas ni se infiere conciliación bancaria.

## Permisos e historial

Las escrituras requieren sesión/CSRF y permisos vigentes del workspace. Catálogo y ajustes: propietario. Inscripción y cobros: propietario o recepción. Coach permanece denegado. Todas las nuevas tablas de negocio tienen RLS; versiones/movimientos/auditoría no se editan ni borran por runtime.

Inscripciones, ajustes, pagos y devoluciones llevan una clave UUID de solicitud. Un reintento idéntico dentro del formulario conserva esa clave. Si se pierde la conexión, reintentar desde el mismo formulario; antes de cerrar/recargar tras una respuesta incierta, consultar el historial para comprobar si se registró. Las claves no se almacenan en localStorage.

## Verificación

Usar `scripts/verify.ps1 -Browser` con los servidores de desarrollo detenidos y PostgreSQL activo. Las pruebas concurrentes necesitan commits reales y conservan historial ficticio en workspaces exclusivos desactivados de mygym_test; no evaden las prohibiciones de borrado usando migrator. Mygym_e2e conserva también sus casos ficticios.

La comprobación visual cubre escritorio y 390px. Estas pruebas no sustituyen una evaluación de carga ni convierten la instalación de desarrollo en un producto listo para producción.
