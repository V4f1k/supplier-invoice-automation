# Změny v kódu pro N8N integraci

## Datum: 2025-09-09

### 1. Surya OCR - Aktualizace na verzi 0.6.13

**Soubor: `app/services/ocr_service.py`**

#### Změněné importy:
```python
# Původní:
from surya.ocr import run_ocr
from surya.model.detection.model import load_model as load_detection_model
from surya.model.recognition.model import load_model as load_recognition_model
from surya.input.load import load_from_file

# Nové:
from surya.foundation import FoundationPredictor
from surya.recognition import RecognitionPredictor
from surya.detection import DetectionPredictor
```

#### Změněná inicializace modelů:
```python
# Původní:
self.detection_model = load_detection_model()
self.recognition_model = load_recognition_model()

# Nové:
self.foundation_predictor = FoundationPredictor()
self.recognition_predictor = RecognitionPredictor(self.foundation_predictor)
self.detection_predictor = DetectionPredictor()
```

#### Změněné OCR volání:
```python
# Původní:
predictions = run_ocr(images, [["en"]] * len(images), self.detection_model, self.recognition_model)

# Nové:
predictions = self.recognition_predictor([image], det_predictor=self.detection_predictor)
```

### 2. Docker konfigurace

**Soubor: `Dockerfile`**

Přidány OpenGL knihovny pro Surya OCR:
```dockerfile
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1
```

**Soubor: `docker-compose.yml`**

Změněn port binding pro přístup z Tailscale sítě:
```yaml
# Původní:
ports:
  - "8000:8000"

# Nové:
ports:
  - "0.0.0.0:8000:8000"
```

### 3. Nový endpoint pro N8N

**Soubor: `app/api/v1/endpoints.py`**

#### Přidané importy:
```python
import base64
from typing import Optional
from pydantic import BaseModel
```

#### Přidané modely:
```python
class N8NBinaryFile(BaseModel):
    """Model for N8N binary file data"""
    data: str  # Base64 encoded file data
    mimeType: Optional[str] = "application/pdf"
    fileName: Optional[str] = "invoice.pdf"

class N8NRequest(BaseModel):
    """Model for N8N request with binary file"""
    file: Optional[N8NBinaryFile] = None
    file_base64: Optional[str] = None
    filename: Optional[str] = None
    content_type: Optional[str] = None
```

#### Nový endpoint:
```python
@router.post("/extract-n8n", response_model=ExtractionResponse)
async def extract_invoice_n8n(request: N8NRequest) -> ExtractionResponse:
    """
    Extract structured data from N8N binary file format
    
    Přijímá base64 encoded soubor z N8N workflow
    Podporuje různé formáty vstupních dat:
    - file.data (N8N binary format)
    - file_base64 (alternativní pole)
    """
```

### 4. Opravy AI service volání

**Soubor: `app/api/v1/endpoints.py`**

```python
# Původní:
ai_service = await get_ai_service()

# Nové (get_ai_service není async):
ai_service = get_ai_service()
```

### 5. Oprava cache ukládání

**Soubor: `app/api/v1/endpoints.py`**

```python
# Původní:
cache_data = response_data.model_dump()

# Nové (kompatibilní s dict i Pydantic model):
if hasattr(response_data, 'model_dump'):
    cache_data = response_data.model_dump()
else:
    cache_data = response_data if isinstance(response_data, dict) else response_data.__dict__
```

## Použití

### Původní endpoint (multipart/form-data):
```bash
curl -X POST "http://100.84.233.27:8000/extract" \
  -F "file=@faktura.pdf"
```

### Nový N8N endpoint (base64 JSON):
```bash
curl -X POST "http://100.84.233.27:8000/extract-n8n" \
  -H "Content-Type: application/json" \
  -d '{
    "file": {
      "data": "<base64_encoded_file>",
      "mimeType": "application/pdf",
      "fileName": "faktura.pdf"
    }
  }'
```

## N8N Workflow konfigurace

Pro použití s N8N:
1. Webhook přijímá binary data s `binaryData: true` a `rawBody: true`
2. Code node připraví binary data pro HTTP Request
3. HTTP Request volá endpoint `/extract-n8n` s JSON obsahujícím base64 data

## Známé problémy

1. N8N má problém s posíláním binary dat jako multipart/form-data
2. Proto byl vytvořen nový endpoint přijímající base64 encoded data v JSON
3. Tailscale IP adresa (100.84.233.27) musí být použita pro komunikaci mezi N8N serverem a OCR službou