# FerrelonStock — Proyecto Final 2 Django | Conquer Blocks

### 👤 Información del Estudiante

| Campo | Detalle |
|-------|---------|
| **Nombre** | Silvano Puccini |
| **Curso** | Desarrollo Web Full Stack |
| **Academia** | ConquerBlocks |
| **Módulo** | Django Avanzado — E-commerce |
| **Proyecto** | Proyecto 11: Tienda Online Minimalista |
| **Fecha** | Marzo 2026 |

---

### 🌐 Enlaces de Entrega

🔗 **Repositorio:**  
[https://github.com/SilvanoPuccini/ferrelonstock](https://github.com/SilvanoPuccini/ferrelonstock)

🚀 **Demo en vivo:**  
[https://ferrelonstock.onrender.com](https://ferrelonstock.onrender.com)

👤 **Credenciales de demo:**  
- **Admin:** `admin` / `FerrelonAdmin2026!`

---

## 📌 Descripción

**FerrelonStock** es un e-commerce profesional desarrollado con **Django 5** para una ferretería y corralón online. El proyecto permite a los clientes navegar un catálogo de productos, filtrar por categorías y marcas, agregar productos al carrito sin recargar la página, realizar compras con pasarelas de pago reales (Stripe y Mercado Pago), hacer seguimiento de envíos en tiempo real y dejar valoraciones de productos.

El proyecto fue realizado como entrega del **Proyecto 11: Tienda Online Minimalista** del módulo de Django en **ConquerBlocks**, pero fue evolucionado significativamente hacia un producto real completo con funcionalidades avanzadas de e-commerce, diseño UX profesional y deploy en producción.

---

## 🎯 Objetivo de la entrega

Aplicar los conceptos del módulo de Django sobre un proyecto e-commerce completo, poniendo en práctica:

- Arquitectura **MVT** con 7 apps modulares.
- Modelos con relaciones complejas (productos, pedidos, envíos, reviews, pagos).
- Sistema de carrito basado en sesión con actualización en tiempo real (HTMX).
- Integración con pasarelas de pago reales (Stripe y Mercado Pago).
- Sistema de envío con zonas, transportistas y tracking con webhooks.
- Autenticación completa con django-allauth.
- Panel de administración personalizado con acciones masivas, import/export.
- Almacenamiento de imágenes en la nube (Cloudinary).
- Security hardening para producción.
- Tests automatizados con pytest.
- Deploy en Render con PostgreSQL.

---

## 🛠️ Stack Tecnológico

| Tecnología | Uso |
|-----------|-----|
| **Python 3.10** | Lenguaje principal |
| **Django 5** | Framework backend |
| **PostgreSQL 16** | Base de datos relacional |
| **Tailwind CSS (CDN)** | Framework de estilos |
| **Flowbite** | Componentes UI |
| **HTMX** | Interactividad sin JavaScript (carrito, buscador, filtros) |
| **Alpine.js** | Micro-interacciones (menús, acordeones, estrellas) |
| **django-allauth** | Autenticación (registro, login, logout, reset password) |
| **Stripe** | Pasarela de pago internacional |
| **Mercado Pago** | Pasarela de pago Argentina/LATAM |
| **Cloudinary** | Almacenamiento de imágenes en la nube |
| **WhiteNoise** | Servir archivos estáticos en producción |
| **Gunicorn** | Servidor WSGI para producción |
| **django-import-export** | Importación/exportación masiva CSV/XLSX |
| **xhtml2pdf** | Generación de facturas en PDF |
| **pytest-django** | Testing automatizado |
| **django-environ** | Manejo de variables de entorno |
| **dj-database-url** | Configuración de base de datos para deploy |

---

## 🏗️ Decisiones Técnicas

### ¿Por qué este stack?

- **HTMX + Alpine.js** en vez de React/Vue: Permite interactividad avanzada (carrito drawer, buscador en tiempo real, filtros dinámicos) sin la complejidad de un framework JS completo. El proyecto sigue siendo 100% Django con templates.
- **Tailwind CSS CDN** en vez de compilado: Para un proyecto académico, el CDN simplifica la configuración sin sacrificar la calidad del diseño.
- **Cloudinary** en vez de media local: Las imágenes persisten entre deploys y se sirven desde CDN global, resolviendo el problema de almacenamiento en plataformas como Render.
- **Stripe + Mercado Pago**: Stripe para pagos internacionales, Mercado Pago para el mercado argentino/LATAM. Ambas integradas con flujos de pago completos.
- **PostgreSQL** con extensión pg_trgm: Permite búsqueda fuzzy (trigram similarity) para que el buscador encuentre productos aunque el usuario escriba con errores.

### Arquitectura de 7 Apps

El proyecto está organizado en apps independientes con responsabilidades claras:

- **shop**: Catálogo, productos, categorías, marcas, reviews
- **cart**: Carrito basado en sesión con HTMX
- **orders**: Pedidos, items, mensajes cliente-vendedor, factura PDF
- **payments**: Integración Stripe y Mercado Pago
- **shipping**: Zonas, métodos, transportistas, tracking, webhooks
- **accounts**: Perfil de usuario, avatar, dirección con auto-sync al checkout
- **core**: Páginas estáticas, contacto, FAQ, equipo dinámico

---

## ✅ Funcionalidades Principales

### 🛍️ Tienda
- Catálogo de productos con paginación
- Detalle de producto con galería de imágenes clickeables
- Búsqueda fuzzy por nombre de producto y marca (PostgreSQL trigrams)
- Filtro por categoría y marca con sidebar colapsable e independiente
- Sidebar sticky que sigue al usuario mientras hace scroll
- Sistema de ofertas con precio de descuento y badge visual
- Página dedicada de ofertas

### 🛒 Carrito
- Agregar, actualizar y eliminar productos sin recargar la página (HTMX)
- Drawer lateral con Alpine.js
- Contador de productos en el header (actualización en tiempo real)
- Barra de progreso para envío gratis ($50.000 threshold configurable)
- Respeta precios de oferta automáticamente

### 📦 Pedidos
- Checkout con datos de envío y zona
- Auto-llenado de dirección desde el perfil del usuario
- Historial de pedidos con doble badge (estado de pago + estado de envío)
- Detalle de pedido con layout de tabs y sidebar
- Sistema de mensajes/reclamos entre cliente y vendedor
- Generación de comprobante/factura en PDF con datos legales argentinos

### 💳 Pagos
- **Stripe**: Flujo completo con Checkout Sessions (api para simular comprar numero ocr tarjeta: 4242 4242 4242 4242 - vto 03/28 cvc 123 - confirmar compra o pagar)
- **Mercado Pago**: Integración con API de preferencias
- Selector de método de pago en el checkout
- Registro de pagos en modelo Payment

### 🚚 Envíos
- 7 zonas de envío con precios diferenciados
- 3 métodos de envío (express, estándar, retiro)
- 4 transportistas (Andreani, OCA, Correo Argentino, Mercado Envíos)
- Calculador de envío dinámico con HTMX en el checkout
- Página de tracking con timeline visual, barra de progreso y datos del carrier
- Endpoints webhook para Andreani, OCA y carrier genérico

### ⭐ Valoraciones
- Sistema de reviews con estrellas clickeables (1-5)
- Un review por usuario por producto
- Promedio de valoración y cantidad en la ficha de producto
- Comentarios con nombre, fecha y avatar
- Formulario solo para usuarios logueados

### 👤 Cuentas
- Registro e inicio de sesión con django-allauth (por email)
- Perfil de usuario con avatar, teléfono, dirección completa
- Auto-creación de perfil al registrarse
- Sincronización bidireccional perfil ↔ checkout
- Iniciales del usuario como fallback de avatar

### 📊 Panel de Administración
- Admin personalizado con columnas visuales (badges de descuento, estado de oferta, valoración, vendidos)
- Acciones masivas de descuento (10%, 15%, 20%, 25%, 30%, 50%)
- Acciones masivas de estado de pedidos
- **Import/Export** CSV y XLSX para productos y pedidos (django-import-export)
- Inline de imágenes de galería, envíos y mensajes
- Equipo del "Sobre Nosotros" gestionable desde admin (nombre, cargo, foto, orden)

### 🌐 Páginas
- **Home**: Hero con buscador, categorías destacadas, productos destacados con carrusel, features, CTA dinámico
- **Sobre Nosotros**: Hero, estadísticas, trayectoria, valores en cards, equipo dinámico desde admin, CTA
- **Contacto**: Formulario de contacto, mapa + info + WhatsApp, FAQ con 9 preguntas en acordeón
- **Términos y Condiciones** / **Política de Privacidad**
- WhatsApp flotante en todas las páginas
- Navegación con indicador activo (subrayado) por página

---

## 📁 Estructura del Proyecto

```bash
ferrelonstock/
├── ferrelonstock/          # Configuración principal
│   ├── settings.py         # Settings con django-environ
│   ├── settings_prod.py    # Settings de producción
│   ├── urls.py
│   └── wsgi.py
├── shop/                   # Catálogo: productos, categorías, marcas, reviews
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── admin.py
│   ├── urls.py
│   ├── tests/
│   └── management/commands/
├── cart/                   # Carrito basado en sesión
│   ├── cart.py
│   ├── views.py
│   └── tests.py
├── orders/                 # Pedidos, items, mensajes, factura PDF
│   ├── models.py
│   ├── views.py
│   ├── invoice.py
│   ├── admin.py
│   └── tests.py
├── payments/               # Stripe + Mercado Pago
│   ├── models.py
│   └── views.py
├── shipping/               # Zonas, carriers, tracking, webhooks
│   ├── models.py
│   ├── views.py
│   ├── webhooks.py
│   └── tests.py
├── accounts/               # Perfil de usuario
│   ├── models.py
│   ├── views.py
│   └── tests.py
├── core/                   # Home, About, Contact, FAQ, Team
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   └── tests.py
├── templates/              # Templates organizados por app
│   ├── base.html
│   ├── _includes/
│   ├── core/
│   ├── shop/
│   ├── cart/
│   ├── orders/
│   ├── shipping/
│   ├── accounts/
│   └── account/            # Templates de allauth
├── static/
├── build.sh                # Script de build para Render
├── render.yaml             # Configuración de deploy
├── Procfile
├── requirements.txt
└── README.md
```

---

## 🧪 Tests

El proyecto incluye **65 tests automatizados** con pytest-django, cubriendo:

| Módulo | Tests | Cobertura |
|--------|-------|-----------|
| **shop/models** | 12 | Categoría, Producto, Marca, Review, descuentos, rating promedio |
| **shop/views** | 14 | Listado, detalle, ofertas, búsqueda, filtros, submit review, duplicados |
| **cart** | 8 | Agregar, eliminar, clear, stock, precio descuento, vistas |
| **orders** | 8 | Modelo, totales, mensajes, checkout, historial, seguridad (no ver pedidos ajenos) |
| **core** | 7 | Home, about, contact, terms, privacy, formulario contacto, equipo |
| **accounts** | 5 | Perfil auto-creado, iniciales, vistas, edición |
| **shipping** | 5 | Zonas, config singleton, tracking URL, vista tracking |

```bash
# Ejecutar todos los tests
python -m pytest -v

# Resultado esperado
======================= 65 passed in ~30s =======================
```

---

## 🔒 Seguridad

### Desarrollo
- Variables de entorno con django-environ
- `.env` excluido de git
- SECRET_KEY generado aleatoriamente

### Producción (`DEBUG=False`)
- `SECURE_SSL_REDIRECT = True`
- `SECURE_HSTS_SECONDS = 31536000` (1 año)
- `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
- `SESSION_COOKIE_SECURE = True`
- `CSRF_COOKIE_SECURE = True`
- `X_FRAME_OPTIONS = 'DENY'`
- `SECURE_CONTENT_TYPE_NOSNIFF = True`
- WhiteNoise para archivos estáticos
- Cloudinary para media (imágenes nunca en el servidor)
- Gunicorn como servidor WSGI

---

## ☁️ Deploy en Producción (Render)

La aplicación está desplegada en **Render** usando:

- **Python 3.10** + **Django 5**
- **PostgreSQL** (servicio gestionado por Render)
- **Gunicorn** como servidor WSGI
- **WhiteNoise** para archivos estáticos
- **Cloudinary** para almacenamiento de imágenes
- Variables de entorno para configuración sensible

El deploy se realiza **automáticamente desde GitHub** ante cada push a `main`.

### Variables de entorno requeridas:

| Variable | Descripción |
|----------|-------------|
| `SECRET_KEY` | Clave secreta de Django (generada automáticamente) |
| `DEBUG` | `False` en producción |
| `ALLOWED_HOSTS` | `.onrender.com` |
| `DATABASE_URL` | Provista automáticamente por Render |
| `DJANGO_SETTINGS_MODULE` | `ferrelonstock.settings` |
| `CLOUDINARY_CLOUD_NAME` | Nombre del cloud de Cloudinary |
| `CLOUDINARY_API_KEY` | API Key de Cloudinary |
| `CLOUDINARY_API_SECRET` | API Secret de Cloudinary |
| `STRIPE_PUBLIC_KEY` | Clave pública de Stripe (test) |
| `STRIPE_SECRET_KEY` | Clave secreta de Stripe (test) |
| `MP_PUBLIC_KEY` | Clave pública de Mercado Pago (test) |
| `MP_ACCESS_TOKEN` | Access token de Mercado Pago (test) |

### 🖼️ Almacenamiento de imágenes

Las imágenes se almacenan en **Cloudinary** (plan gratuito), garantizando persistencia entre deploys. Configurado tanto para desarrollo como producción mediante el sistema `STORAGES` de Django 5.

⚠️ **Nota:** La demo está hosteada en Render con plan gratuito. El primer acceso puede tardar ~30 segundos en cargar si el servicio está en reposo.

---

## ⚙️ Instalación Local

### 1. Clonar el repositorio
```bash
git clone https://github.com/SilvanoPuccini/ferrelonstock.git
cd ferrelonstock
```

### 2. Crear y activar entorno virtual
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Crear base de datos PostgreSQL
```sql
CREATE DATABASE ferrelonstock_db;
CREATE USER ferrelon WITH PASSWORD 'ferrelon123';
GRANT ALL PRIVILEGES ON DATABASE ferrelonstock_db TO ferrelon;
ALTER ROLE ferrelon CREATEDB;
```

Activar extensión de trigramas:
```sql
\c ferrelonstock_db
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

### 5. Configurar variables de entorno
Crear un archivo `.env` a partir de `.env.example`:
```bash
cp .env.example .env
```

Editar `.env` con tus credenciales:
```env
SECRET_KEY=tu-secret-key-super-segura
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://ferrelon:ferrelon123@localhost:5432/ferrelonstock_db
CLOUDINARY_CLOUD_NAME=tu-cloud
CLOUDINARY_API_KEY=tu-key
CLOUDINARY_API_SECRET=tu-secret
STRIPE_PUBLIC_KEY=pk_test_xxx
STRIPE_SECRET_KEY=sk_test_xxx
MP_PUBLIC_KEY=TEST-xxx
MP_ACCESS_TOKEN=TEST-xxx
```

### 6. Ejecutar migraciones y datos demo
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py load_demo_data
python manage.py load_brands
python manage.py load_shipping
python manage.py load_carriers
python manage.py load_product_images
```

### 7. Ejecutar servidor
```bash
python manage.py runserver
```

Acceder a: `http://127.0.0.1:8000`

---

## 📋 Management Commands

| Comando | Descripción |
|---------|-------------|
| `load_demo_data` | Carga 6 categorías y 20 productos de demo |
| `load_brands` | Carga 12 marcas (Bosch, DeWalt, Stanley, etc.) |
| `load_shipping` | Carga 7 zonas y 3 métodos de envío |
| `load_carriers` | Carga 4 transportistas (Andreani, OCA, Correo Argentino, Mercado Envíos) |
| `load_product_images` | Descarga imágenes de productos desde Unsplash |
| `assign_cloud_images` | Asigna rutas de Cloudinary a productos, categorías y equipo |
| `migrate_to_cloudinary` | Migra imágenes locales a Cloudinary |

---

## ✅ Estado del Proyecto

Proyecto funcional tipo **e-commerce completo**, preparado para:

- ✅ Entrega académica (Proyecto 11 — ConquerBlocks)
- ✅ Portfolio profesional
- ✅ Presentación técnica
- ✅ Demostración funcional con datos reales
- ✅ Base para evolución a producto real

---

## 🔮 Mejoras Futuras

- Email transaccional (notificar cambio de estado de pedido)
- Login con Google (allauth social)
- Traducciones EN completas
- Newsletter backend real (actualmente el formulario no guarda)
- Wishlist / Lista de deseos
- Sistema de cupones de descuento
- Migración a VPS con CloudPanel para producción real
- Tests de integración end-to-end

---

## 👨‍💻 Autor

**Silvano Puccini**

- GitHub: [@SilvanoPuccini](https://github.com/SilvanoPuccini)
- Estudiante de Full Stack Web Development — ConquerBlocks (España)
- Estudiante de TUDAI — Universidad de la Defensa Nacional (Argentina)

---

## 📄 Licencia

Este proyecto es parte del programa educativo de **ConquerBlocks Academy**.  
Uso exclusivamente académico y de portfolio.
