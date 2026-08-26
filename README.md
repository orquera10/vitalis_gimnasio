# 🏋️‍♂️ Vitalis Fitness Club - Sistema de Gestión de Gimnasio

Sistema integral de gestión de gimnasio, socios, clases, entrenadores, pagos, reportes y configuración desarrollado con **Django 5**, diseño **Obsidian Glassmorphism & Champagne Gold** y suite completa de pruebas automatizadas.

---

## 📁 Módulos del Sistema

1. **`core`**: Autenticación (login/logout VIP), panel de administración, Dashboard ejecutivo con 4 KPIs principales, gráficos interactivos Canvas (Tendencia de Ingresos & Distribución de Planes), **Centro de Alertas y Notificaciones en tiempo real** y **Control de Accesos por Rol (RBAC)**.
2. **`members`**: Gestión completa de Socios y Planes de membresía, estados de cuota (*Activa, Pendiente, Vencida*), ficha técnica 360°, historial de asistencias y pagos, y **carga de fotos de perfil desde archivo local (Pillow) o URL**.
3. **`classes`**: Sistema de Disciplinas/Categorías, programación de horarios recurrentes semanales, **Almanaque / Calendario interactivo**, aforo en tiempo real, inscripciones y control de asistencia (*Presente, Ausente*).
4. **`trainers`** *(dentro de `classes`)*: Directorio de Entrenadores/Instructores, especialidades deportivas, fotos de perfil y agenda de clases.
5. **`payments`**: Módulo financiero con cobro de cuotas, métodos de pago (*Efectivo, Transferencia/QR, Tarjeta, Mercado Pago*), emisión de **recibos oficiales digitales (`REC-2026-XXXX`) imprimibles** y **renovación automática de membresías**.
6. **`reports`**: Centro de Analíticas & Reportería con **gráficos de recaudación, alerta temprana de socios por vencer** y **exportación a Excel/CSV** de pagos, socios y asistencias, más informe ejecutivo para imprimir en PDF.
7. **`settings` / Configuración**: Centro de Ajustes de la Sede, edición de datos institucionales, CUIT/CBU, gestor de planes de membresía, disciplinas, **gestión de empleados con roles (Administrador, Recepcionista, Entrenador)**, reglas operativas y **descarga de copia de seguridad (JSON)**.

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
```

### 3. Iniciar el servidor de desarrollo
```powershell
python manage.py runserver
```

Navega a:
* **Dashboard Principal**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* **Directorio de Socios**: [http://127.0.0.1:8000/miembros/](http://127.0.0.1:8000/miembros/)
* **Almanaque de Clases**: [http://127.0.0.1:8000/clases/](http://127.0.0.1:8000/clases/)
* **Directorio de Entrenadores**: [http://127.0.0.1:8000/clases/entrenadores/](http://127.0.0.1:8000/clases/entrenadores/)
* **Gestión de Pagos & Recibos**: [http://127.0.0.1:8000/pagos/](http://127.0.0.1:8000/pagos/)
* **Centro de Reportes & Analíticas**: [http://127.0.0.1:8000/reportes/](http://127.0.0.1:8000/reportes/)
* **Centro de Configuración & Ajustes**: [http://127.0.0.1:8000/configuracion/](http://127.0.0.1:8000/configuracion/)
* **Panel de Administración Django**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## ⚙️ Variables de Entorno & Configuración de Base de Datos

El proyecto incluye soporte para **Variables de Entorno (`.env`)** y cambio fluido entre **SQLite** y **PostgreSQL**.

### 1. Crear archivo `.env`
Copia la plantilla `.env.example`:
```powershell
copy .env.example .env
```

### 2. Configurar PostgreSQL (Opcional)
Para conectar con una base de datos PostgreSQL, edita `.env`:
```env
USE_POSTGRES=True
DB_NAME=vitalis_gym
DB_USER=postgres
DB_PASSWORD=tu_contraseña_aqui
DB_HOST=localhost
DB_PORT=5432
```
*O bien mediante una URL de conexión única (Neon, Supabase, Railway, Render):*
```env
DATABASE_URL=postgresql://usuario:contraseña@servidor.com:5432/vitalis_gym
```

*(Si `USE_POSTGRES=False`, el sistema utilizará SQLite local automáticamente).*

---

## 📦 Extracción y Carga de Datos (Backup & Migración)

### Exportar datos de la base de datos a JSON:
```powershell
python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission --indent 2 --output data_backup.json
```

### Cargar los datos en una nueva base de datos (ej. PostgreSQL):
```powershell
python manage.py migrate
python manage.py loaddata data_backup.json
```

---

## 🧪 Ejecutar la suite de pruebas automatizadas
```powershell
python manage.py test
```
* **64 pruebas unitarias e integrales pasando con éxito (OK 100%)**.
