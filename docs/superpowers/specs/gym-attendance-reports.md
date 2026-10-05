# Asistencia, vencimientos y reportes

Fecha: 2026-10-02. Estado: implementado y verificado en desarrollo; continuación de calidad completada, incluida la mejora de fechas en revisión de entrada. Evidencia actual: 102 pruebas aprobadas en IMPLEMENTATION_LOG.md.

## Objetivo y arquitectura

Completar la operación diaria de Gym: recepción busca un cliente, comprueba su servicio y registra la entrada; el propietario consulta vencimientos y reportes por fecha. Mantener Django/DRF, React/TypeScript y PostgreSQL real en Windows. No incorporar QR, torniquetes, biometría, registro público ni dependencias remotas.

La asistencia pertenece al módulo `gym`. Los reportes de servicio consultan selectores de ese módulo; los de dinero pertenecen a `receivables`. Cada módulo mantiene la escritura de sus modelos. Se reutilizan permisos por workspace, transacciones, auditoría, claves de reintento y RLS.

## Decisiones confirmadas

- Una deuda no bloquea automáticamente una membresía vigente.
- El servicio depende de fechas, congelaciones, cancelaciones y estado de la ficha ya implementados.
- Importes Decimal; nunca sumar monedas distintas.
- Una fecha de fin de membresía es exclusiva internamente. La UI muestra el último día incluido.
- Recepción registra operaciones ordinarias; los ajustes del propietario conservan motivo e historial.

## Reglas de entrada confirmadas

1. Entrada ordinaria con servicio vigente, aunque exista deuda. Vencida/sin servicio actual admite excepción exclusiva del propietario con motivo; incluye un plan cuyo inicio todavía es futuro. Congelada/ficha inactiva no admite entrada, tampoco excepcional.
2. Una visita adicional el mismo día exige confirmación explícita y recuento revisado. Doble clic o reintento nunca crea una visita adicional.

## Asistencia: propuesta técnica

- Buscar por nombre dentro del negocio, búsqueda acotada y paginada. Mostrar nombre, estado del servicio y fecha de término; el saldo se consulta sólo con permiso financiero.
- La revisión muestra último día del período actual, último día cubierto anterior cuando no hay período actual, y próximo inicio contratado. Respeta cancelaciones y excluye períodos cancelados sin servicio. Basta gym.attendance para estos datos mínimos. El historial de anulación muestra autor, instante y motivo.
- Comprobar el estado usando un instante del servidor convertido a la zona horaria del workspace. No confiar en un estado enviado por el navegador.
- Registrar Attendance con workspace, cliente, actor, instante UTC, fecha local y zona horaria capturadas, membresía utilizada cuando exista, modalidad ordinaria/excepción, motivo si corresponde, clave de solicitud y huella. Conservar la decisión de entrada de ese momento aunque se modifique la membresía después.
- Registrar sólo entradas realizadas; no inferir salidas, aforo actual, tiempo de entrenamiento ni acceso físico. Una denegación no cuenta como asistencia.
- Reintento idéntico devuelve el registro existente. Misma clave con datos distintos se rechaza. Bloquear la ficha durante comprobación/registro para coordinar con cambios de membresía y evitar carreras entre operadores.
- Cuando se permita una segunda visita, una previsualización informa cuántas entradas válidas existen ese día; la confirmación exige el recuento visto para detectar una visita registrada simultáneamente.
- Corrección de un registro erróneo mediante anulación del propietario con motivo en un evento separado, sin borrar o sobrescribir el registro original. Una anulación no altera contratos ni dinero y se distingue de una salida.
- RLS forzada para las nuevas tablas y permisos runtime append-only. La guardia de rol las incorpora automáticamente por pertenecer a gym; no introducir una conexión privilegiada en pruebas.

## Vencimientos: propuesta técnica

- Vista operativa por cliente con filtros: próximos a vencer, sin servicio vigente por vencimiento, congelados y programados. Horizonte de próximas caducidades seleccionable, inicialmente 7 días; mostrar explícitamente fecha de referencia y zona horaria.
- Evitar presentar como vencido a un cliente que ya renovó y tiene servicio vigente. Conservar la consulta histórica de cada período en la cuenta existente.
- Una renovación futura contigua extiende el servicio contratado; una separación entre períodos debe mostrarse, no ocultarse sumando días indiscriminadamente.
- Mostrar días calendario hasta el último día de cobertura contigua. Los días de servicio descontando congelaciones se consultan en la cuenta existente del cliente; no mezclar ambos contadores ni almacenarlos.
- Listado paginado con orden estable por fecha relevante/cliente/UUID, sin cargar todos los expedientes en el navegador.

## Reportes: definiciones

### Asistencia

Elegir fecha inicial/final inclusivas. El reporte utiliza la fecha local guardada en cada entrada. Mostrar entradas válidas, clientes distintos que asistieron, entradas por excepción y anulaciones separadas. Una segunda visita es otra entrada, pero no otro cliente distinto. No calcular una tasa de asistencia sin un denominador de población definido.

### Dinero

El período se interpreta en la zona horaria actual del negocio: desde el inicio local de la primera fecha hasta el inicio local del día siguiente a la última. Convertir ambos límites a instantes UTC; no asumir que todos los días tienen exactamente 24 horas.

Por moneda: pagos registrados en el período, devoluciones registradas en el período y movimiento neto = pagos - devoluciones. Una devolución de un pago anterior al período se incluye por la fecha de devolución. Etiquetar los datos como registros manuales; no afirmar conciliación bancaria, ingresos contables, utilidad ni facturación fiscal.

Saldo pendiente: foto actual de cargos menos aplicaciones más devoluciones, indicando el instante de consulta. No etiquetarlo como saldo histórico al cierre del rango. Incluir cargos de clientes inactivos/cancelados que siguen adeudados. No multiplicar importes por joins con múltiples aplicaciones o devoluciones.

### Consistencia y límites

Lecturas de cada reporte con una instantánea consistente de PostgreSQL para que sus totales no mezclen estados antes/después de una operación concurrente. Consultas agregadas y paginación del detalle; sin transferir toda la base al frontend. Rango máximo inicial 366 días por consulta y campos desconocidos rechazados. Reportes en pantalla, sin exportación de archivos en este hito.

Cada reporte utiliza una sola sentencia SQL parametrizada: los totales y el recuento/página comparten la instantánea de esa sentencia PostgreSQL. No exige cambiar el aislamiento de toda la petición. El resumen de asistencia aplica las anulaciones actuales a la fecha local original de cada entrada.

## Permisos

- `gym.attendance`: OWNER y RECEPTION consultan estado mínimo necesario y registran entradas. Excepciones y anulaciones sólo OWNER.
- `gym.manage`: OWNER y RECEPTION consultan vencimientos, conforme al módulo actual.
- `gym.reports`: sólo OWNER consulta el resumen agregado de asistencia.
- `receivables.reports` y `receivables.manage`: sólo OWNER consulta el resumen financiero y saldos. El cobro cotidiano de recepción conserva su permiso actual.
- Cada consulta valida rol/acceso/capacidad; no se concede acceso por conocer una URL. Capacidades independientes: un reporte financiero no exige acceso al catálogo Gym.

## Pruebas previstas

- Membresía vigente con deuda, cambio de día local, primer/último día, congelación/cancelación y ficha inactiva.
- Reintento y clave reutilizada, doble clic, operadores concurrentes, segunda visita según regla elegida, anulación y auditoría atómicas.
- Cliente ajeno, capacidad revocada, rol coach denegado y acceso SQL sin contexto rechazado.
- Renovación vigente no aparece como cliente vencido; congelaciones y períodos futuros no producen contadores duplicados.
- Dos monedas, pago parcial, varias aplicaciones, varias devoluciones, devolución dentro del rango de un pago anterior, límites UTC/local y cambio horario.
- Totales agregados consistentes con movimientos concurrentes; saldo actual incluye contratos cancelados.
- Navegador: buscar → revisar → registrar → ver historial; permiso revocado con formulario abierto; reportes vacíos/con datos; escritorio/móvil.

## Seguimiento

Contratos en docs/api/openapi.yaml; evidencia y decisiones en docs/operations/IMPLEMENTATION_LOG.md. Instalación comercial, exportaciones y control físico de acceso quedan fuera de este hito.
