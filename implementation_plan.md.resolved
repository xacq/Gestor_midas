# Mejora de Extracción de Texto y Resumen NLP Offline

Mejorar la calidad de extracción de texto (OCR + PDF nativo) y agregar un resumen automático del documento usando PLN (Procesamiento de Lenguaje Natural) offline, sin dependencia de internet ni APIs externas.

## Diagnóstico del Problema Actual

Los documentos extraen poco o nada de texto. Las causas probables son:

1. **PSM fijo en 6** — `--psm 6` asume "bloque de texto uniforme", lo cual falla en documentos con tablas, columnas o layouts mixtos
2. **Umbral de binarización fijo** (160) — No se adapta a la calidad/contraste del documento
3. **OCR nunca captura confianza** — `ocr_confidence` siempre queda en `None`, no hay forma de saber si el OCR leyó bien
4. **Normalización agresiva** — Líneas con >15% de "símbolos raros" se eliminan, pero estos pueden ser caracteres legítimos mal reconocidos
5. **Sin logging de diagnóstico** — Si la extracción falla, no hay forma de saber por qué
6. **Sin fallback de PSM** — Si `psm 6` falla, no intenta otros modos

## Proposed Changes

### Componente 1: Mejora de Extracción (`documents/services`)

#### [MODIFY] [extraction.py](file:///c:/midas_gestor/documents/services/extraction.py)

Mejoras principales:

- **Múltiples modos PSM con fallback**: Intentar PSM 3 (auto), y si produce poco texto, probar PSM 6 (bloque uniforme) y PSM 4 (columna). Quedarse con el que produzca más texto
- **Captura de confianza real**: Usar `pytesseract.image_to_data()` para obtener scores de confianza por palabra y calcular el promedio
- **Preprocesamiento adaptativo**: Aplicar múltiples umbrales de binarización (140, 160, 180) y elegir el que dé mejor resultado
- **Redimensionado**: Escalar imágenes pequeñas o de baja resolución antes del OCR
- **Normalización menos agresiva**: Reducir el umbral de eliminación de caracteres raros y ser más tolerante
- **Logging detallado**: Agregar `logging` para trazar qué sucede en cada etapa

#### [MODIFY] [pipeline.py](file:///c:/midas_gestor/documents/services/pipeline.py)

- Capturar y almacenar el `ocr_confidence` real que ahora devuelve la extracción mejorada
- Agregar logging del pipeline completo
- Agregar try/except con logging para que los errores no pasen desapercibidos

---

### Componente 2: Resumen Extractivo con NLP Offline

#### Librería elegida: **sumy** + **NLTK**

- **sumy**: Librería dedicada a resumen extractivo. Soporta LexRank (basado en similitud de oraciones) y LSA (Análisis Semántico Latente). Funciona 100% offline
- **NLTK**: Necesario para tokenización en español. Se descarga el modelo `punkt_tab` una vez y trabaja offline
- **Sin IA ni APIs**: Todo corre en la propia máquina, ideal para LAN bancaria

#### [NEW] [summarization.py](file:///c:/midas_gestor/documents/services/summarization.py)

Nuevo servicio que:
- Recibe el texto extraído del documento
- Usa `sumy.parsers.plaintext.PlaintextParser` con tokenización NLTK en español
- Aplica **LexRank** como algoritmo primario (buen balance calidad/velocidad para documentos legales/comerciales)
- Genera un resumen de N oraciones (configurable, default ~5 oraciones)
- Fallback: si el texto es muy corto (<3 oraciones), devuelve el texto completo sin resumir

#### [MODIFY] [models.py](file:///c:/midas_gestor/documents/models.py)

- Agregar campo `summary = models.TextField(blank=True, default="")` al modelo `Document`
- Migración necesaria

#### [MODIFY] [pipeline.py](file:///c:/midas_gestor/documents/services/pipeline.py)

- Agregar paso 4: después de la extracción de metadatos, generar el resumen y guardarlo en `doc.summary`

#### [MODIFY] [detail.html](file:///c:/midas_gestor/templates/documents/detail.html)

- Mostrar el resumen generado en la vista de detalle del documento (visible para usuarios)

#### [MODIFY] [review.html](file:///c:/midas_gestor/templates/documents/review.html)

- Mostrar el resumen en la vista de revisión (visible para admin durante validación)

#### [MODIFY] [published_list.html](file:///c:/midas_gestor/templates/documents/published_list.html)

- Mostrar un extracto del resumen (truncado) en la tarjeta de cada documento en el listado

---

### Componente 3: Dependencias

#### [MODIFY] [requirements.txt](file:///c:/midas_gestor/requirements.txt)

Agregar:
```
sumy==0.11.0
nltk==3.9.1
```

#### Script de setup NLTK

Después de instalar, ejecutar una sola vez:
```python
import nltk
nltk.download('punkt_tab')
```

> [!IMPORTANT]
> **Descarga única**: Los datos de NLTK (`punkt_tab`) se descargan una vez durante la instalación (requiere internet solo en ese momento). Después funcionan completamente offline. En la LAN del banco, se pueden copiar los archivos de datos manualmente si no hay internet.

---

## User Review Required

> [!IMPORTANT]
> **Nuevas dependencias**: Se agregarán `sumy` y `nltk`. Ambas funcionan 100% offline después de la instalación inicial. ¿Hay alguna restricción en las librerías que se pueden instalar?

> [!WARNING]
> **Migración de base de datos**: Se agregará un campo `summary` al modelo `Document`. Esto requiere ejecutar `python manage.py makemigrations` y `python manage.py migrate`. ¿Es aceptable?

---

## Verification Plan

### Test automatizado: Script de diagnóstico

Se creará un management command `test_extraction.py` que:
1. Toma un PDF existente de `media/documents/`
2. Ejecuta la extracción mejorada
3. Imprime: texto extraído (primeros 500 chars), confianza OCR, método usado, resumen generado
4. Permite comparar antes/después

```bash
python manage.py test_extraction <document_id>
```

### Verificación manual por el usuario

1. **Subir un documento PDF** por la interfaz web (`/documents/upload/`)
2. **Ir a borradores** (`/documents/drafts/`) → ver que se extrajo texto
3. **Revisar el documento** (`/documents/review/<pk>/`) → verificar que aparece el resumen
4. **Publicar el documento** → ir al detalle como usuario → confirmar que el resumen y metadatos se muestran

> [!NOTE]
> Sería muy útil que me compartas o me indiques qué tipo de PDFs estás usando (¿son escaneos, PDFs digitales, PDFs con tablas?) para poder ajustar mejor el OCR. ¿Puedes confirmar?
