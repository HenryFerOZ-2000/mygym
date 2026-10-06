# MyGym

Desarrollo: login, espacios autorizados, fichas de clientes, planes/promociones editables,
membresías, cobros manuales, asistencia y reportes, auditoría transaccional y aislamiento PostgreSQL RLS.
Una base de código para Gym/Coach y Local/Cloud.
El producto comercial y los siguientes módulos siguen el roadmap de [contexto](docs/PROJECT_CONTEXT.md).

## Abrir el proyecto preparado

Desde PowerShell en esta carpeta:

```powershell
.\scripts\start-dev.ps1
```

Abre **http://127.0.0.1:5173**. Usuario `demo.owner`.
La contraseña aleatoria está en `.local\mygym_dev-demo.json`: ábrelo localmente, no lo pegues en chats ni Git.
También existen `demo.reception` y `demo.coach`, con la contraseña demo inicial; coach tiene denegada la gestión de fichas.
Gym Titan y Gym Aurora contienen únicamente personas ficticias. No introduzcas clientes reales.

```powershell
.\scripts\stop-dev.ps1
# Para detener también PostgreSQL:
.\scripts\stop-dev.ps1 -Database
```

El arranque usa ventanas ocultas, comprueba puertos y no configura inicio automático.
PostgreSQL escucha sólo en 127.0.0.1:55432; backend en 8000 y Vite en 5173.

## Planes, membresías y cobros

1. Entra en Gym Titan o Gym Aurora y abre **Planes y promociones**. El propietario crea o edita precio, duración en días/meses, disponibilidad y promociones.
2. En **Clientes**, abre **Membresías y cobros**. Selecciona un plan, revisa las fechas y el importe y confirma la inscripción. Se crea un cargo, todavía sin pago.
3. Usa **Registrar abono** cuando recibas efectivo o transferencia. Los pagos parciales dejan un saldo visible.
4. El propietario puede congelar, corregir fechas, cancelar o registrar devoluciones con motivo. Cada acción conserva historial.

Editar un plan no cambia lo contratado anteriormente. Una congelación extiende la vigencia y desplaza períodos futuros compatibles. Cancelar no elimina la deuda. Devolver dinero vuelve a aumentar el saldo del cargo; MyGym sólo registra la devolución realizada fuera de la aplicación.

Recepción puede inscribir y cobrar; no modifica catálogo ni autoriza ajustes/devoluciones. La zona horaria del gimnasio determina las fechas. Los meses calendario pueden tener distinta duración: la previsualización muestra el último día incluido y la fecha de vencimiento.

Guía y límites: [operación Gym](docs/operations/gym.md). [Diseño del módulo](docs/superpowers/specs/gym-operations.md).

## Asistencia, vencimientos y reportes

- **Asistencia** permite buscar un cliente, revisar el servicio y confirmar su entrada. Membresía vigente permite entrar aunque tenga deuda; vencida o sin servicio actual exige autorización del propietario con motivo. Congelada o ficha inactiva bloquea la entrada.
- La revisión muestra las fechas del período actual, la cobertura anterior y el siguiente inicio según corresponda. Las anulaciones muestran quién las realizó, cuándo y por qué. Las consultas fallidas permiten reintentar sin recargar.
- Una segunda visita del día requiere confirmación explícita. Los reintentos no duplican el registro. El propietario puede anular una entrada equivocada con motivo; el historial se conserva.
- **Vencimientos y reportes** muestra cobertura y renovaciones por cliente. El propietario consulta entradas válidas, clientes distintos y movimientos manuales por fechas/moneda. El saldo pendiente se identifica como actual, separado del período seleccionado.

Las capacidades son independientes por negocio. [Reglas y alcance](docs/superpowers/specs/gym-attendance-reports.md).
Al elegir un negocio se abre una función habilitada para ese usuario; los menús respetan sus capacidades. Los permisos siempre se validan también en la API.

## Preparar otra instalación de desarrollo Windows

Requisitos: Python 3.13, Node 22 compatible (>=22.12), npm y Git. No requiere Docker, WSL ni servicios Cloud.
Se probaron Python 3.13.4, Node 22.16.0 y PostgreSQL 17.11. Revisar actualizaciones de parche antes de producción.

```powershell
.\scripts\setup-dev.ps1
```

Descarga dependencias bloqueadas, PostgreSQL oficial de EDB (SHA256 fijado) y Chromium para pruebas.
Crea `.venv`, `frontend/node_modules`, `.local` privado, `.env`, tres bases exclusivas y roles distintos.
No modifica PATH, firewall, políticas globales ni instala PostgreSQL como servicio Windows.
La descarga inicial necesita Internet; la operación local del recorrido no requiere servicios remotos de MyGym.
Si tu política impide scripts, usa los comandos manuales de [desarrollo Windows](docs/operations/windows-development.md), sin cambiarla globalmente.

## Verificar

Detén antes el backend/frontend de desarrollo para liberar los puertos de las pruebas de navegador:

```powershell
.\scripts\stop-dev.ps1
.\scripts\verify.ps1 -Browser
```

Las pruebas usan PostgreSQL real en `mygym_test`; Playwright usa `mygym_e2e`.
El runtime carece de privilegios de propietario, superusuario y BYPASSRLS. Migraciones usan otro rol.
Resultados y limitaciones: [registro](docs/operations/IMPLEMENTATION_LOG.md).

## Estructura y documentación

- `backend/modules`: identity, workspaces, clients, audit, gym, receivables y utilidades shared. Modelos, políticas, consultas, servicios y API separados.
- `backend/tenancy`: contexto transaccional y verificación del rol runtime.
- `frontend/src`: app, features y shared; HTTP centralizado y caché por identidad/workspace.
- [Arquitectura](docs/architecture/001-modular-monolith.md), [permisos/RLS](docs/security/permissions-and-rls.md).
- [Especificación](docs/superpowers/specs/core.md), [plan](docs/superpowers/plans/core.md), [OpenAPI](docs/api/openapi.yaml).

No es un instalador comercial ni un despliegue productivo. `runserver` y Vite son exclusivamente desarrollo loopback.
No incluye facturación fiscal, pasarela, cobro automático, fotos, portal de clientes, MFA ni recuperación comercial.
Código versionado en https://github.com/HenryFerOZ-2000/mygym. Sin despliegue público.

## Servidor Local inicial

```powershell
.\scripts\build-local.ps1
.\scripts\start-local.ps1 -Check
.\scripts\start-local.ps1
```

Abre **http://127.0.0.1:8765**; detén con `Ctrl+C`. Waitress sirve React compilado y API. El arranque verifica configuración, build, migraciones y RLS sin modificar esquema. [Preparación, demo y límites](docs/operations/local-delivery.md).

## Ensayo protegido de recuperacion (preparacion)

```powershell
.\scripts\check-recovery.ps1 -Fixture
```

Protege e inspecciona un archivo de solo esquema de mygym_test con PostgreSQL 17 y el usuario Windows actual. No exporta filas ni restaura una base. Sin -Fixture el preflight rechaza el runtime actual: faltan identidades de respaldo/recuperacion aprobadas y un destino nuevo. No es un backup portable ni recuperacion comercial. [Alcance, comandos, permisos pendientes y protocolo](docs/operations/backup-recovery.md).
