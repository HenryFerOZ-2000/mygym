Actúa como arquitecto de software y desarrollador full-stack para MyGym. Trabajarás conmigo mediante Codex, sobre la carpeta de proyecto autorizada. Responde en español, utiliza nombres de código coherentes en inglés y explica las decisiones importantes sin asumir que conozco todos los detalles de infraestructura.

Este mensaje contiene el contexto completo del producto. No necesitas acceder a conversaciones anteriores ni a un ZIP para comprenderlo. Si existen documentos o código en la carpeta, revísalos y reconcílialos con este contexto sin sobrescribir trabajo existente.

IMPORTANTE: conocer toda la visión NO autoriza a implementarla entera de una vez. El primer encargo, definido al final, es diagnóstico y planificación. La implementación se realizará por hitos aprobados y verificados.

# 1. CONTEXTO DEL NEGOCIO

Soy Henry y voy a desarrollar este proyecto con un amigo. Queremos construir un producto propio, mantenible y comercializable para gimnasios y entrenadores. El cliente piloto ha pedido un sistema local para registrar clientes, controlar inscripciones, vigencias y pagos.

No queremos desarrollar un programa aislado para ese gimnasio y después rehacerlo como una web. Queremos una plataforma reutilizable que pueda venderse a múltiples negocios.

Nombre provisional: MyGym. Un dominio como mygym.com es solo un ejemplo: no está contratado, no se ha verificado su disponibilidad y no debes comprarlo.

La visión es una plataforma centralizada con dos líneas funcionales, Gym y Coach, y dos modalidades de instalación, Cloud y Local. La primera instalación comercial será para el gimnasio piloto; el núcleo también deberá demostrar aislamiento entre organizaciones ficticias.

El equipo es de dos desarrolladores y trabajaremos con Codex desde Windows. Prioriza una arquitectura clara y un costo inicial bajo, sin sacrificar aislamiento de datos ni crear infraestructura innecesaria.

# 2. LAS CUATRO OFERTAS DEL MISMO PRODUCTO

## MyGym Gym Cloud

Un gimnasio crea su negocio dentro de MyGym y paga una suscripción a nuestra plataforma. Administra empleados, coaches autorizados, clientes, membresías, vencimientos, cobros, asistencia y reportes. Puede habilitar un portal sencillo para sus clientes.

Cada gimnasio conserva su información separada de otros negocios. Puede haber varias sedes posteriormente; no necesitamos construir su administración completa desde el primer hito.

## MyGym Gym Local

La gestión se instala en una computadora o servidor del gimnasio y funciona sin servicios Cloud obligatorios. Se venderá inicialmente como licencia de pago único, con condiciones separadas para instalación, soporte y actualizaciones.

El personal autorizado utiliza el sistema desde un navegador. Una red local con varias computadoras será una posibilidad de despliegue, no una autorización para exponer el servidor a Internet.

En la edición inicial Local no habrá portal para los clientes finales. Podrá incorporar funciones de coach dentro del gimnasio según los módulos contratados.

## MyGym Coach Cloud

Un entrenador independiente tiene un workspace y paga su suscripción a MyGym. Gestiona clientes, rutinas personalizadas, planes alimenticios, mediciones, fotografías de progreso, historial, cobros y seguimiento.

Sus clientes pueden entrar para consultar planes y registrar información permitida: entrenamiento realizado, cargas, repeticiones, medidas y fotografías cuando corresponda.

## MyGym Coach Local

El entrenador utiliza una herramienta privada en su computadora. Él registra y administra las fichas, planes, mediciones, fotos y seguimiento. Sus clientes no tendrán cuenta de acceso en esta primera edición.

Puede exportar rutinas, alimentación y reportes a PDF, guardarlos en su equipo y compartirlos manualmente por Drive, WhatsApp o correo. Generar el archivo funciona sin Internet; subirlo o enviarlo requiere conexión.

Conclusión: una plataforma y una base de código; dos líneas funcionales y dos modalidades de despliegue. No crear cuatro aplicaciones, cuatro repositorios ni cuatro ramas permanentes.

# 3. EXPERIENCIA DEL CLIENTE FINAL EN CLOUD

## Cliente de gimnasio

El gimnasio registra una ficha y puede invitar a esa persona al portal. La invitación utiliza un enlace temporal y de un solo uso para verificar y establecer el acceso; no envía una contraseña fija por correo.

El cliente puede consultar su plan, fecha de inicio, vencimiento, días restantes, estado, historial propio de pagos y asistencia según permisos. También puede consultar rutinas genéricas publicadas por el gimnasio y una biblioteca sencilla de ejercicios.

Cada ejercicio puede incluir nombre, instrucciones, series, repeticiones, descanso y contenido visual autorizado. La gestión simple de un gimnasio no debe convertirse obligatoriamente en entrenamiento personalizado.

Vencer una membresía no elimina la identidad del cliente ni su historial. Debemos distinguir inicio de sesión, vigencia de membresía y acceso a funciones. Las restricciones comerciales detalladas se decidirán antes de implementar ese flujo.

## Cliente de coach

Puede ver sus rutinas asignadas, plan alimenticio publicado, indicaciones, medidas y evolución. Puede registrar cada serie realizada: carga utilizada, unidad, repeticiones, fecha y observaciones permitidas.

Debe distinguirse lo prescrito por el coach de lo realizado por el cliente. Por ejemplo, una rutina puede indicar 3 series de 10 y el cliente registrar cargas y repeticiones distintas para cada serie.

El coach consulta ese historial para hacer seguimiento. Las fotografías de progreso son opcionales, especialmente protegidas y no se habilitarán antes de completar sus controles de seguridad.

El cliente es un usuario del portal, no un tercer comprador obligatorio de MyGym. Inicialmente su acceso procede de la relación autorizada con un gimnasio o coach.

# 4. IDENTIDAD ÚNICA SIN COMPARTIR EXPEDIENTES

Separar estos conceptos:

- User: identidad de inicio de sesión.
- Workspace: negocio, como un gimnasio o un coach independiente.
- WorkspaceAccess: relación de un operador con un negocio, su rol y estado.
- ClientRecord: expediente de una persona dentro de un negocio, con cuenta vinculada opcional.
- GymMembership: servicio de gimnasio contratado y su vigencia.
- CoachAssignment/CoachingRelationship: relación de atención y sus permisos.

Una ficha local puede no tener correo ni usuario. Un registro de cliente no significa automáticamente que pueda iniciar sesión.

Una persona puede pertenecer a un gimnasio, ser cliente de un coach y trabajar como entrenador en otro negocio, usando una identidad Cloud. Los roles se asignan por workspace, no mediante un único tipo global de usuario.

Ejemplo: Carlos tiene una membresía en Gym Titan y entrenamiento con Coach Henry. Puede consultar ambos contextos, pero Gym Titan no recibe automáticamente las fotos o planes privados de Coach Henry.

Ejemplo: un coach empleado de Gym Titan y propietario de su negocio personal cambia de workspace. No copia ni hereda expedientes del gimnasio en su negocio personal.

Coincidir en nombre o correo no autoriza a fusionar expedientes ni revelar relaciones con otros negocios. Vincular una cuenta exige un flujo verificado. Mantener un contexto independiente por petición y por pestaña.

# 5. MODELO COMERCIAL Y FUNCIONES CONTRATADAS

Distinguir cuatro relaciones económicas:

1. Gimnasio paga a MyGym por la plataforma Cloud.
2. Coach paga a MyGym por la plataforma Cloud.
3. Cliente paga al gimnasio su membresía.
4. Cliente paga al coach por entrenamiento.

En Local, el comprador paga la licencia del software; sus propios clientes siguen pagando sus servicios normalmente. Desactivar la suscripción SaaS en Local no elimina el módulo de cobros del negocio.

Los precios de venta y límites comerciales NO están cerrados. Planes por número de clientes, usuarios, sedes o módulos son posibilidades, no requisitos con números definitivos. No prometer clientes ilimitados, soporte perpetuo ni actualizaciones gratuitas para siempre.

Separar configuración de despliegue, producto, capacidades y autorización:

- DEPLOYMENT_MODE es una configuración de instalación.
- Gym/Coach y los módulos habilitados pertenecen al workspace.
- Roles y permisos pertenecen a sus relaciones de acceso.
- Licencias y suscripciones determinan capacidades, no sustituyen permisos.

No usar PRODUCT=GYM como variable global de una nube que atiende Gym y Coach simultáneamente. Ocultar un menú no protege su API.

# 6. ENTORNO DE DESARROLLO: WINDOWS

Desarrollaremos inicialmente con Windows nativo y PowerShell. No exigir Linux, WSL, Docker, formateo, arranque dual o una máquina virtual para empezar.

Cloud podrá desplegarse en Linux posteriormente. Un servidor Linux remoto no implica que la computadora del desarrollador también deba usar Linux.

Verifica el entorno al que realmente tienes acceso. No confundir tu sandbox o sesión remota con mi Windows físico. Si solo puedes comprobar el entorno de Codex, dilo; no inventes versiones instaladas en mi computadora.

Comprobar Python, Node.js/npm, Git y PostgreSQL sin instalar, desinstalar ni modificar el sistema durante el diagnóstico. No imprimir secretos ni cadenas completas de conexión.

Mantener entornos virtuales y dependencias del proyecto aislados. No modificar PATH, políticas globales de PowerShell, servicios, firewall o componentes de otros proyectos sin autorización específica.

Una instalación de desarrollo no equivale al producto MyGym Local comercial. El instalador, arranque automático, actualizaciones, recuperación y seguridad de red se validarán en una etapa distinta.

# 7. TECNOLOGÍAS ACORDADAS

Usar como base:

- Frontend: React + TypeScript + Vite.
- Navegación: React Router.
- Consultas y caché: TanStack Query.
- Interfaz: Tailwind CSS y componentes reutilizables.
- Backend: Python 3.13 + Django 5.2 LTS + Django REST Framework compatible.
- Base de datos: PostgreSQL 17 real, también para pruebas de integración.
- API: REST con prefijo /api/v1/ y contrato OpenAPI.
- Archivos: interfaz de almacenamiento Django, R2 privado en Cloud y disco privado en Local.
- PDF: plantillas controladas y WeasyPrint, verificando requisitos nativos de Windows cuando corresponda.
- Tests: pytest/pytest-django, Vitest y Playwright.
- Entrega: Git, revisión de cambios, verificaciones automatizadas y dependencias fijadas.

Estas son versiones mayores propuestas. Comprobar compatibilidad y parches en documentación oficial antes de fijarlos. No usar latest indiscriminadamente ni cambiar versiones mayores o tecnologías silenciosamente. Elegir una versión soportada de Node compatible con las dependencias reales.

No sustituir PostgreSQL por SQLite para aparentar que funciona. No añadir Firebase, MongoDB, autenticación SaaS, Next.js, microservicios o una aplicación móvil solo por preferencia del agente.

Para Cloud se considera Linux con un servidor apropiado, como Nginx/Gunicorn, y contenedores reproducibles. No trasladar automáticamente ese despliegue a Windows: un servidor nativo Local deberá ser compatible, por ejemplo evaluando Waitress. Nunca entregar runserver o el servidor Vite de desarrollo como producción.

Las tareas externas pueden comenzar con outbox persistente y un comando ejecutado periódicamente. Una cola y workers dedicados, como Celery con un broker compatible, se incorporan cuando exista una necesidad concreta. No hacerlos dependencias obligatorias del primer hito.

# 8. ARQUITECTURA MODULAR

Construir un monolito modular: una aplicación backend con límites claros, no un servidor por módulo ni toda la lógica mezclada en vistas.

Mapa de responsabilidades:

- identity: cuentas, sesiones, invitaciones y recuperación.
- workspaces: negocios, accesos, roles, sedes y capacidades.
- clients: fichas de clientes por negocio.
- gym: planes, membresías, renovaciones y asistencia.
- coaching: relaciones coach-cliente y asignaciones.
- training: ejercicios, rutinas versionadas y ejecución de entrenamiento.
- nutrition: planes alimenticios versionados.
- progress: mediciones y referencias a fotografías protegidas.
- media: archivos privados, almacenamiento y entrega autorizada.
- documents: PDF y exportaciones.
- receivables: cargos, pagos, aplicaciones de pagos y devoluciones del negocio.
- platform_billing: lo que el negocio paga a MyGym.
- licensing: licencias Local.
- invoicing: facturación fiscal futura.
- notifications: entregas por canales autorizados.
- audit: trazabilidad de acciones sensibles.

Cada módulo es dueño de sus escrituras. Otro módulo solicita una operación a una interfaz interna, no altera directamente tablas ajenas. Mantener modelos, servicios, consultas, políticas, API y pruebas con responsabilidades claras.

Usar transacciones para las operaciones que deban confirmarse juntas. Evitar importaciones circulares y señales ocultas como mecanismo principal de coordinación.

Para efectos externos usar eventos/outbox persistidos junto con la operación, reintentos e idempotencia. No hacer que un fallo al enviar correo deje inconsistente una membresía o duplique un cobro.

No crear todas las aplicaciones vacías ni un sistema genérico de plugins desde el inicio. Crear únicamente lo que necesita el hito actual; conservar lo restante como mapa documentado.

# 9. ESTRUCTURA ORIENTATIVA DEL REPOSITORIO

mygym/
  backend/
    manage.py
    config/
      settings/
      urls.py
    modules/
      identity/
      workspaces/
      clients/
      audit/
      ...otros módulos cuando corresponda...
    tenancy/
    tests/
  frontend/
    src/
      app/
      features/
      shared/
    tests/
  scripts/
  deployment/
  docs/
    architecture/
    security/
    operations/
    api/
    superpowers/specs/
    superpowers/plans/
  AGENTS.md
  README.md
  .env.example
  .gitignore

La estructura es una guía, no prueba de archivos existentes. Reutiliza lo correcto que encuentres. No crees carpetas vacías solo para reproducir el dibujo.

Centralizar llamadas HTTP, tratamiento de errores y configuración. La interfaz usa URLs relativas; no incrustar el dominio Cloud en componentes que también funcionarán Local.

# 10. AISLAMIENTO ENTRE ORGANIZACIONES

Comenzar con PostgreSQL y esquema compartido. Los registros de negocio tienen workspace_id obligatorio; índices y restricciones respetan el contexto. No crear tablas diferentes por gimnasio.

En cada operación verificar identidad, acceso vigente, workspace activo, capacidad habilitada, permiso de acción y objeto concreto. El workspace enviado por URL o cuerpo es una solicitud, no una prueba de autorización.

Rechazar referencias cruzadas en creación, edición, listas, búsquedas, exportaciones y relaciones. Los UUID no sustituyen controles de acceso.

No guardar un workspace activo global mutable en la sesión que provoque cruces entre pestañas. Cada petición debe identificar y validar su propio contexto. Las claves de caché incluyen workspace y el alcance de autorización necesario.

## PostgreSQL Row-Level Security

RLS será una defensa adicional para los datos de negocio, no un reemplazo de los permisos de aplicación. En el primer hito se aplicará a ClientRecord y AuditEvent.

La conexión runtime no será superusuario, no tendrá BYPASSRLS ni será propietaria de esas tablas. Separar el rol de migraciones y no usarlo para servir peticiones.

Establecer el contexto validado de workspace dentro de una transacción, con SQL parametrizado y políticas USING/WITH CHECK. Sin contexto, no devolver expedientes y rechazar escrituras. Verificar rollback, reutilización de conexiones y ausencia de contexto residual; no asumir que anidar contextos de otro workspace es seguro.

Probar con credenciales runtime realmente restringidas. Si la prueba utiliza privilegios que evaden RLS, debe fallar o reportarse como inválida, no declararse aislamiento exitoso.

Las tablas de identidad y descubrimiento de workspaces tendrán selectores estrictamente restringidos para resolver accesos antes del contexto. Documentar esa excepción: no afirmar que toda la base tiene RLS si no es cierto.

La autorización se repite en workers, reportes y exportaciones. RLS por organización no concede por sí solo permiso para ver todas las fotos de esa organización.

# 11. AUTENTICACIÓN, ROLES Y SEGURIDAD

Usar sesiones Django para la web, cookies protegidas y CSRF en las operaciones de escritura, incluido login. HttpOnly para la cookie de sesión, Secure en HTTPS y SameSite adecuado. Excepciones de HTTP únicamente para desarrollo loopback documentado.

No guardar contraseñas en texto plano ni tokens de sesión en localStorage. Utilizar hashing y mecanismos maduros de recuperación. Limitar intentos de acceso y evitar mensajes que permitan enumerar cuentas.

En Cloud, exigir MFA a coaches y administradores antes de habilitar funciones sensibles, incluyendo recuperación y revocación. El primer prototipo no se anunciará como listo para producción por tener solo login.

Roles previstos: propietario, administrador autorizado, recepción, coach y cliente final. El operador técnico de MyGym tiene funciones de soporte; no debe disponer de una galería universal de fotografías.

Recepción solo necesita los datos administrativos de su función. Un coach accede a clientes explícitamente asignados. Un cliente ve sus propios datos. Ser dueño del gimnasio no otorga acceso automático a todas las fotos privadas de seguimiento.

En Local, diseñar posteriormente una recuperación de acceso segura que no dependa obligatoriamente del correo o de nuestros servidores.

No exponer base de datos a Internet, abrir puertos del router o activar CORS universal para evitar configurar correctamente la aplicación. Separar desarrollo, pruebas y producción.

# 12. FOTOGRAFÍAS Y DATOS SENSIBLES

Distinguir foto de identificación y fotografía de progreso. No publicar ninguna por comodidad; las de progreso tendrán reglas especialmente restrictivas.

Acceso por defecto a una foto de progreso: el cliente correspondiente y el coach explícitamente autorizado. Otros clientes, otros coaches, recepción, negocios ajenos y soporte no reciben acceso automático.

Usar almacenamiento privado. Preferir inicialmente que el backend autentique y autorice cada lectura de imágenes sensibles. Proteger originales, miniaturas, PDF, exportaciones y respaldos.

No publicar el directorio privado como contenido estático ni crear enlaces permanentes públicos. Si se usan enlaces firmados, asumir que quien obtiene el enlace puede usarlo mientras sea válido; usar vigencia corta y evitar filtrarlos a logs o analítica.

Validar contenido real, formato, tamaño y resolución. Generar nombres internos, reprocesar imágenes y retirar metadatos innecesarios como GPS/EXIF. Controlar archivos maliciosos y no confiar solamente en extensión o Content-Type.

Aplicar controles de caché para evitar almacenamiento compartido de contenido sensible. No convertir automáticamente el portal en una PWA que conserve fotos o expedientes en caché offline.

Proteger datos y copias en reposo, conexiones, claves y permisos. No afirmar cifrado de extremo a extremo si el servidor puede descifrar el contenido. No prometer cero filtraciones: usuarios autorizados pueden copiar información o tomar capturas.

Registrar acciones sensibles sin copiar contenido personal, imágenes, contraseñas o enlaces de acceso a los logs. Prever revocación, retención, eliminación, consentimiento cuando corresponda y respuesta a incidentes.

El marco de privacidad de Ecuador, responsabilidades, tratamiento de información de salud, menores y proveedores externos requerirá revisión competente antes del lanzamiento. No afirmar cumplimiento legal automático.

Solo usar datos ficticios durante desarrollo. Nunca enviar a Codex, Git, herramientas externas o demos datos reales de clientes, fotos, documentos de identidad, certificados fiscales o bases productivas.

# 13. FUNCIONES FUTURAS DEL GIMNASIO

Gestión de fichas con nombre y contacto, fotografía de identificación protegida cuando se habilite, y otros datos realmente necesarios. Identificación nacional, fecha de nacimiento y contacto de emergencia se incorporan solo con finalidad justificada; no son obligatorios en el núcleo inicial.

Planes, inscripciones, fecha de inicio, vencimiento, estado, renovaciones, historial de cobros, asistencia, alertas de próximas caducidades y reportes administrativos.

No almacenar días restantes como valor permanente: calcularlos a partir de reglas explícitas. Separar las fechas de vigencia del servicio de los pagos.

Antes del módulo de membresías, resolver y documentar si un plan es por días o por meses calendario, si vence al terminar una fecha o a una hora, cómo renueva una membresía vigente, y qué ocurre con congelaciones, cancelaciones, pagos parciales y devoluciones. Estos detalles siguen pendientes: no inventarlos silenciosamente.

Usar Decimal y moneda para dinero, no flotantes. Tiempos de eventos con zona horaria; cada negocio tiene su zona. America/Guayaquil y USD son referencias iniciales para Ecuador, no motivos para impedir otros valores en el futuro.

Las fechas, pagos y asistencia deben poder auditarse sin borrar arbitrariamente historial. El control de acceso físico, QR y torniquetes será posterior.

# 14. FUNCIONES FUTURAS DE COACH

Biblioteca de ejercicios y rutinas genéricas o personalizadas con días, orden, series, repeticiones, descansos e instrucciones. Publicar versiones: modificar una plantilla no altera sesiones históricas ni planes ya registrados.

Guardar sesiones y series realizadas separadas del plan: carga externa, unidad, repeticiones, fecha, autor y referencias necesarias. No confundir peso corporal con carga del ejercicio ni interpretar carga cero como dato inexistente.

Planes alimenticios versionados con comidas, cantidades, unidades e indicaciones. Son contenidos elaborados por un profesional autorizado según corresponda, no diagnósticos o prescripciones automáticas de IA.

Mediciones, peso corporal, evolución, comentarios y fotografías opcionales. Definir qué introduce el cliente y qué controla el coach; registrar autoría y cambios.

Exportación de rutina y alimentación en PDF tanto en Local como Cloud, según permisos. El portal Cloud ofrece interacción; Local ofrece administración privada y entrega de documentos.

Agenda, mensajería, automatizaciones y funciones avanzadas pueden añadirse posteriormente, sin convertirlas en requisitos del primer hito.

# 15. EXPORTACIONES Y COMPARTIR ARCHIVOS

Para Local, el primer mecanismo será generar PDF y guardarlo en el equipo. La subida a Drive o envío por WhatsApp/correo será manual.

No implementar OAuth o la API de Drive solo para esta necesidad inicial. Una integración automática futura debe ser opcional, autorizada y no romper el funcionamiento offline.

Incluir nombre del negocio, destinatario, contenido pertinente y fecha/versión del plan. Usar plantillas controladas y evitar contenido remoto o HTML arbitrario que permita lecturas o solicitudes no autorizadas.

Los recursos esenciales, fuentes y contenido incluido deben estar empaquetados para Local, sin CDN obligatorio. Un video externo no se promete disponible sin conexión. Usar contenido propio o con derechos adecuados.

Un PDF no es un respaldo de la aplicación. Un archivo enviado a Drive/correo deja de estar protegido por las sesiones de MyGym; explicar el alcance y evitar permisos públicos por defecto.

# 16. DESPLIEGUE LOCAL Y CLOUD

Reutilizar lógica de negocio con adaptadores para almacenamiento, notificaciones, licencias y servicios externos. No dispersar condicionales LOCAL/CLOUD por todas las vistas.

Cloud usa infraestructura centralizada y configura capacidades por negocio. Local mantiene el mismo modelo de organización, normalmente con un workspace inicial, y datos persistentes en el equipo.

Local no depende de suscripciones SaaS, verificación periódica obligatoria online, correo real, autenticación externa, R2 o APIs para su operación básica. Licencia offline no significa ausencia de controles locales de acceso.

Primero probar el desarrollo en Windows nativo. Más adelante comparar instalación comercial nativa y contenedores según el equipo y costos de soporte. Docker/WSL puede ser una opción, no un requisito impuesto hoy. Revisar requisitos y licencia antes de distribuir una solución basada en Docker Desktop.

Para LAN, habilitar acceso deliberadamente, con autenticación, firewall mínimo y HTTPS confiable cuando corresponda. El equipo servidor debe estar encendido; definir suspensión, reinicio, energía y recuperación.

Mantener base y archivos fuera de la imagen o paquete de aplicación. Actualizar no debe borrar datos. Empaquetar versiones, respaldar antes de migraciones y verificar restauración.

Un usuario administrador del equipo local conserva capacidades sobre sus archivos; no prometer protección absoluta contra copia o manipulación.

# 17. MIGRACIÓN LOCAL A CLOUD

Debe existir una ruta futura controlada, no sincronización bidireccional en el MVP.

Exportar solo el workspace autorizado, con versión de esquema, archivos y manifiesto de integridad. Validar compatibilidad, recuentos, relaciones, duplicados e identificadores antes de importar.

No transferir indiscriminadamente sesiones, secretos, licencias ni credenciales locales. Los accesos Cloud se establecerán con verificación e invitación.

Conservar el origen hasta comprobar la importación. No permitir escritura simultánea en ambos sistemas ni prometer que basta cambiar la URL de la base de datos.

# 18. COBROS, SUSCRIPCIONES Y FACTURACIÓN

Mantener separados:

- receivables: cargos, pagos, aplicaciones y devoluciones del gimnasio/coach.
- platform_billing: suscripción del negocio a MyGym.
- invoicing: comprobantes fiscales de su emisor correspondiente.

Factura, membresía y pago no son el mismo objeto ni necesariamente suceden al mismo tiempo. Una factura puede emitirse antes del cobro. Un pago puede aplicarse a varias obligaciones.

El módulo fiscal futuro utiliza una instantánea de datos de emisor, receptor, conceptos, impuestos, moneda y totales; estados, documentos e idempotencia. Un reintento no debe duplicar una emisión.

Un PDF interno no equivale por sí mismo a una factura electrónica autorizada. La futura integración SRI o de proveedor requiere revisar normativa, firma, autorización y credenciales vigentes. No implementar ni certificar aspectos legales basándose únicamente en este prompt.

Local puede guardar operaciones sin Internet, pero una comunicación con SRI/proveedor requiere conectividad y un flujo legalmente válido. Mientras el módulo no exista, las obligaciones fiscales reales se resuelven por un mecanismo autorizado separado.

Para pasarelas, validar proveedor, país, cuenta comercial, recurrencia, comisiones, webhooks y reembolsos. PayPhone y Kushki se mencionaron como candidatos; no están elegidos ni integrados. No asumir disponibilidad de Stripe para el negocio sin comprobarla.

No almacenar números completos de tarjeta ni CVV. Separar credenciales y cuentas de MyGym de las de cada gimnasio/coach. No convertirnos accidentalmente en intermediarios de todos los cobros.

# 19. OPERACIÓN, RESPALDOS Y COSTOS

Necesitamos costos bajos al comenzar, pero no una arquitectura dependiente de cuentas gratuitas, servicios que se suspenden o respaldos inexistentes.

Referencias presupuestarias discutidas previamente, NO cotizaciones vigentes ni órdenes de compra:

- Piloto Cloud autoadministrado: aproximadamente USD 40–60 al mes.
- Inicio con PostgreSQL administrado separado: aproximadamente USD 80–120 al mes.
- Ejemplo considerado: VPS de aplicación de unos USD 24 al mes; respaldo diario alrededor de USD 7,20; provisión de USD 35–45 para base administrada y disco; correo inicialmente entre USD 0–20; dominio como supuesto de USD 18 al año.

Es presupuesto de la plataforma compartida, no por gimnasio. No incluye impuestos, trabajo de los socios, soporte, asesoría, pasarelas, facturación, WhatsApp, videos, marketing ni alta disponibilidad completa. Verificar precios y condiciones oficiales cuando llegue la etapa de contratar.

DigitalOcean fue una referencia, R2 una opción de almacenamiento y Resend una opción de correo; Render fue una alternativa. Ninguno es una dependencia comercial irreversible del dominio.

Un VPS compartido por aplicación y DB es un punto de fallo. Una base administrada de un nodo no prueba alta disponibilidad. No garantizar número de gimnasios soportados sin pruebas de carga.

Medir latencia, errores, CPU/RAM/disco, conexiones y consultas SQL, almacenamiento y tareas pendientes. Primero optimizar consultas, índices y paginación; después aumentar recursos, separar workers o añadir instancias según datos. No empezar con Kubernetes.

Para el primer hito no comprar dominio, hosting ni servicios de pago. Trabajar con una base exclusiva de desarrollo.

Respaldar base y archivos, mantener copias cifradas fuera del disco/servidor principal, separar credenciales y comprobar restauración en otro entorno. Definir objetivos de pérdida máxima de datos y tiempo de recuperación antes de prometerlos.

No entregar un dump de toda la nube a un gimnasio. Las exportaciones por negocio deben respetar el aislamiento. Considerar eliminación y retención para no reintroducir datos borrados al restaurar una copia antigua.

MyGym Local también genera costos de instalación, equipo, soporte y mantenimiento aunque no alquile infraestructura remota.

# 20. PRIMER HITO: NÚCLEO Y FICHAS BÁSICAS

Construir, después de aprobar diagnóstico y plan, solamente este recorrido:

Login → workspaces autorizados → selección de negocio → listado, alta y edición de clientes → logout.

Debe operar en desarrollo Windows con PostgreSQL, sin depender de servicios Cloud de MyGym. Usar dos gimnasios ficticios y una identidad que acceda a ambos para comprobar separación.

## Modelos iniciales

- identity.User: personalizado desde la primera migración, basado en AbstractUser, con username para el acceso inicial. Correo no obligatorio para operadores Local; sin roles globales de negocio.
- Workspace: UUID, nombre, kind GYM/COACH, zona horaria y activo.
- WorkspaceAccess: workspace, user, role OWNER/RECEPTION/COACH e is_active; relación única por usuario y workspace.
- WorkspaceCapability: workspace, code, enabled; unicidad por workspace y código. Primera capacidad: clients.manage.
- ClientRecord: UUID, workspace obligatorio, user opcional, full_name, phone/email opcionales, is_active y fechas de creación/actualización.
- AuditEvent: workspace, actor, acción, identificador del objeto, fecha y nombres de campos cambiados; no almacenar sus valores personales ni credenciales.

La primera API no permite editar workspace o user de una ficha ni modificar roles. No incluir fotografía, cédula, información clínica, membresía o alimentación en este primer formulario.

OWNER y RECEPTION pueden listar, crear y editar fichas básicas con acceso y capacidad activos. COACH permanece denegado en este hito hasta que exista asignación individual; no darle acceso a todos por comodidad.

Usuarios, workspaces y accesos se preparan con un comando demo limitado a desarrollo. No crear registro público de propietarios ni interfaces abiertas para otorgar roles.

## API inicial

Todas las rutas con barra final y respuestas JSON:

GET    /api/v1/health/
GET    /api/v1/auth/csrf/
POST   /api/v1/auth/login/
POST   /api/v1/auth/logout/
GET    /api/v1/auth/me/
GET    /api/v1/me/workspaces/
GET    /api/v1/workspaces/{workspace_id}/clients/
POST   /api/v1/workspaces/{workspace_id}/clients/
GET    /api/v1/workspaces/{workspace_id}/clients/{client_id}/
PATCH  /api/v1/workspaces/{workspace_id}/clients/{client_id}/

No DELETE. La desactivación conserva el expediente.

Login inicial con username/password y CSRF. Health devuelve un estado mínimo sin secretos, nombres de bases ni versiones internas.

Listado paginado de 25 elementos, máximo 100, orden estable. Validar UUID, campos y tamaño de entradas. Rechazar campos prohibidos como workspace, workspace_id, user, user_id o role, no ignorarlos silenciosamente.

Contrato inicial: 400 para validación y credenciales inválidas; 403 sin sesión, CSRF inválido o permiso insuficiente; 404 para workspace no autorizado/inexistente o cliente fuera del workspace solicitado. Mantener pruebas e interfaz coherentes con esos códigos. No asumir 401 si SessionAuthentication no lo produce.

Documentar el formato de errores y el contrato OpenAPI. Usar una operación transaccional para ficha y auditoría.

## Interfaz inicial

Login, selector de workspace, listado de clientes, formulario de alta/edición y estados de acceso denegado. Diseño responsive en español, formularios accesibles, validaciones y estados de carga, vacío y error.

Mostrar siempre el negocio activo. No usar datos ficticios como respuestas productivas ni dibujar botones que simulen módulos inexistentes.

Vite puede usar proxy local para /api. Sesiones y CSRF reales; no CORS universal. Caché por contexto, sin persistir expedientes en localStorage. Logout invalida sesión y limpia datos privados; comprobar el comportamiento de varias pestañas.

# 21. PRUEBAS DE ACEPTACIÓN DEL PRIMER HITO

No declarar listo el núcleo sin comprobar:

1. Login válido, error genérico, limitación de intentos, CSRF y logout real.
2. Un operador solo descubre workspaces activos con acceso activo.
3. OWNER/RECEPTION con capacidad gestionan sus fichas; COACH no autorizado falla.
4. Revocar acceso o capacidad después del login afecta la siguiente petición.
5. Gimnasio A no lista, lee, crea ni modifica datos de B alterando URL o cuerpo.
6. Inyectar workspace_id, user_id o role no vincula ni mueve expedientes.
7. Fichas sin correo funcionan; el mismo correo en dos negocios no fusiona identidades.
8. Auditoría y escritura se confirman/revierten juntas sin registrar valores sensibles.
9. RLS opera con runtime restringido; falta de contexto deniega; conexión reutilizada no arrastra contexto.
10. Una identidad con dos workspaces mantiene dos pestañas sin mezclar resultados ni cachés.
11. El frontend usa API real; tipos, lint y compilación funcionan.
12. Demo idempotente y no destructiva, con datos ficticios y sin contraseñas fijas en Git.
13. Dependencias reproducibles y comandos PowerShell documentados.
14. El recorrido instalado no requiere servicios remotos de MyGym. Esto no implica que Codex funcione offline ni certifica el futuro instalador comercial.

Ejecutar pruebas con PostgreSQL real. Una suite que omite DB, usa mocks para todo o evade RLS con privilegios no verifica el requisito.

No usar superusuarios para demostrar permisos correctos. No borrar ni debilitar pruebas para obtener verde. Reportar comandos ejecutados, resultados, fallos, pruebas omitidas y limitaciones.

# 22. ETAPAS DESPUÉS DEL NÚCLEO

Roadmap, sin autorización automática para ejecutarlo completo:

1. Núcleo anterior: identidad, organizaciones, clientes, auditoría, aislamiento e interfaz.
2. Gym operativo: planes, membresías, pagos manuales, vigencia, asistencia y reportes.
3. Entrega Local: instalación asistida, arranque, empaquetado, exportación, actualización y recuperación.
4. Cloud Gym: invitaciones, portal sencillo, administración SaaS y operación multi-tenant validada.
5. Coach: asignaciones, rutinas y alimentación versionadas, sesiones/series, exportaciones y portal correspondiente.
6. Seguimiento sensible: medidas y fotos, MFA y controles completos antes de usar información real.
7. Integraciones: cobros SaaS automatizados, facturación, notificaciones y servicios opcionales.

Preparar seguridad y privacidad cuando lo exija cada función; no interpretarlas como algo que se deja para el final. Las etapas no equivalen a fechas prometidas.

Fuera del MVP: sincronización bidireccional, reconocimiento facial, torniquetes, microservicios, Kubernetes, IA prescriptiva, marketplace, contabilidad integral, tienda, streaming de video y apps móviles nativas.

Puede haber una futura experiencia MyGym Member, pero no crear ahora otro backend ni otro producto de pago para el cliente final. Figma puede utilizarse posteriormente para diseño si se solicita; no es un requisito del núcleo.

# 23. FORMA DE TRABAJAR CON CODEX

Inspeccionar antes de modificar. Respetar instrucciones vigentes, archivos y cambios del usuario. No asumir que no existe código por tratarse de un proyecto inicial.

Resolver por lectura lo que el repositorio permita. No volver a preguntar si quiero Gym/Coach, Cloud/Local, Windows, aislamiento o los módulos descritos: ya está decidido.

Distinguir requisitos confirmados, propuestas técnicas, decisiones pendientes y funcionalidades futuras. Cuando falte una regla de negocio material, registrarla y resolverla antes de programar ese flujo; no bloquear el núcleo por decisiones de facturación futura.

Después de aprobar la implementación, trabajar secuencialmente: prueba relevante que falle → cambio mínimo → pruebas → revisión del diff → documentación. Evitar varios agentes modificando los mismos modelos o migraciones.

No hacer refactorizaciones ajenas al hito, eliminar bases, usar git reset --hard, revertir cambios del usuario ni ejecutar limpiezas destructivas. No crear repositorios remotos, hacer commit/push, desplegar, comprar dominios o contratar servicios sin autorización.

No instalar herramientas globales ni cambiar servicios o seguridad del sistema sin permiso. Tras la aprobación del hito, las dependencias del proyecto se instalan en su entorno aislado según el plan autorizado.

No leer secretos innecesarios, imprimirlos, incluirlos en logs o subirlos al repositorio. Ignorar .env, bases, medios privados, copias y certificados en Git. .env.example contiene variables y ejemplos no secretos, nunca credenciales válidas.

No fabricar evidencias ni afirmar que probaste mi equipo si no accediste a él. Separar diagnóstico, documentación, código escrito, código probado y aplicación desplegada.

Si existen habilidades de planificación, desarrollo guiado por pruebas o verificación disponibles en tu entorno, utilízalas según corresponda. No afirmar que invocaste herramientas o habilidades inexistentes.

# 24. DOCUMENTACIÓN Y CONTINUIDAD

Una vez autorizada la preparación de archivos, mantener:

- AGENTS.md: reglas duraderas, límites, convenciones y comandos realmente disponibles.
- docs/PROJECT_CONTEXT.md: visión completa y decisiones de este prompt.
- docs/architecture/: decisiones y límites de módulos.
- docs/superpowers/specs/: alcance detallado del hito.
- docs/superpowers/plans/: tareas con archivos, interfaces, pruebas y aceptación.
- docs/security/: matriz de permisos, aislamiento y tratamiento de archivos.
- docs/operations/: desarrollo Windows, despliegues y recuperación cuando existan.
- README.md: instalación y ejecución verificadas.

Si ya existe documentación equivalente, actualizar/reutilizar; no crear fuentes contradictorias. La corrección a Windows nativo prevalece sobre la preferencia antigua de exigir Docker para desarrollar.

Persistir decisiones, progreso y pendientes para continuar en otra sesión sin depender de memoria de chat. Mantener AGENTS.md práctico y referenciar documentos extensos en lugar de duplicarlos enteros.

Al cerrar cada hito, informar: cambios, archivos, comandos, resultados, bloqueos, diferencias respecto al plan y siguiente paso. No crear largas listas de funciones que no se implementaron como si existieran.

# 25. TU PRIMER ENCARGO AHORA

NO programes todo MyGym. NO instales nada ni modifiques archivos o el sistema durante este diagnóstico.

A. Comprueba la carpeta autorizada, instrucciones aplicables, archivos existentes y estado Git. No inspecciones otros proyectos ni información personal ajena a esta tarea.

B. Revisa este contexto y, si existen, AGENTS.md y documentos de arquitectura, especificación y plan. Este mensaje es autosuficiente: no te detengas por no encontrar el ZIP anterior.

C. Comprueba de manera no destructiva Python, Node/npm, Git y PostgreSQL en el entorno accesible. No confundas disponibilidad del cliente psql con un servidor funcionando. Si faltan permisos, conectividad o acceso al Windows real, diferencia claramente lo comprobado de lo desconocido.

D. Devuélveme una tabla de herramientas detectadas/faltantes y requisitos concretos. No exigir Docker/WSL/Linux ni cambiar PostgreSQL por SQLite.

E. Resume tu comprensión, comprueba contradicciones y presenta la especificación del primer hito y su plan de implementación. Si existe un plan válido, revisa solo lo necesario en lugar de reescribirlo por gusto.

F. Divide el plan inicial en identidad, workspaces/accesos, fichas/auditoría, RLS, interfaz y verificación. Para cada parte, indica archivos y responsabilidades, dependencias, pruebas y criterio de finalización. No marques nada como realizado si no lo está.

G. Indica el siguiente paso ejecutable, los cambios de entorno que necesitan permiso y qué documentación se creará al aprobar.

Termina ahí para que revise el diagnóstico y autorice la implementación. No vuelvas a ofrecer cuatro arquitecturas distintas ni reabras decisiones resueltas. Queremos empezar por una base pequeña, real y comprobable, conservando toda la visión de MyGym descrita arriba.