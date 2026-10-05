# Desarrollo Windows

## Entorno y persistencia

Python 3.13.4 y Node 22.16.0 detectados; dependencias exactas en requirements.lock/package-lock.json.
PostgreSQL 17.11 extraído de archivo oficial EDB, sólo bin/lib/share en `.local/pg17`.
`.local/pgdata` almacena bases. No borrarlo para reinstalar código.
`.local/database.json` contiene claves privadas de administración/migración/runtime; `.env` sólo runtime.
ACL Windows restringe `.local` y `.env` al usuario actual y SYSTEM. No equivale a cifrado de disco.
No respaldos comerciales ni recuperación probada aún; sólo datos ficticios. Copiar PDF no sería respaldo.

Tres bases separadas: mygym_dev, mygym_test, mygym_e2e. Migrator es propietario sin superusuario;
runtime tiene permisos CRUD necesarios, sin CREATE de esquema, sin propiedad ni membresía migrator.
Runtime sólo lee django_migrations (necesario para comprobación de arranque), no puede modificarlo.
No puede borrar fichas ni actualizar/borrar auditoría. Pruebas de Django usan rollback, no flush privilegiado.

## Comandos manuales desde la raíz

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.lock
.\.venv\Scripts\python.exe scripts\download_postgres.py
.\.venv\Scripts\python.exe scripts\provision_local.py
.\.venv\Scripts\python.exe scripts\migrate_local.py mygym_dev
.\.venv\Scripts\python.exe scripts\migrate_local.py mygym_test
.\.venv\Scripts\python.exe scripts\migrate_local.py mygym_e2e
.\.venv\Scripts\python.exe scripts\seed_local.py mygym_dev
.\.venv\Scripts\python.exe scripts\seed_local.py mygym_e2e
```

Frontend, desde `frontend`:

```powershell
npm.cmd ci
npx.cmd playwright install chromium
npm.cmd run dev
```

Backend, en otra consola desde raíz:

```powershell
.\.venv\Scripts\python.exe backend\manage.py runserver 127.0.0.1:8000 --noreload
```

No activar `.venv` es necesario: invocar su Python evita cambiar políticas PowerShell.
Logs locales en `.local`; no compartirlos sin revisar. No contienen cuerpos intencionalmente.
Las credenciales demo no se restablecen al reejecutar seed. Si cambias una contraseña manualmente,
el archivo demo inicial puede quedar obsoleto: no es un mecanismo de recuperación.

## Pruebas y contrato

`verify.ps1 -Browser`: pip check, Ruff, Django check, migraciones pendientes, OpenAPI, pytest,
ESLint, Vitest, TypeScript/build y Playwright. Sale con error ante cualquier fallo.
`run_e2e.py` inicia backend temporal con mygym_e2e y lo detiene incluso si falla una prueba.
Chromium/Vite se ejecutan localmente; no se usan servicios de correo, CDN o autenticación externa.
El runner genera datos ficticios adicionales en mygym_e2e; nunca afecta a mygym_dev.

## Límites

HTTP y cookies sin Secure se permiten sólo en configuración development/test y acceso loopback.
base.py mantiene cookies Secure; todavía faltan configuración/validación de producción, HTTPS confiable,
respaldo/restauración, recuperación de acceso, empaquetado y arranque automático.
No habilitar LAN, router, CORS universal ni usar runserver/Vite en producción.
