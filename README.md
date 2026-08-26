# 🏋️‍♂️ Vitalis Fitness Club - Sistema de Gestión de Gimnasio & Portal de Socios

Sistema integral y multiplataforma de gestión de gimnasios, socios, clases, entrenadores, pagos, analíticas y **Portal de Autoservicio para Clientes/Socios**. Desarrollado con **Django 5**, diseño de vanguardia **Obsidian Glassmorphism & Champagne Gold**, y suite de pruebas automatizadas al 100%.

---

## 📁 Módulos del Sistema

### 🏢 1. Panel Administrativo & Staff (Consola Ejecutiva)
1. **`core`**:
   * Autenticación segura de personal (login/logout VIP).
   * **Dashboard Ejecutivo**: 4 KPIs en tiempo real (Socios Activos, Ocupación Hoy, Ingresos del Mes, Renovaciones Pendientes).
   * **Gráficos HD Interactivos en Canvas**: Tendencia anual de ingresos y distribución de planes de membresía.
   * **Centro de Alertas & Notificaciones**: Avisos dinámicos en tiempo real de membresías por vencer, cuotas vencidas, clases completas (100% cupo) y pagos pendientes.
   * **Control de Accesos por Rol (RBAC)**: Permisos diferenciados para *Administradores*, *Recepcionistas* y *Profesores / Entrenadores*.

2. **`members` (Socios & Membresías)**:
   * Alta, edición, búsqueda rápida por nombre/DNI/email y filtros avanzados por estado y plan.
   * Ficha técnica 360° del socio con historial de pagos, asistencias y contacto de emergencia.
   * **Gestión de fotos de perfil**: Subida directa de archivos de imagen locales (procesadas con Pillow) o mediante URL externa.
   * Cálculo automático de vigencia y fechas de vencimiento.
   * Comando de sincronización automática de cuentas de usuario (`sync_member_users`).

3. **`classes` (Clases, Almanaque & Entrenadores)**:
   * **Almanaque / Calendario Semanal y Mensual**: Navegación dinámica entre semanas, etiquetas por disciplina y badges de ocupación en vivo.
   * **Horarios Recurrentes**: Programación semanal automatizada por día y hora.
   * Control de asistencia en tiempo real (*Presente, Ausente*) y límite de aforo.
   * **Directorio de Entrenadores**: Perfiles de instructores, especialidades, fotos y agenda de clases asignadas.

4. **`payments` (Finanzas & Cobranzas)**:
   * Registro de cobros y pagos de cuotas con métodos múltiples (*Efectivo, Transferencia/QR, Tarjeta de Débito/Crédito, Mercado Pago*).
   * **Emisión de Recibos Oficiales Digitales (`REC-2026-XXXX`)** con formato de impresión formal.
   * **Renovación automática de membresías** al registrar un pago completado.
   * Filtros por rango de fechas, método, estado y exportación.

5. **`reports` (Analítica & Reportería Ejecutiva)**:
   * Dashboard con métricas financieras, ticket promedio y distribución de ingresos por plan y medio de pago.
   * Detección temprana de retención: Alertas de vencimientos a 7, 15 y 30 días.
   * **Exportación a CSV / Excel**: Reporte de Pagos, Padrón de Socios y Asistencia a Clases.
   * **Informe Ejecutivo Imprimible / PDF**: Formato formal optimizado para impresión de gerencia.

6. **`settings` (Configuración & Ajustes de Sede)**:
   * Edición de información institucional (Nombre de Sede, CUIT/Tax ID, Dirección, Teléfono, CBU/Alias).
   * Gestor de Planes de membresía y Disciplinas deportivas con modales interactivos.
   * **Gestión de Empleados & Roles**: Alta de personal con asignación de roles (Administrador, Recepcionista, Entrenador) y bloqueo de auto-eliminación.
   * **Copia de Seguridad (Backup)**: Descarga directa de la base de datos completa en formato JSON.

---

### 📱 2. Portal del Socio / Cliente (`portal`)
Área web móvil y responsiva diseñada exclusivamente para los socios del gimnasio:

* **Acceso del Cliente (`/portal/login/`)**: Inicio de sesión seguro con su usuario o DNI.
* **Tarjeta de Membresía Digital**: Credencial VIP con estado de suscripción en vivo (*Activa, Al Día*), nombre del plan, fecha de vencimiento y barra visual de días restantes.
* **Mi Rutina & Ejercicios (`/portal/rutina/`)**:
  * Rutinas divididas por días (Día 1: Piernas, Día 2: Pecho/Espalda, etc.).
  * Detalle de cada ejercicio con grupo muscular, series x repeticiones, tiempo de descanso en segundos, fotos demostrativas y notas del entrenador.
* **Progreso & Medidas Corporales (`/portal/progreso/`)**:
  * Registro y evolución de peso corporal (kg), % de grasa corporal, masa muscular (kg), cintura (cm) y pecho (cm).
  * Gráfico interactivo de tendencia de peso a lo largo del tiempo.
* **Muro de Récords Personales (PRs)**:
  * Trofeos e insignias de máximos levantamientos (Press de Banca, Sentadilla, Peso Muerto).
* **Reserva de Clases desde el Móvil**:
  * Vista de clases disponibles hoy con cupos en vivo y botón de inscripción inmediata con 1 clic.
* **Mi Perfil (`/portal/perfil/`)**:
  * Consulta y actualización de datos personales, teléfono y contacto de emergencia.

### 🚪 3. Terminal / Tótem de Entrada Kiosko (`/terminal/`)
Pantalla de autoservicio para montar en tablets, tótems de entrada o molinetes en la recepción:

* **Acceso por DNI**: El socio ingresa su DNI en el teclado numérico táctil de pantalla completa o lo escanea con un lector de código de barras / QR.
* **🟢 Pantalla Verde (Al Día)**: Mensaje de bienvenida personalizado (*"¡Bienvenido/a, [Nombre]!"*), foto del socio, plan contratado, fecha de vencimiento y días restantes de vigencia, con sonido de confirmación.
* **🔴 Pantalla Roja (Vencido)**: Mensaje de alerta visual y sonora (*"⚠️ Tu membresía venció el DD/MM/YYYY. Acércate a recepción"*).
* **🟡 Pantalla Ámbar (Pendiente / No Encontrado)**: Aviso de cuota pendiente o DNI no registrado.
* **Reinicio Automático**: Contador visual de 4 segundos que resetea la pantalla para el siguiente socio automáticamente.
* **Registro de Asistencia**: Guarda cada ingreso con fecha y hora exacta en el historial del socio.

---

## 🚀 Cómo ejecutar el proyecto

### 1. Activar el entorno virtual
En Windows (PowerShell):
```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Sembrar datos de prueba iniciales (Opcional)
```powershell
python manage.py seed_members
python manage.py seed_classes
python manage.py seed_payments
python manage.py seed_client_data
```

### 3. Iniciar el servidor de desarrollo
```powershell
python manage.py runserver
```

### 🔗 Enlaces Principales del Sistema

#### 🏢 Panel de Gestión & Administración:
* **Dashboard Principal**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* **Directorio de Socios**: [http://127.0.0.1:8000/miembros/](http://127.0.0.1:8000/miembros/)
* **Almanaque de Clases**: [http://127.0.0.1:8000/clases/](http://127.0.0.1:8000/clases/)
* **Directorio de Entrenadores**: [http://127.0.0.1:8000/clases/entrenadores/](http://127.0.0.1:8000/clases/entrenadores/)
* **Gestión de Pagos & Recibos**: [http://127.0.0.1:8000/pagos/](http://127.0.0.1:8000/pagos/)
* **Centro de Reportes & Analíticas**: [http://127.0.0.1:8000/reportes/](http://127.0.0.1:8000/reportes/)
* **Centro de Configuración & Ajustes**: [http://127.0.0.1:8000/configuracion/](http://127.0.0.1:8000/configuracion/)
* **Panel de Administración Django**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

#### 🚪 Terminal de Entrada / Kiosko:
* **Tótem de Acceso por DNI**: [http://127.0.0.1:8000/terminal/](http://127.0.0.1:8000/terminal/)

#### 📱 Portal de Autoservicio para Socios:
* **Portal del Cliente**: [http://127.0.0.1:8000/portal/](http://127.0.0.1:8000/portal/)
* **Login de Socios**: [http://127.0.0.1:8000/portal/login/](http://127.0.0.1:8000/portal/login/)
* **Mi Rutina de Entrenamiento**: [http://127.0.0.1:8000/portal/rutina/](http://127.0.0.1:8000/portal/rutina/)
* **Mi Progreso & Medidas**: [http://127.0.0.1:8000/portal/progreso/](http://127.0.0.1:8000/portal/progreso/)
* **Mi Perfil**: [http://127.0.0.1:8000/portal/perfil/](http://127.0.0.1:8000/portal/perfil/)

---

## ⚙️ Variables de Entorno & Configuración de Base de Datos

El proyecto incluye soporte para **Variables de Entorno (`.env`)** y cambio fluido entre **SQLite** y **PostgreSQL**.

### 1. Crear archivo `.env`
Copia la plantilla `.env.example`:
```powershell
copy .env.example .env
```

### 2. Configurar PostgreSQL
Edita tu `.env` para conectar con tu servidor PostgreSQL:
```env
USE_POSTGRES=True
DB_NAME=gimnasio_prueba
DB_USER=postgres
DB_PASSWORD=tu_contraseña_aqui
DB_HOST=192.168.1.25
DB_PORT=5432
```
*O bien mediante una URL directa (Neon, Supabase, Railway, Render):*
```env
DATABASE_URL=postgresql://usuario:contraseña@servidor.com:5432/vitalis_gym
```

*(Si `USE_POSTGRES=False`, el sistema operará automáticamente con SQLite local).*

---

## 📦 Extracción y Carga de Datos (Backup & Migración)

### Exportar base de datos a JSON:
```powershell
python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission --indent 2 --output data_backup.json
```

### Cargar datos en una base de datos nueva o PostgreSQL:
```powershell
python manage.py migrate
python manage.py loaddata data_backup.json
```

---

## 🧪 Suite de Pruebas Automatizadas
```powershell
python manage.py test
```
* **69 pruebas unitarias e integrales pasando con éxito (OK 100%)**.
