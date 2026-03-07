# Análisis de Requisitos — Gestor MIDAS

## Descripción del Sistema

**Gestor MIDAS** es un sistema de gestión documental construido con Django 4.2, que permite cargar, procesar (con OCR/extracción de texto), clasificar, revisar y publicar documentos PDF. Implementa dos roles de usuario, tres tipos de documentos y un sistema de auditoría completo.

---

## ✅ Verificación de Requisitos

### 1. Dos Roles: Admin y Usuario

| Requisito | ¿Implementado? | Detalles |
|-----------|:-:|-----------|
| Rol **Admin** | ✅ | Controlado por `@staff_member_required` (campo `is_staff` de Django). El admin puede cargar, revisar, validar y publicar documentos. |
| Rol **User** (usuario) | ✅ | Controlado por `@login_required`. Cualquier usuario autenticado puede ver documentos publicados y acceder a su detalle. |
| Separación de permisos | ✅ | Las vistas de admin ([upload](file:///c:/midas_gestor/documents/views.py#70-121), [drafts_list](file:///c:/midas_gestor/documents/views.py#126-135), [review](file:///c:/midas_gestor/documents/views.py#143-241), [audit](file:///c:/midas_gestor/documents/views_audit.py#7-26)) exigen `is_staff=True`. Las vistas de usuario ([published_list](file:///c:/midas_gestor/documents/views.py#14-51), [document_detail](file:///c:/midas_gestor/documents/views.py#53-68)) solo exigen autenticación. |

> [!NOTE]
> Existe además un grupo `GERENCIA` en [permissions.py](file:///c:/midas_gestor/documents/permissions.py) y una función [is_gerencia()](file:///c:/midas_gestor/documents/permissions.py#1-3), pero actualmente **no se utiliza** en ninguna vista. Podría servir para un tercer nivel de acceso en el futuro.

---

### 2. Admin: Levantamiento (Carga) y Lectura de Información Sensible

| Funcionalidad | ¿Implementado? | Archivo(s) |
|---------------|:-:|------------|
| **Carga de documentos** (upload PDF) | ✅ | [views.py](file:///c:/midas_gestor/documents/views.py) → [upload_document()](file:///c:/midas_gestor/documents/views.py#70-121), [upload.html](file:///c:/midas_gestor/templates/documents/upload.html) |
| **Extracción automática de texto** (OCR + texto embebido) | ✅ | [extraction.py](file:///c:/midas_gestor/documents/services/extraction.py) — Extracción híbrida: primero texto embebido, luego OCR con Tesseract si es insuficiente |
| **Clasificación automática** del tipo de documento | ✅ | [classification.py](file:///c:/midas_gestor/documents/services/classification.py) — Basada en reglas regex por tipo |
| **Extracción de metadatos** (fechas, montos, partes, referencias) | ✅ | [metadata.py](file:///c:/midas_gestor/documents/services/metadata.py) |
| **Revisión y edición de metadatos** por admin | ✅ | [views.py](file:///c:/midas_gestor/documents/views.py) → [review_document()](file:///c:/midas_gestor/documents/views.py#143-241), [review.html](file:///c:/midas_gestor/templates/documents/review.html) |
| **Flujo de estados**: Borrador → Validado → Publicado | ✅ | `Document.Status` con choices `DRAFT`, `VALIDATED`, `PUBLISHED` |
| **Habilitar/Inhabilitar** documentos | ✅ | Campo `enabled` en [Document](file:///c:/midas_gestor/documents/models.py#19-54), controlable desde la revisión |
| **Vista de borradores** (solo admin) | ✅ | [drafts_list()](file:///c:/midas_gestor/documents/views.py#126-135) con `@staff_member_required` |
| **Log de auditoría** (solo admin) | ✅ | [views_audit.py](file:///c:/midas_gestor/documents/views_audit.py) con `@staff_member_required` |

---

### 3. Tres Tipos de Documentos (Clasificación)

| Tipo | Código | ¿Implementado? | Reglas de Clasificación |
|------|--------|:-:|-------------------------|
| **Contratos** | `CONTRACT` | ✅ | Busca: cláusulas, contratante, contratista, objeto, plazo, valor/monto |
| **Órdenes de Compra** | `PO` | ✅ | Busca: orden de compra, item, cantidad, proveedor, total |
| **Certificaciones** | `CERT` | ✅ | Busca: certifica/certificación, notaría, compareciente, fe de, sello/firma |

> [!TIP]
> Los tipos se manejan dinámicamente mediante el modelo [DocumentType](file:///c:/midas_gestor/documents/models.py#6-17), así que se pueden agregar nuevos tipos sin cambiar código. La clasificación automática, sin embargo, solo tiene reglas para estos 3 tipos.

---

### 4. Usuario: Acceso a Información, Descarga y Otras Opciones

| Funcionalidad | ¿Implementado? | Detalles |
|---------------|:-:|---------|
| **Listado de documentos publicados** | ✅ | [published_list.html](file:///c:/midas_gestor/templates/documents/published_list.html) — Solo muestra documentos con `status=PUBLISHED` y `enabled=True` |
| **Búsqueda** por título, texto, partes, referencia | ✅ | Filtros `Q()` en [published_list()](file:///c:/midas_gestor/documents/views.py#14-51) |
| **Filtrado por tipo** de documento | ✅ | Select de tipo en la vista de lista |
| **Detalle del documento** con metadatos | ✅ | [detail.html](file:///c:/midas_gestor/templates/documents/detail.html) — Muestra referencia, partes, fechas, monto |
| **Vista previa del PDF** (iframe) | ✅ | Embebido en la página de detalle |
| **Descarga del PDF** | ✅ | Botón "Abrir/Descargar PDF" con link directo al archivo |
| **Historial de versiones** | ✅ | Lista de versiones con número y fecha en el detalle |
| **Dashboard de gerencia** (KPIs) | ✅ | [views_manager.py](file:///c:/midas_gestor/documents/views_manager.py) — Contratos activos/por vencer, montos, etc. |

---

## 📊 Resumen de Conformidad

| Requisito Específico | Estado |
|----------------------|--------|
| Rol de Admin con capacidad de carga | ✅ **Cumple** |
| Rol de Admin con lectura de info sensible | ✅ **Cumple** |
| 3 tipos de documentos categorizados | ✅ **Cumple** |
| Rol de Usuario con acceso a documentos | ✅ **Cumple** |
| Descarga de documentos por usuario | ✅ **Cumple** |
| Separación de acceso entre roles | ✅ **Cumple** |

---

## ⚠️ Observaciones y Posibles Mejoras

| # | Observación | Severidad |
|---|------------|-----------|
| 1 | **Sin descarga restringida** — Los archivos PDF se sirven directamente desde `MEDIA_URL`. Un usuario que conozca la URL directa podría acceder sin autenticación (en modo `DEBUG=True` el `static()` de desarrollo no verifica autenticación). | ⚠️ Media |
| 2 | **Grupo GERENCIA** definido pero no utilizado en vistas — La función [is_gerencia()](file:///c:/midas_gestor/documents/permissions.py#1-3) existe en [permissions.py](file:///c:/midas_gestor/documents/permissions.py) pero ninguna vista la usa para controlar acceso. | ℹ️ Baja |
| 3 | **Paginación no implementada** — Las listas tienen un límite hardcoded (200 documentos, 300 logs) en lugar de paginación real. | ℹ️ Baja |
| 4 | **Sin registro de descarga en auditoría** — Se registran cargas, validaciones, publicaciones, pero **no las descargas** de usuarios, lo cual podría ser relevante para DLP (Data Loss Prevention). | ⚠️ Media |
| 5 | **Dashboard de gerencia sin restricción a grupo GERENCIA** — Usa `@login_required` en lugar de `@staff_member_required` o verificación de grupo, así que cualquier usuario autenticado puede acceder a los KPIs. | ⚠️ Media |
| 6 | **SECRET_KEY** insegura en settings — Usa el valor por defecto `django-insecure-`, solo apropiado para desarrollo. | ⚠️ Media (producción) |

---

## Arquitectura del Sistema

```mermaid
graph TD
    A[Usuario] -->|login_required| B[Listado Publicados]
    A -->|login_required| C[Detalle Documento]
    A -->|login_required| D[Dashboard Gerencia]
    C --> E[Vista previa PDF]
    C --> F[Descarga PDF]

    G[Admin] -->|staff_member_required| H[Subir Documento]
    G -->|staff_member_required| I[Lista Borradores]
    G -->|staff_member_required| J[Revisión/Validación]
    G -->|staff_member_required| K[Log Auditoría]

    H --> L[Pipeline Automático]
    L --> M[Extracción Texto/OCR]
    L --> N[Clasificación 3 Tipos]
    L --> O[Extracción Metadatos]
    
    J -->|Guardar/Validar/Publicar| P[Cambio de Estado]
    P -->|PUBLISHED + enabled| B
```

## Conclusión

**El sistema Gestor MIDAS sí cumple con los requisitos especificados:**
1. ✅ **Dos roles** (Admin / Usuario) con separación clara de permisos
2. ✅ **Admin**: carga y lectura de información sensible del documento
3. ✅ **3 tipos de documentos**: CONTRACT, PO, CERT
4. ✅ **Usuario**: acceso a información, descarga, búsqueda y filtrado

Las observaciones listadas son mejoras menores que no afectan el cumplimiento funcional de los requisitos base.
