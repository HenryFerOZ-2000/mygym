# Gym operativo: diseño técnico

Fuente: reglas aceptadas en `gym-business-rules.md`. Implementación local sobre el núcleo existente, sin nuevas dependencias comerciales ni commits automáticos.

## Recorrido y módulos

Propietario: catálogo de planes/promociones → ficha del cliente → previsualización de inscripción → confirmar vigencia y cargo → registrar abonos → consultar saldo e historial → congelar, corregir, cancelar o devolver cuando proceda.
Recepción: consultar catálogo, inscribir/renovar y cobrar. Coach: sin acceso administrativo. Las capacidades `gym.manage` y `receivables.manage` se verifican separadamente; una inscripción requiere ambas porque crea un cargo.

`gym` conserva Plan, PlanVersion, Membership, MembershipChange y Freeze. `receivables` conserva Charge, Payment, Allocation y Refund. Cada tabla tiene workspace, UUID, RLS forzada y prohibición de borrado runtime. Versiones, movimientos y cambios de historial no se actualizan por runtime. Los modelos nunca permiten una relación entre negocios mediante los servicios.

## Catálogo y promociones

Plan es una identidad estable con disponibilidad; PlanVersion es una instantánea inmutable de nombre, importe Decimal(12,2), moneda de tres letras, tipo DAYS/MONTHS, cantidad, indicador promoción y fechas opcionales de venta. La primera versión es 1. Cada edición exige `expected_version` para detectar una pantalla desactualizada y crea versión nueva. No se modifican membresías anteriores. Una promoción es un plan identificado como oferta, sin motor de cupones ni descuentos combinables. Precio cero permitido para ofertas gratuitas; pagos y devoluciones deben ser positivos.

## Fechas y movimientos del servicio

Intervalos [start_date, end_date): fin exclusivo; la interfaz siempre muestra el último día incluido. Meses se calculan sumando N meses al inicio y ajustando el día al máximo del mes destino. 31/01/2027 + 1 mes termina exclusivamente 28/02/2027; la pantalla advierte que el último día incluido es 27/02/2027. No hay cobro recurrente automático: cada renovación es un período explícito y calcula sus meses desde su propio inicio.

Una previsualización devuelve versión, inicio, último día incluido, precio y moneda. La confirmación repite el cálculo y exige las fechas/versiones vistas; si algo cambió, devuelve validación para revisar. Sin períodos vigentes/futuros, se usa la fecha elegida (hoy o futura). Con períodos contratados, se inicia como mínimo al final del último no cancelado. No se superponen períodos de un cliente.

Congelación: propietario, motivo, inicio >= hoy y rango dentro del período efectivo antes de extenderlo. El rango de suspensión es inclusivo en la UI y exclusivo internamente. Se añade su duración al final del período y se desplazan todos los períodos futuros del mismo cliente por igual, preservando días ya comprados. Para evitar cambiar una suspensión ya comunicada, si algún período afectado posterior ya tiene congelación programada, se rechaza y se informa; no se desplazan silenciosamente sus suspensiones. Cada desplazamiento se registra como MembershipChange con fechas anteriores/nuevas.

Cancelación: propietario, motivo, fecha efectiva >= hoy, dentro del período o igual a su inicio para cancelar una inscripción futura. El servicio termina al inicio de esa fecha. Las renovaciones futuras son contratos independientes y no se cancelan ni adelantan automáticamente. No modifica cargos/pagos.

Corrección: propietario, motivo, intervalo válido, sin solapamiento; no se corrige un período con congelaciones o cancelación registradas. Conserva fechas previas/nuevas en MembershipChange; no cambia precio/cargo. Estados y días restantes se calculan usando la zona horaria del workspace; cliente inactivo no admite nuevas inscripciones y no queda habilitado para servicio.

## Cobros

Inscripción y Charge se crean atómicamente. Payment registra método CASH/TRANSFER, importe/moneda, fecha de registro y aplicaciones explícitas a cargos del mismo cliente/workspace/moneda. Cada pago puede repartir su importe entre varios cargos; la suma debe igualarlo y no superar sus saldos. No hay crédito sin aplicar en este hito.

Refund registra devolución manual, motivo y aplicaciones revertidas; no envía dinero. Se especifica cuánto se devuelve de cada aplicación del pago, sin exceder lo no devuelto. El saldo del cargo vuelve a aumentar por esa cantidad, porque devolver un pago no condona una deuda; la UI lo indica antes de confirmar. Cancelar servicio tampoco condona el cargo. No hay facturación fiscal, conciliación bancaria ni pasarela.

Cada inscripción, congelación, corrección, cancelación, pago y devolución lleva UUID `request_id` con huella del contenido. Reintentar la misma solicitud devuelve el resultado existente; reutilizar la clave con contenido diferente se rechaza. Las operaciones del cliente bloquean su fila para serializar renovaciones, cobros y devoluciones concurrentes; la versión del plan se bloquea al confirmar. Catálogo usa control de versión optimista.

## API y UI

Prefijo `/api/v1/workspaces/{workspace_id}/`. `gym/plans/` GET/POST, `gym/plans/{plan_id}/` PATCH; `clients/{client_id}/gym/` GET historial, `.../gym/preview/` POST, `.../gym/memberships/` POST; `.../gym/memberships/{membership_id}/{freeze|cancel|correct}/` POST. `clients/{client_id}/receivables/` GET, `.../receivables/payments/` POST, `.../receivables/payments/{payment_id}/refunds/` POST. Listas paginadas y orden estable; las consultas de historial no exponen otras fichas. Entradas estrictas, fechas/UUID/importes validados, CSRF y respuestas JSON uniformes.

UI española: catálogo, formularios de edición/promoción y pantalla de membresías/cobros desde cada cliente. Previsualización antes de inscripción; confirmaciones explícitas de cambios y devoluciones. Caché con usuario/workspace/cliente, sin almacenamiento persistente de datos privados. Errores de acceso ocultan formularios. Formularios con etiquetas, diálogo accesible, layout móvil.

## Referencias consultadas el 30/09/2026

- https://docs.gymdesk.com/en/help/docs/freezing-unfreezing-members: distingue pausa, pagos y extensión de vigencia. MyGym adopta extensión por días sin prorrateo automático.
- https://docs.gymdesk.com/en/help/docs/payments: registrar devolución manual no envía fondos. MyGym exige confirmación de devolución externa.
- https://support.glofox.com/hc/en-us/articles/46424071016212-Managing-Memberships-from-Glofox-Pro: presenta períodos activos, futuros y pasados. MyGym mantiene esa distinción visual, sin adoptar cobro recurrente.

Las referencias informan la experiencia; las reglas aprobadas del proyecto prevalecen.
