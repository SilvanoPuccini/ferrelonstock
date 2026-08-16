from pathlib import Path
import os
import environ
import dj_database_url
import cloudinary
import cloudinary.uploader
import cloudinary.api
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse_lazy

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment variables
env = environ.Env(
    DEBUG=(bool, False)
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'), overwrite=False) if os.path.exists(os.path.join(BASE_DIR, '.env')) else None

DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1', '.onrender.com'])

# SECRET_KEY: en desarrollo local se tolera un default obvio, pero en
# producción (DEBUG=False) es obligatoria y NUNCA puede quedar vacía.
if DEBUG:
    SECRET_KEY = env('SECRET_KEY', default='dev-only-insecure-key')
else:
    SECRET_KEY = env('SECRET_KEY', default='')
    if not SECRET_KEY:
        raise ImproperlyConfigured(
            'SECRET_KEY no está definida. Configurá la variable de entorno '
            'SECRET_KEY con un valor único y aleatorio antes de arrancar en producción.'
        )

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    # 'cloudinary_storage',  # Solo se usa via STORAGES
    'cloudinary',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'django.contrib.sites',
    'django.contrib.humanize',
    'import_export',

    # Third party
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'django_htmx',

    # Local apps
    'core',
    'shop',
    'cart',
    'orders',
    'payments',
    'accounts.apps.AccountsConfig',
    'shipping',
    'wishlist',
    'coupons',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

ROOT_URLCONF = 'ferrelonstock.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'cart.context_processors.cart',
                'core.context_processors.languages',
                'core.context_processors.categories_nav',
                'django.template.context_processors.i18n',
            ],
        },
    },
]

WSGI_APPLICATION = 'ferrelonstock.wsgi.application'

# La URL de la base de datos SIEMPRE viene de la variable de entorno.
# Nunca se hardcodean credenciales en el código.
DATABASE_URL = os.environ.get('DATABASE_URL', '')

if DATABASE_URL:
    # Render/Neon u otro proveedor proveen DATABASE_URL automáticamente.
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
elif DEBUG:
    # Desarrollo local sin credenciales (trust auth / socket local).
    DATABASES = {
        'default': dj_database_url.config(
            default='postgres://ferrelon@localhost:5432/ferrelonstock_db'
        )
    }
else:
    raise ImproperlyConfigured(
        'DATABASE_URL no está definida. Configurá la variable de entorno '
        'DATABASE_URL con la URL de tu base de datos antes de arrancar.'
    )

# Cache compartida entre workers de gunicorn. LocMemCache (el default de
# Django) es por proceso: con varios workers cada uno tendría su propio
# contador y el rate limit de login se podría evadir. DatabaseCache usa la
# misma DB de siempre (sin dependencias nuevas); la tabla la crea
# `manage.py createcachetable` en build.sh.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_cache',
    },
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('es', 'Español'),
    ('en', 'English'),
]
LOCALE_PATHS = [BASE_DIR / 'locale']

# Static files
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django Allauth
SITE_ID = 1
# Dominio real usado por el Site (links absolutos de los emails).
# En producción Render lo provee vía env; fallback al dominio público.
SITE_DOMAIN = env('SITE_DOMAIN', default='ferrelonstock.onrender.com')
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
ACCOUNT_LOGIN_METHODS = {'email'}
# Adapter custom: un fallo de SMTP NUNCA rompe el signup/login (el email de
# confirmación se envía durante el registro; si Brevo falla, se loguea y el
# flujo continúa en vez de explotar con 500).
ACCOUNT_ADAPTER = 'accounts.adapters.AccountAdapter'
# Rate limit de login (anti fuerza bruta): 5 intentos fallidos por email en
# 5 minutos, con tope adicional por IP (10/min). Se apoya en la cache
# compartida definida arriba (CACHES) para valer entre workers de gunicorn.
ACCOUNT_RATE_LIMITS = {
    'login_failed': '10/m/ip,5/300s/key',
}
# Hay UN proxy de confianza: el edge de Render. Sin esto allauth tomaría
# REMOTE_ADDR (la IP del edge) y TODOS los usuarios compartirían el mismo
# bucket por-IP, así 10 logins fallidos bloquearían todo el sitio. Es seguro
# porque ALLOWED_HOSTS está limitado a .onrender.com y la app solo es
# alcanzable a través del edge de Render, que SOBREESCRIBE X-Forwarded-For.
# NO usar ALLOWED_TRUSTED_CLIENT_IP_HEADER: cualquier cliente puede forjar
# ese header y evadir el rate limit.
ALLAUTH_TRUSTED_PROXY_COUNT = 1
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
# Verificación de email OBLIGATORIA: sin email confirmado el usuario no
# puede iniciar sesión (filtro anti-estafas).
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_UNIQUE_EMAIL = True
# El link de confirmación expira en 3 días.
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
# Al confirmar el email, el usuario queda logueado automáticamente.
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
# Notificaciones de allauth (cambio de password, email, etc.) activadas
# para que los templates con branding realmente se envíen.
ACCOUNT_EMAIL_NOTIFICATIONS = True
# Sin prefijo "[Sitio]" en el subject: respeta los asuntos con marca.
ACCOUNT_EMAIL_SUBJECT_PREFIX = ''
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = reverse_lazy('account_login')

# Cart session keys
CART_SESSION_ID = 'cart'
COUPON_SESSION_ID = 'coupon'

# Email (transaccional; Brevo)
# Prioridad 1: API HTTP de Brevo (puerto 443, nunca bloqueada desde datacenters).
# El SMTP de Brevo (587) bloquea a nivel TCP las IPs de datacenter (Render) y
# el connect se cuelga -> worker muerto -> 500 (visto en producción).
BREVO_API_KEY = env('BREVO_API_KEY', default='')
if BREVO_API_KEY:
    EMAIL_BACKEND = 'accounts.brevo_email_backend.BrevoEmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
# Timeout de conexión SMTP. CRÍTICO: sin esto el connect a un proveedor
# caído/lento queda bloqueado para siempre, el worker de gunicorn supera su
# timeout (30s por defecto), Render lo mata y el usuario ve un 500 con
# SystemExit (que NI SIQUIERA es capturado por `except Exception`). Con un
# timeout corto, la conexión falla con socket.timeout (una Exception normal)
# y el blindaje de accounts/adapters.py + orders/emails.py la degrada a
# warning sin romper el flujo.
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='FerrelonStock <silvano.jm.puccini@gmail.com>')
# Destinatario de notificaciones de pedidos nuevos (vacío = no se envían)
NOTIFICATION_EMAIL = env('NOTIFICATION_EMAIL', default='')

# Sin EMAIL_HOST ni BREVO_API_KEY configurados (desarrollo local): backend
# console para ver los emails en la salida estándar. En producción sin
# proveedor el envío degrada con un warning en logs pero NUNCA rompe el
# checkout (ver orders/emails.py). Con BREVO_API_KEY el backend de API tiene
# prioridad y NUNCA se pisa.
if not EMAIL_HOST and not BREVO_API_KEY:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Stripe
STRIPE_PUBLIC_KEY = env('STRIPE_PUBLIC_KEY', default='')
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET', default='')

# Mercado Pago
MP_PUBLIC_KEY = env('MP_PUBLIC_KEY', default='')
MP_ACCESS_TOKEN = env('MP_ACCESS_TOKEN', default='')
MP_WEBHOOK_SECRET = env('MP_WEBHOOK_SECRET', default='')

# Shipping webhook
SHIPPING_WEBHOOK_SECRET = env('SHIPPING_WEBHOOK_SECRET', default='')

# Cloudinary
cloudinary.config(
    cloud_name=env('CLOUDINARY_CLOUD_NAME', default=''),
    api_key=env('CLOUDINARY_API_KEY', default=''),
    api_secret=env('CLOUDINARY_API_SECRET', default=''),
)
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': env('CLOUDINARY_CLOUD_NAME', default=''),
    'API_KEY': env('CLOUDINARY_API_KEY', default=''),
    'API_SECRET': env('CLOUDINARY_API_SECRET', default=''),
}
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}
# Seguridad básica (se sobreescribe en producción)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'

