# Decisión: un producto, dos líneas, dos despliegues

Backend Django 5.2 LTS/Python 3.13/DRF, PostgreSQL 17 y frontend React/TypeScript/Vite.
Un repositorio y monolito modular. Gym/Coach pertenecen al workspace; DEPLOYMENT_MODE a la instalación.
Local y Cloud comparten dominio. Local básico no depende de correo, SaaS ni almacenamiento remoto.
Se crean identity, workspaces, clients y audit en el hito 1. tenancy es infraestructura de aislamiento.
Mapa futuro: gym, coaching, training, nutrition, progress, media, documents, receivables,
platform_billing, licensing, invoicing y notifications. No crear módulos vacíos.
User identifica acceso; ClientRecord es un expediente privado de un negocio. Una cuenta puede acceder a varios negocios sin compartir expedientes.
Cada petición lleva workspace en URL, valida acceso/capacidad/rol y abre transacción con contexto RLS.
Identidad y descubrimiento son excepciones a RLS, con selectores restringidos. RLS inicial sólo protege clients y audit.
Sesiones Django, CSRF incluso login, proxy Vite para desarrollo loopback. Sin tokens ni fichas en localStorage.
Gym operativo añade gym (catálogo versionado y vigencia), receivables (dinero) y utilidades shared sin modelos propios. Receivables no depende del módulo gym.
Asistencia pertenece a gym: entrada y anulación son eventos append-only con RLS forzada. Sus servicios usan el mismo bloqueo de cliente que los cambios de membresía; una clave de solicitud identifica cada operación. Los selectores de vencimientos/asistencia están en gym y el agregado monetario en receivables; cada reporte usa una sentencia SQL para compartir instantánea entre totales y página.
Producción, instalador comercial, recuperación offline, MFA, fotos y facturación quedan para sus hitos.
