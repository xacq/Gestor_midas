# Midas Gestor

Sistema de gestión documental inteligente con capacidades de OCR, clasificación automática y extracción de metadatos para documentos empresariales.

## 📋 Descripción

Midas Gestor es una aplicación web Django diseñada para gestionar documentos empresariales (contratos, órdenes de compra, certificados, etc.) con procesamiento automático mediante OCR, clasificación inteligente y extracción de metadatos clave.

### Características Principales

- **Gestión de Documentos**: Sistema completo de carga, versionado y organización de documentos
- **OCR Inteligente**: Extracción automática de texto de documentos escaneados usando Tesseract OCR
- **Clasificación Automática**: Sugerencias de clasificación de documentos por tipo
- **Extracción de Metadatos**: Identificación automática de fechas, montos, números de referencia y partes involucradas
- **Sistema de Auditoría**: Registro completo de todas las acciones realizadas en el sistema
- **Control de Versiones**: Manejo de múltiples versiones de documentos
- **Autenticación y Permisos**: Sistema de usuarios con control de acceso

## 🛠️ Tecnologías

- **Backend**: Django 4.2.16
- **Base de Datos**: SQLite (desarrollo)
- **OCR**: Tesseract OCR + pytesseract
- **Procesamiento PDF**: pypdf, pdf2image
- **Frontend**: Bootstrap 5 (crispy-forms)
- **Imágenes**: Pillow

## 📦 Requisitos Previos

### Software Requerido

Antes de instalar el proyecto, debes tener instalado:

1. **Python 3.8+**
2. **Tesseract OCR**
3. **Poppler**

### Instalación de Tesseract OCR

#### Windows

1. Descarga el instalador desde: https://github.com/UB-Mannheim/tesseract/wiki
2. Ejecuta el instalador y anota la ruta de instalación (por defecto: `C:\Program Files\Tesseract-OCR`)
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

### 5. Configurar Rutas de Tesseract y Poppler

Edita el archivo `config/settings.py` y ajusta las siguientes variables según tu instalación:

```python
# Windows (ejemplo)
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESSDATA_DIR = r"C:\Program Files\Tesseract-OCR\tessdata"
POPPLER_PATH = r"C:\poppler\Library\bin"
TESSDATA_PREFIX = r"C:\Program Files\Tesseract-OCR"

# Linux/macOS (generalmente no es necesario configurar estas rutas)
# TESSERACT_CMD = "/usr/bin/tesseract"
# TESSDATA_DIR = "/usr/share/tesseract-ocr/4.00/tessdata"
```

### 6. Crear Base de Datos

```bash
python manage.py migrate
```

### 7. Crear Superusuario

```bash
python manage.py createsuperuser
```

### 8. Ejecutar Servidor de Desarrollo

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
│   ├── forms.py        # Formularios
│   ├── services/       # Lógica de negocio
│   │   ├── extraction.py      # Extracción de texto y OCR
│   │   ├── classification.py  # Clasificación de documentos
│   │   ├── metadata.py        # Extracción de metadatos
│   │   ├── pipeline.py        # Pipeline de procesamiento
│   │   └── audit.py           # Registro de auditoría
│   └── templatetags/   # Template tags personalizados
├── media/              # Archivos subidos por usuarios
├── static/             # Archivos estáticos (CSS, JS, imágenes)
├── templates/          # Plantillas HTML
│   ├── base/           # Plantillas base
│   ├── documents/      # Plantillas de documentos
│   └── audit/          # Plantillas de auditoría
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

El sistema utiliza configuraciones optimizadas para OCR:

- **DPI**: 300 (alta calidad para escaneos)
- **OEM**: 1 (LSTM - mejor calidad)
- **PSM**: 6 (bloque de texto uniforme)
- **Idiomas**: español + inglés (`spa+eng`)

Puedes ajustar estos parámetros en `documents/services/extraction.py`.

## 📚 Uso

### 1. Tipos de Documentos

Primero, define los tipos de documentos en el panel de administración:
- Contratos (CONTRACT)
- Órdenes de Compra (PO)
- Certificados (CERT)
- etc.

### 2. Cargar Documentos

1. Accede a la sección de documentos
2. Haz clic en "Nuevo Documento"
3. Selecciona el tipo de documento
4. Sube el archivo PDF
5. El sistema automáticamente:
   - Extrae el texto (con OCR si es necesario)
   - Sugiere una clasificación
   - Extrae metadatos clave

### 3. Revisar y Validar

1. Revisa el texto extraído y los metadatos sugeridos
2. Corrige cualquier información incorrecta
3. Valida el documento para marcarlo como revisado
4. Publica el documento cuando esté listo

### 4. Auditoría

Todas las acciones quedan registradas en el sistema de auditoría, incluyendo:
- Carga de documentos
- Extracción OCR
- Revisiones
- Validaciones
- Publicaciones

## 🧪 Desarrollo

### Ejecutar Tests

```bash
python manage.py test
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
- Implementa backups regulares de la base de datos

## 📝 Modelos de Datos

### Document
- Documento principal con título, tipo, estado y texto extraído
- Estados: DRAFT, VALIDATED, PUBLISHED

### DocumentVersion
- Versionado de archivos
- Almacena hash SHA256 para integridad

### DocumentMetadata
- Metadatos extraídos: fechas, montos, referencias, partes

### AuditLog
- Registro completo de auditoría con IP, user agent y metadatos

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
