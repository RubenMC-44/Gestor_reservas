# Gestor de Reservas — Proyecto Django

Aplicación para reservar pistas deportivas (pádel, tenis, fútbol sala...) con calendario de disponibilidad, control de solapamientos, reservas recurrentes y panel de administración.

---

## Requisitos

- Python 3.10+
- pip

---

## Puesta en marcha

### 1. Crear y activar entorno virtual

```bash
# En Windows:
python -m venv venv
venv\Scripts\activate

# En Mac/Linux:
python -m venv venv
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Aplicar migraciones

```bash
python manage.py migrate
```

### 4. Cargar datos de ejemplo (pistas y horarios)

```bash
python manage.py loaddata reservas/fixtures/initial_data.json
```

### 5. Crear superusuario (para el panel de gestión y el admin de Django)

```bash
python manage.py createsuperuser
```

### 6. Arrancar el servidor

```bash
python manage.py runserver
```

Abre [http://127.0.0.1:8000](http://127.0.0.1:8000) en el navegador.

---

## Estructura del proyecto

```
gestor_reservas/
├── gestor_reservas/        # Configuración del proyecto
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/               # Registro, login, logout, perfil
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   └── templates/accounts/
├── reservas/               # Lógica principal
│   ├── models.py           # Resource, Availability, Booking
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   ├── utils.py            # Envío de emails
│   ├── admin.py
│   ├── fixtures/           # Datos de ejemplo
│   └── templates/
│       ├── base.html
│       └── reservas/
└── manage.py
```

---

## Funcionalidades

**Obligatorias:**
- Registro, login y logout de usuarios
- Listado y detalle de pistas con horario semanal
- Calendario mensual de ocupación (filtrável por pista)
- Creación de reservas con validación de solapamientos
- Reservas recurrentes (semanal) con generación automática
- Historial de reservas del usuario (próximas, pasadas, canceladas)
- Cancelación de reservas por el usuario

**Extras:**
- Notificaciones por email al confirmar y cancelar (consola en desarrollo)
- Panel de gestión para staff: ver todas las reservas, filtrar por estado/pista/fecha, cancelar reservas

---

## Notas

- Los emails se imprimen en la terminal (backend de consola). Para envío real, configura `EMAIL_BACKEND`, `EMAIL_HOST`, etc. en `settings.py`.
- El panel de gestión (`/gestion/`) solo es accesible para usuarios con `is_staff=True`.
- Las imágenes de pistas se guardan en `media/resources/` (carpeta creada automáticamente).
