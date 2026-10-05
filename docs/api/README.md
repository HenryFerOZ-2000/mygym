# Contrato API del núcleo

OpenAPI generado en `openapi.yaml` desde vistas/serializadores y contrato común.
Regenerar con `python backend/manage.py spectacular --file docs/api/openapi.yaml --validate --fail-on-warn` usando Python del entorno virtual.

Todas las rutas llevan `/api/v1/` y barra final. Cuerpos JSON, tamaño máximo 16 KiB.
GET auth/csrf/ devuelve csrfToken y establece cookie. POST login necesita esa cookie y X-CSRFToken,
incluso sin sesión. Tras login, obtener token de nuevo porque Django lo rota.
POST logout necesita sesión y CSRF. La UI reconcilia /auth/me/ si la sesión ya expiró.
Sesión HttpOnly, sin tokens localStorage. Respuestas privadas `Cache-Control: no-store, private`.

Error común:

```json
{"error":{"code":"validation_error","message":"Revisa los datos de la solicitud.","fields":{"full_name":["Este campo es requerido."]}}}
```

400: validación, cuerpo/UUID inválido, credenciales incorrectas o bloqueo temporal genérico.
403: sin sesión, CSRF inválido o rol/capacidad insuficiente.
404: workspace no autorizado/inexistente, ficha ajena o página fuera del listado.
405: método no habilitado, incluido DELETE. 415: contenido no JSON.
Health sólo `{"status":"ok"}`: no expone detalles de infraestructura ni garantiza readiness de DB.

Fichas: full_name requerido <=200, phone opcional <=32, email opcional <=254, is_active booleano.
PATCH parcial; id, workspace, user, roles y demás campos no declarados se rechazan.
Paginación page/page_size: 25 por defecto, máximo 100, enteros positivos, orden created_at/id ascendente.
Las fichas conservan su listado básico; asistencia añade búsqueda por nombre. No hay exportación en este hito. Una capacidad habilitada no reemplaza permisos.

Gym añade catálogo bajo `gym/plans/` y cuenta bajo `clients/{client_id}/gym/` y `clients/{client_id}/receivables/` dentro del workspace. OpenAPI describe las 27 rutas disponibles.
Las páginas nuevas devuelven `next`/`previous` como número de página o null (las fichas conservan sus URLs). Todas mantienen límite 25/100.
Inscripciones/ajustes/pagos/devoluciones requieren UUID `request_id`: reintento idéntico recupera registro; misma clave con otro contenido responde 400. Edición de catálogo requiere `expected_version`.
La API financiera admite hasta 50 aplicaciones a cargos por pago, con misma moneda y cliente; importes decimales de dos posiciones. Una devolución revierte aplicaciones y restaura saldo, sin transferir dinero.

Asistencia: `attendance/clients/` busca fichas mínimas por `q`; `clients/{id}/attendance/preview/` devuelve estado/fecha local/recuento; POST `clients/{id}/attendance/` exige `request_id`, `expected_date`, `expected_count`, `confirm_repeat` para visitas adicionales, y `exception`/`reason` sólo para propietario. `attendance/` lista por `q`/`date`; POST `attendance/{id}/void/` anula con motivo. No se borra ni sobrescribe el registro original.

`gym/expiries/` filtra `status`, `horizon` (1–90), `q`, `page` y `page_size`. Una fila por cliente y cobertura de renovaciones contiguas; fechas de fin exclusivas, `last_day` incluido. `reports/attendance/` y `reports/financial/` requieren `from_date`/`to_date` inclusivos, máximo 366 días. El saldo financiero es actual (`outstanding_now`, instante `as_of`), no saldo al cierre del rango. Cada reporte obtiene todos sus agregados en una sola sentencia PostgreSQL.

La previsualización de asistencia incluye `last_day` del período actual (incluido), `previous_last_day` y `next_start`, todos anulables. Respeta cancelaciones y excluye períodos de duración efectiva cero; no confundir last_day del período con coverage_end de renovaciones contiguas del reporte. Las entradas incluyen `void_actor` y `voided_at`, nulos hasta su anulación.
