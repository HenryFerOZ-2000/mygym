# MyGym Local: entrega inicial Windows

Waitress 3.0.2 sirve el frontend compilado y la API en el mismo origen HTTP,
exclusivamente 127.0.0.1. No requiere servicios Cloud de MyGym.

## Preparar y arrancar

Desde la raíz del checkout preparado (Python 3.13, Node 22, PostgreSQL 17):

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.lock
.\scripts\build-local.ps1
.\scripts\start-local.ps1 -Check
.\scripts\start-local.ps1
```

Abre http://127.0.0.1:8765. Ctrl+C detiene sólo ese proceso. Se puede elegir otro
puerto con `-Port 8767`. PostgreSQL debe estar disponible: el arranque no lo
inicia, provisiona, migra o restaura. No cierra el editor ni servidores de desarrollo.

La configuración privada conserva DJANGO_SECRET_KEY, DB_HOST, DB_PORT, DB_NAME,
DB_USER, DB_PASSWORD y DEPLOYMENT_MODE. Nunca publiques .env o .local.
DB_HOST debe ser 127.0.0.1, DEPLOYMENT_MODE LOCAL; clave de al menos 32 caracteres,
sin marcador inseguro Django. Runtime distinto del propietario de migraciones,
sin superusuario/BYPASSRLS. DEBUG desactivado, cookies HTTP sólo loopback y nombres
de cookies Local separados de desarrollo (los puertos no aíslan cookies).

El preflight valida configuración, index/manifiesto/assets, conexión, ausencia de
migraciones pendientes y RLS forzada. Sólo consulta el estado; no modifica esquema.
Si falla, no escucha y devuelve código distinto de cero. El launcher evita imprimir
excepciones de conexión que podrían contener datos sensibles. Revisa dependencias,
build, configuración privada, disponibilidad DB, migraciones y rol runtime.
Ante migraciones pendientes, coordina respaldo y actualización antes de continuar.
Un puerto ocupado no autoriza a detener su proceso.

`build-local.ps1` genera dist/index.html, assets y .vite/manifest.json. Después de
`npm run build` vuelve a ejecutar build-local: Local requiere el manifiesto.
Node sólo es necesario al compilar. React admite recarga de rutas conocidas;
API/rutas/assets desconocidos mantienen 404. Sólo se sirven index y dist/assets,
sin exponer fuentes, manifiesto, secretos o carpetas del proyecto. HTML no-store,
assets versionados immutable; API conserva no-store/private.

## Verificar sin detener la demo abierta

```powershell
.\scripts\verify.ps1
.\scripts\build-local.ps1
.\.venv\Scripts\python.exe .\scripts\run_local_e2e.py
```

El runner usa mygym_e2e ya preparada, credenciales ficticias privadas y 8766;
ejecuta los recorridos existentes contra Waitress/build y cierra sólo el proceso
que creó. No migra ni crea cuentas. Captura vacía: .local/local-login.png.

## Administrador sólo demo

Las cuentas actuales demo.owner/demo.reception/demo.coach son persistentes;
no se cambian sus contraseñas. Se prepara un único username admin, OWNER de los
dos gimnasios ficticios, sin staff/superuser de Django. No tiene password por defecto.
No se ejecutó la creación de esa cuenta contra la base persistente.

Después de confirmar que la base contiene únicamente la demo ficticia, el
propietario ejecuta en su terminal local:

```powershell
.\.venv\Scripts\python.exe .\backend\manage.py prepare_demo_admin --confirm-fictional
```

Introduce y confirma la contraseña en las dos entradas ocultas. No la pases por
chat, argumentos, variables de entorno ni archivos. El comando exige perfil demo,
base de desarrollo/test/E2E permitida, exactamente los dos workspaces sembrados y
sólo las identidades demo esperadas. Si admin ya existe, rechaza sin modificarlo.
Una contraseña simple se admite únicamente por confirmación de demo ficticia;
los validadores globales permanecen intactos. La identidad se marca mediante un
grupo sin permisos globales; login y sesiones la rechazan cuando DEMO_ENABLED es
false, incluyendo config.settings.local. Usa ese acceso en la demo de desarrollo
http://127.0.0.1:5173, no en el perfil Local. La contraseña sólo se guarda como hash.

## Límites

Servidor asistido en una computadora; aún no instalador comercial, servicio
Windows, LAN, exposición pública, backup/restore o portal Cloud. Backup/restore
es la siguiente etapa, primero sobre bases separadas. Precios/licencias pendientes.
