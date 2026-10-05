# Gym: reglas de planes, membresías y cobros

Estado: reglas aprobadas en conversación. El usuario también autoriza contrastar el diseño con negocios de referencia en la web.

## Confirmado por el usuario

- Cada plan puede durar un número de días o un número de meses calendario.
- Cada gimnasio debe poder editar sus propios planes para adaptar su oferta, incluidas promociones.
- Se conserva la arquitectura de monolito modular y el aislamiento por workspace.

## Edición y promociones

- El propietario gestiona nombre, precio, moneda, duración y disponibilidad de sus planes. Recepción puede inscribir y registrar cobros; no cambia el catálogo inicialmente.
- Cada modificación del precio o duración crea una versión del plan. Las inscripciones conservan una instantánea de las condiciones contratadas; editar el catálogo no modifica membresías, cargos ni pagos históricos.
- Una promoción es una oferta del gimnasio con nombre, precio final, duración y fechas de disponibilidad opcionales. Puede ofrecer un precio menor o días adicionales sin alterar el plan base ni requerir un motor de cupones.
- Desactivar un plan o una promoción impide nuevas inscripciones, pero conserva el historial.
- Corregir una membresía existente es una operación distinta de editar un plan: requiere permiso del propietario, motivo y auditoría. Una corrección de vigencia no modifica automáticamente cargos o pagos.

## Reglas de negocio aprobadas

1. Vigencia por fechas en la zona horaria del gimnasio. El inicio cuenta como primer día y la fecha final mostrada se disfruta completa. El vencimiento ocurre al comenzar el día siguiente. No se almacenan días restantes.
2. Días: N días desde el inicio, con fin exclusivo inicio + N días. Meses: fin exclusivo calculado desde el inicio sumando N meses calendario y ajustando al último día del mes destino si no existe ese día. La interfaz muestra ambas fechas antes de confirmar. Ejemplo: inicio 31 de enero de 2027, un mes, fin exclusivo 28 de febrero; último día incluido 27 de febrero. Convención aceptada junto con estas reglas.
3. Renovación anticipada: empieza al terminar el período contratado, sin perder días vigentes ni superponer períodos. Si ya venció, empieza en la fecha elegida para la nueva inscripción. Se registran períodos sucesivos; no se reescribe el anterior.
4. Pagos parciales permitidos. La deuda se muestra por separado y no cambia por sí sola las fechas ni bloquea automáticamente la membresía. No se aplican recargos automáticos.
5. Congelaciones mediante propietario, con motivo y rango de días explícito, sin solapamientos ni aplicación retroactiva. Los días congelados no habilitan servicio y se añaden a la vigencia. La coordinación con renovaciones futuras está definida en gym-operations.md.
6. Cancelaciones mediante propietario, con motivo y fecha efectiva. Conservan historial; no producen una devolución o eliminación de deuda automática.
7. Devoluciones manuales mediante propietario, con motivo, vinculadas a pagos existentes y limitadas al importe disponible para devolver. Se registran movimientos de compensación, sin editar ni borrar el pago original. La reversión aumenta el saldo del cargo, según gym-operations.md.
8. Cobros manuales, inicialmente efectivo o transferencia; importes Decimal y moneda explícita. Sin pasarela ni emisión fiscal en este hito.

## Límites de arquitectura

- `gym`: catálogo, versiones/ofertas, inscripciones y períodos de servicio.
- `receivables`: cargos, pagos, aplicaciones y devoluciones. No gestiona la suscripción del gimnasio a MyGym ni comprobantes fiscales.
- Coordinación mediante servicios explícitos y transacciones; cada módulo escribe sus propios modelos.
- Nuevas tablas de negocio con aislamiento por workspace, autorización por operación y RLS usando el rol runtime restringido.
- Las condiciones de una inscripción y su cargo se confirman de forma atómica. Los reintentos no deben duplicar operaciones.
- La UI debe mostrar precio, moneda, duración, fechas y saldo antes de confirmar operaciones.

## Siguiente paso

Especificación técnica: `gym-operations.md`. Plan de ejecución: `../plans/gym-operations.md`.
