# Ensayo de respaldo y recuperación Local

## Alcance aprobado y resultado actual

El usuario aprobó preparar el flujo con datos ficticios antes de decidir ubicación y permisos para datos reales. Este incremento entrega protección e inspección de un archivo de **sólo esquema** de `mygym_test`, guardias y pruebas de recuperación. **No entrega aún un respaldo completo ni una restauración de negocio de extremo a extremo.** No existe botón que sugiera que esas operaciones están disponibles.

No se modifica `.env`, la aplicación activa, cuentas ni roles PostgreSQL. No se exportan filas, hashes de autenticación o sesiones. No se usa el administrador del clúster para superar RLS.

## Ejecutar lo verificado en Windows

Desde la raíz del checkout, con PostgreSQL existente disponible:

```powershell
.\scripts\check-recovery.ps1 -Fixture
```

Usa Python del proyecto y los clientes PostgreSQL 17 ya instalados. Produce un archivo único cifrado bajo `.local/recovery-fixtures`, lo descifra en memoria y comprueba su legibilidad con `pg_restore --list`. No ejecuta SQL de restauración. No escribe el dump sin cifrar a disco, no imprime SQL, credenciales, contenido, huellas ni listas de usuarios. El archivo queda ignorado por Git.

```powershell
.\scripts\check-recovery.ps1
```

Comprueba el runtime real y termina bloqueado (Python: código 2; wrapper PowerShell: error explícito) porque no es una identidad de respaldo integral. Es un resultado esperado, no una restauración fallida. No lee filas ni cambia roles para resolverlo.

## Protección y límites

El sobre versión 1 encapsula metadatos y archivo custom PostgreSQL 17 bajo DPAPI con alcance del **usuario de Windows**, interfaz prohibida y sin `LOCAL_MACHINE`. Integra una comprobación adicional del contenido descifrado. Detecta corrupción y versiones no admitidas; publicación atómica sin sobrescribir archivos existentes. Tamaño máximo del dump: 64 MiB para este ensayo, procesado en memoria.

DPAPI depende normalmente del usuario y equipo originales: **esto no es una copia portable ni una solución frente a pérdida del equipo/perfil Windows**. No se promete recuperación comercial. Antes de datos reales se decidirán cifrado portable, recuperación de claves, destino protegido, retención, volumen de datos y medios privados. No hay nuevas dependencias, servicios ni costos.

## Bloqueo de permisos confirmado

La lectura de catálogo encontró runtime y migrador sin superusuario, BYPASSRLS, CREATEDB ni CREATEROLE; sólo `mygym_admin` tiene privilegios amplios. Runtime y migrador no pueden exportar íntegramente tablas con RLS forzado. `--enable-row-security` no resuelve la integridad: permitiría una copia parcial según contexto y queda excluido. No se concedió BYPASSRLS ni se creó credencial alguna.

La siguiente prueba completa necesita aprobación específica y preparación supervisada de:

1. Una identidad dedicada, no superusuario, para lectura integral del **origen ficticio**, sin creación de roles/bases y sin escrituras; su acceso de lectura y BYPASSRLS serían un cambio de seguridad que aún no se ha autorizado.
2. Una base nueva y vacía `mygym_restore_test_<identificador>` y una identidad de recuperación limitada a ese destino. No reutilizar `mygym_dev`, `mygym_test` o `mygym_e2e` como destino.
3. Propiedad de esquema, permisos y políticas del candidato compatibles con el migrador y runtime restringido; se preparan sólo en el destino de ensayo, nunca mediante cambios globales a los roles existentes.

Las credenciales se introducirán mediante un canal local privado acordado, nunca en argumentos, Git o evidencias. Los builders de comandos y guardias son componentes internos de la futura ejecución; **no hay comando de restauración expuesto en este incremento**.

## Protocolo de restauración diseñado, todavía pendiente de prueba completa

- Mantener origen intacto y aplicación apuntando a él. Verificar identidad de origen/destino, versión cliente/servidor y migraciones soportadas; bloquear destinos ocupados o con otras conexiones sin terminar sesiones ajenas.
- Exportar custom completo y consistente con `pg_dump`, sin roles globales, permisos, secretos de configuración ni datos de `django_session`. Sólo admitir archivos confiables de la instalación: un dump puede ejecutar código al restaurarse.
- Descifrar y validar protección, versión y legibilidad antes de conectar al destino. Mantener exclusividad operativa del candidato durante preflight/restore; una comprobación de catálogo aislada no evita carreras.
- Restaurar con `pg_restore --single-transaction --exit-on-error`, sin `--clean`, `--create`, desactivar triggers o RLS. El rollback de PostgreSQL ante fallo de restore debe probarse realmente cuando se habilite la identidad de recuperación.
- Validar en el candidato: contrato/migraciones, constraints, integridad y cantidades por workspace contra el inventario del origen; sesiones vacías; runtime sin propiedad/superusuario/bypass; RLS ENABLE/FORCE y ausencia de lecturas sin contexto, cruces y contexto residual. El helper de purga de sesiones exige transacción y sus pruebas demuestran rollback con fixtures reales.
- Un fallo deja el candidato sin activar, conservando origen y archivo cifrado. No se afirma rollback de una activación que no se ha implementado. Cambiar la configuración de la aplicación requiere aprobación separada, incluso después de pasar la validación; conservar la anterior para volver atrás.

## Evidencia y siguientes brechas

Ver registro de implementación para resultados actuales. Las pruebas de envelope usan bytes ficticios; el comando `-Fixture` usa un archivo PostgreSQL real de sólo esquema. Las pruebas de sesiones/RLS ejecutan SQL contra `mygym_test` con runtime restringido y rollback de pytest. No se han demostrado aún exportación/restauración integral, permisos del candidato, integridad de filas después de restore o recuperación en otro Windows. Prioridad: permisos acotados y destino nuevo; después prueba completa y cifrado portable; luego UX de operador, retención y recuperación ante fallos.

Fuentes oficiales: [pg_dump PostgreSQL 17](https://www.postgresql.org/docs/17/app-pgdump.html), [pg_restore PostgreSQL 17](https://www.postgresql.org/docs/17/app-pgrestore.html), [CryptProtectData](https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata), [CryptUnprotectData](https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptunprotectdata).
