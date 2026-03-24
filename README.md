# Midas Gestor

Sistema de gestión documental inteligente con capacidades de OCR, clasificación automática, extracción de metadatos y resumen NLP para documentos empresariales.

## 📋 Descripción

Midas Gestor es una aplicación web Django diseñada para gestionar documentos empresariales (contratos, órdenes de compra, certificados, etc.) con procesamiento automático mediante OCR, clasificación inteligente, extracción de metadatos clave y generación de resúmenes extractivos offline.

### Características Principales

- **Gestión de Documentos**: Sistema completo de carga, versionado y organización de documentos
- **OCR Inteligente**: Extracción automática de texto de documentos escaneados usando Tesseract OCR con múltiples estrategias de PSM y binarización adaptativa
- **Extracción Híbrida**: Combina texto embebido y OCR para maximizar la calidad del texto extraído
- **Clasificación Automática**: Sugerencias de clasificación de documentos por tipo
- **Extracción de Metadatos**: Identificación automática de fechas, montos, números de referencia y partes involucradas
- **Resumen NLP Offline**: Generación automática de resúmenes extractivos usando `sumy` (LexRank/Luhn) + NLTK, sin dependencias externas de red
- **Tipos de Documento Dinámicos**: Modelo `DocumentType` gestionable desde el panel de administración, con tipos predeterminados cargados automáticamente
- **Sistema de Auditoría**: Registro completo de todas las acciones realizadas en el sistema
- **Control de Versiones**: Manejo de múltiples versiones de documentos
- **Autenticación y Permisos**: Sistema de usuarios con control de acceso

## 🛠️ Tecnologías

- **Backend**: Django 4.2.16
- **Base de Datos**: PostgreSQL (psycopg2-binary)
- **OCR**: Tesseract OCR + pytesseract
- **Procesamiento PDF**: pypdf, pdf2image
- **NLP / Resumen**: sumy 0.11.0, nltk 3.9.1, numpy 1.26.4
- **Frontend**: Bootstrap 5 (crispy-forms)
- **Imágenes**: Pillow
- **Estáticos**: whitenoise

## 📦 Requisitos Previos

### Software Requerido

Antes de instalar el proyecto, debes tener instalado:

1. **Python 3.8+**
2. **PostgreSQL 14+**
3. **Tesseract OCR**
4. **Poppler**

### Instalación de Tesseract OCR

#### Windows

1. Descarga el instalador desde: https://github.com/UB-Mannheim/tesseract/wiki
2. Ejecuta el instalador y anota la ruta de instalación (por defecto en español: `C:\Archivos de programa\Tesseract-OCR`)
3. Durante la instalación, asegúrate de incluir los datos de idioma español (`spa.traineddata`)
4. Verifica la instalación:
   ```bash
   tesseract --version
   ```

#### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng
```

#### macOS

```bash
brew install tesseract tesseract-lang
```

### Instalación de Poppler

Poppler es necesario para convertir PDFs a imágenes para el procesamiento OCR.

#### Windows

1. Descarga Poppler para Windows desde: https://github.com/oschwartz10612/poppler-windows/releases
2. Extrae el archivo ZIP en una ubicación permanente (ej: `C:\poppler`)
3. Anota la ruta del directorio `bin` (ej: `C:\poppler\Library\bin`)

#### Linux (Ubuntu/Debian)

```bash
sudo apt install poppler-utils
```

#### macOS

```bash
brew install poppler
```

### Instalación de PostgreSQL

La aplicación usa PostgreSQL como base de datos.

#### Windows

1. Descarga el instalador desde: https://www.postgresql.org/download/windows/
2. Durante la instalación, anota el usuario (`postgres`) y la contraseña elegida
3. Crea la base de datos:
   ```sql
   CREATE DATABASE midas_gestor;
   ```

#### Linux (Ubuntu/Debian)

```bash
sudo apt install postgresql postgresql-contrib
sudo -u postgres psql -c "CREATE DATABASE midas_gestor;"
```

## 🚀 Instalación del Proyecto

### 1. Clonar el Repositorio

```bash
git clone <url-del-repositorio>
cd midas_gestor
```

### 2. Crear Entorno Virtual

```bash
python -m venv .venv
```

### 3. Activar Entorno Virtual

**Windows:**
```bash
.venv\Scripts\activate
```

**Linux/macOS:**
```bash
source .venv/bin/activate
```

### 4. Instalar Dependencias

```bash
pip install -r requirements.txt
```

> **Nota:** La primera vez que se genere un resumen, el sistema descargará automáticamente los datos de tokenización de NLTK (`punkt_tab`). Requiere conexión a internet solo en esa primera ejecución.

### 5. Configurar Rutas de Tesseract y Poppler

Edita el archivo `config/settings.py` y ajusta las siguientes variables según tu instalación:

```python
# Windows (ejemplo con instalación en español)
TESSERACT_CMD = r"C:\Archivos de programa\Tesseract-OCR\tesseract.exe"
TESSDATA_DIR = r"C:\Archivos de programa\Tesseract-OCR\tessdata"
POPPLER_PATH = r"C:\poppler\Library\bin"
TESSDATA_PREFIX = r"C:\Archivos de programa\Tesseract-OCR"

# Linux/macOS (generalmente no es necesario configurar estas rutas)
# TESSERACT_CMD = "/usr/bin/tesseract"
# TESSDATA_DIR = "/usr/share/tesseract-ocr/4.00/tessdata"
```

### 6. Configurar la Base de Datos

Edita `config/settings.py` y ajusta las credenciales de PostgreSQL:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'midas_gestor',
        'USER': 'postgres',
        'PASSWORD': 'tu_contraseña',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 7. Crear Base de Datos (migraciones)

```bash
python manage.py migrate
```

### 8. Cargar Tipos de Documento Predeterminados

```bash
python manage.py seed_document_types
```

Esto carga los tipos de documento base: **Contrato** (`CONTRACT`), **Orden de compra** (`PO`) y **Certificación** (`CERT`).

### 9. Crear Superusuario

```bash
python manage.py createsuperuser
```

### 10. Ejecutar Servidor de Desarrollo

```bash
python manage.py runserver
```

La aplicación estará disponible en: http://127.0.0.1:8000/

## 📁 Estructura del Proyecto

```
midas_gestor/
├── accounts/           # Gestión de usuarios y autenticación
├── audit/              # Sistema de auditoría
├── config/             # Configuración principal de Django
│   ├── settings.py     # Configuración del proyecto
│   └── urls.py         # URLs principales
├── core/               # Funcionalidades centrales (dashboard)
├── documents/          # Módulo principal de documentos
│   ├── models.py       # Modelos de datos
│   ├── views.py        # Vistas principales
│   ├── views_manager.py        # Vistas del panel de manager
│   ├── forms.py        # Formularios
│   ├── forms_review.py # Formularios de revisión
│   ├── signals.py      # Señales Django (hooks post-guardado)
│   ├── permissions.py  # Control de permisos
│   ├── management/
│   │   └── commands/
│   │       ├── seed_document_types.py  # Carga tipos de documento predeterminados
│   │       └── test_extraction.py      # Diagnóstico de extracción OCR
│   ├── migrations/     # Migraciones de base de datos
│   └── services/       # Lógica de negocio
│       ├── extraction.py      # Extracción de texto y OCR mejorado
│       ├── classification.py  # Clasificación de documentos
│       ├── metadata.py        # Extracción de metadatos
│       ├── pipeline.py        # Pipeline de procesamiento
│       ├── summarization.py   # Resumen NLP extractivo offline
│       ├── document_types.py  # Gestión de tipos de documento
│       └── audit.py           # Registro de auditoría
├── ejemplos/           # PDFs de ejemplo para pruebas
├── media/              # Archivos subidos por usuarios
├── scripts/            # Scripts de utilidad
├── static/             # Archivos estáticos (CSS, JS, imágenes)
├── templates/          # Plantillas HTML
│   ├── base/           # Plantillas base
│   ├── core/           # Dashboard
│   ├── documents/      # Plantillas de documentos
│   ├── manager/        # Plantillas del panel de manager
│   ├── audit/          # Plantillas de auditoría
│   └── registration/   # Plantillas de autenticación
├── manage.py           # Utilidad de gestión de Django
└── requirements.txt    # Dependencias del proyecto
```

## 🔧 Configuración

### Variables de Entorno

Para producción, se recomienda usar variables de entorno para configuraciones sensibles:

```python
# En settings.py
import environ

env = environ.Env()
environ.Env.read_env()

SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)
```

### Configuración de OCR

El sistema utiliza una estrategia híbrida mejorada para OCR:

- **Extracción primaria**: Texto embebido nativo del PDF (más rápida y precisa)
- **Fallback OCR**: Si el texto nativo es insuficiente (< 200 caracteres), activa el OCR
- **Multi-PSM**: Prueba automáticamente múltiples modos PSM (3, 6, 4) para encontrar el mejor resultado
- **Binarización adaptativa**: Prueba múltiples umbrales (140, 160, 180) para optimizar la imagen
- **DPI**: 300 (alta calidad para escaneos)
- **OEM**: 1 (LSTM - mejor calidad)
- **Idiomas**: español + inglés (`spa+eng`)

Puedes ajustar estos parámetros en `documents/services/extraction.py`.

### Configuración de Resumen NLP

El resumen se genera automáticamente al procesar cada documento:

- **Algoritmo principal**: LexRank (basado en grafos, mejor calidad)
- **Algoritmo de respaldo**: Luhn (si LexRank falla)
- **Fallback final**: Extracto de los primeros 1500 caracteres del texto
- **Oraciones**: 8 oraciones por defecto (configurable en `summarization.py`)
- **Idioma**: español

El resumen se almacena en el campo `summary` del modelo `Document` y se muestra en la lista de publicados y en el detalle del documento.

## 📚 Uso

### 1. Tipos de Documentos

Los tipos de documento se gestionan desde el panel de administración o se cargan automáticamente con:

```bash
python manage.py seed_document_types
```

Tipos predeterminados:
- **CONTRACT** - Contrato
- **PO** - Orden de compra
- **CERT** - Certificación

### 2. Cargar Documentos

1. Accede a la sección de documentos
2. Haz clic en "Nuevo Documento"
3. Selecciona el tipo de documento
4. Sube el archivo PDF
5. El sistema automáticamente:
   - Extrae el texto (con OCR si es necesario)
   - Genera un resumen NLP extractivo
   - Sugiere una clasificación
   - Extrae metadatos clave

### 3. Revisar y Validar

1. Revisa el texto extraído, el resumen y los metadatos sugeridos
2. Corrige cualquier información incorrecta
3. Valida el documento para marcarlo como revisado
4. Publica el documento cuando esté listo

### 4. Auditoría

Todas las acciones quedan registradas en el sistema de auditoría, incluyendo:
- Carga de documentos
- Extracción OCR
- Revisiones y guardados
- Validaciones
- Publicaciones
- Habilitación / inhabilitación
- Descargas
- Inicios y cierres de sesión

## 🧪 Desarrollo

### Ejecutar Tests

```bash
python manage.py test
```

### Diagnóstico de Extracción OCR

Para verificar que Tesseract y Poppler funcionan correctamente:

```bash
python manage.py test_extraction <ruta_al_pdf>
```

### Crear Migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### Recolectar Archivos Estáticos

```bash
python manage.py collectstatic
```

## 🔒 Seguridad

- Cambia el `SECRET_KEY` en producción
- Configura `DEBUG = False` en producción
- Configura `ALLOWED_HOSTS` apropiadamente
- Usa HTTPS en producción
- Implementa backups regulares de la base de datos PostgreSQL
- No expongas las credenciales de PostgreSQL en el código fuente; usa variables de entorno

## 📝 Modelos de Datos

### DocumentType

- Tipos de documento configurables (código, nombre, descripción, activo)
- Tipos predeterminados: CONTRACT, PO, CERT

### Document

- Documento principal con título, tipo, estado y texto extraído
- **Campo `summary`**: Resumen extractivo generado automáticamente por NLP
- **Campo `ocr_confidence`**: Confianza promedio del OCR (0-100)
- Estados: `DRAFT`, `VALIDATED`, `PUBLISHED`

### DocumentVersion

- Versionado de archivos
- Almacena hash SHA256 para integridad

### DocumentMetadata

- Metadatos extraídos: fechas (principal, inicio, fin), montos, referencias, partes

### AuditLog

- Registro completo de auditoría con IP, user agent y metadatos
- Acciones: UPLOAD, OCR_EXTRACT, REVIEW_SAVE, VALIDATE, PUBLISH, ENABLE, DISABLE, LOGIN, LOGOUT, DOWNLOAD

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es privado y confidencial.

## 👥 Autores

- Equipo de Desarrollo Midas Gestor

## 🐛 Reportar Problemas

Si encuentras algún problema o tienes sugerencias, por favor crea un issue en el repositorio.

## 📞 Soporte

Para soporte técnico, contacta al equipo de desarrollo.
