# 📄 N8N HTTP Request - Nastavení pro Invoice Extraction

Tento návod popisuje, jak nastavit N8N HTTP Request node pro komunikaci s invoice extraction službou.

## 🎯 **Přehled**

Invoice extraction služba nabízí 3 endpointy:
- `/extract` - pro multipart/form-data upload
- `/extract-n8n` - pro komplexní N8N binary data
- `/extract-simple` - **DOPORUČENO** - nejjednoduší pro N8N

## 🚀 **Doporučené nastavení - `/extract-simple`**

### **1. Základní konfigurace HTTP Request node**

```
┌─────────────────────────────────────┐
│          HTTP Request               │
├─────────────────────────────────────┤
│ Method: POST                        │
│ URL: http://your-server:8000/extract-simple │
│ Authentication: None                │
│ Content-Type: application/json      │
└─────────────────────────────────────┘
```

### **2. Request Headers**
```json
{
  "Content-Type": "application/json",
  "Accept": "application/json"
}
```

### **3. Request Body (JSON)**
```json
{
  "data": "{{ $binary.data.data }}",
  "filename": "{{ $binary.data.fileName || 'faktura.pdf' }}",
  "mimetype": "{{ $binary.data.mimeType || 'application/pdf' }}"
}
```

### **4. Kompletní N8N Workflow Example**

```json
{
  "nodes": [
    {
      "name": "Read Binary File",
      "type": "n8n-nodes-base.readBinaryFile",
      "position": [240, 300],
      "parameters": {
        "filePath": "/path/to/your/faktura.pdf"
      }
    },
    {
      "name": "Convert to Base64",
      "type": "n8n-nodes-base.function",
      "position": [440, 300],
      "parameters": {
        "functionCode": "// Convert binary data to base64\nconst binaryData = $input.first().binary.data;\nreturn [{\n  json: {\n    data: binaryData.data,\n    filename: binaryData.fileName || 'faktura.pdf',\n    mimetype: binaryData.mimeType || 'application/pdf'\n  }\n}];"
      }
    },
    {
      "name": "Invoice Extraction",
      "type": "n8n-nodes-base.httpRequest",
      "position": [640, 300],
      "parameters": {
        "method": "POST",
        "url": "http://localhost:8000/extract-simple",
        "options": {
          "headers": {
            "Content-Type": "application/json"
          }
        },
        "body": {
          "data": "={{ $json.data }}",
          "filename": "={{ $json.filename }}",
          "mimetype": "={{ $json.mimetype }}"
        }
      }
    }
  ],
  "connections": {
    "Read Binary File": {
      "main": [[{
        "node": "Convert to Base64",
        "type": "main",
        "index": 0
      }]]
    },
    "Convert to Base64": {
      "main": [[{
        "node": "Invoice Extraction",
        "type": "main",
        "index": 0
      }]]
    }
  }
}
```

## 📋 **Response Format**

### **✅ Success Response (HTTP 200)**
```json
{
  "invoice_number": "FV5040011231",
  "invoice_date": "2025-09-05",
  "due_date": "2025-10-05",
  "vendor_name": "ELKOV elektro a.s.",
  "vendor_address": "Kšírova 701/255\\n619 00 Brno",
  "customer_name": "iSolar PV s.r.o.",
  "customer_address": "Hronovická 663\\n53002 Pardubice",
  "subtotal": 773.25,
  "tax": 162.38,
  "total": 936.0,
  "currency": "CZK",
  "items": [
    {
      "description": "EST G GW42201 KRABICE NOUZ. VYP. TLAČ.120X120X50 (POŽÁR.) IP55",
      "quantity": 1.0,
      "unit_price": 620.51,
      "total_price": 620.51
    },
    {
      "description": "Ekologický poplatek",
      "quantity": 1.0,
      "unit_price": 0.26,
      "total_price": 0.26
    }
  ]
}
```

### **❌ Error Response (HTTP 400/500)**
```json
{
  "success": false,
  "error": "Invalid file type",
  "error_code": "INVALID_FILE_TYPE",
  "detail": "Supported types: application/pdf, image/png, image/jpeg, image/jpg",
  "timestamp": "2025-09-09T14:28:11.596692"
}
```

## ⚙️ **Pokročilé nastavení**

### **Načítání souboru z FileSystem Trigger**
```javascript
// Function node pro zpracování FileSystem triggeru
const filePath = $json.path;
const fs = require('fs');

// Read file and convert to base64
const fileContent = fs.readFileSync(filePath);
const base64Data = fileContent.toString('base64');

return [{
  json: {
    data: base64Data,
    filename: filePath.split('/').pop(),
    mimetype: 'application/pdf'
  }
}];
```

### **Error Handling**
```javascript
// Function node pro error handling
if ($json.success === false) {
  throw new Error(`Invoice extraction failed: ${$json.error} (${$json.error_code})`);
}

// Process successful response
return [{
  json: {
    extracted_data: $json,
    processed_at: new Date().toISOString(),
    status: 'success'
  }
}];
```

## 🔍 **Supported File Types**
- `application/pdf` ✅
- `image/png` ✅  
- `image/jpeg` ✅
- `image/jpg` ✅

## 📏 **Limits**
- **Maximum file size:** 10MB
- **Processing time:** ~15-20 seconds per invoice
- **Supported languages:** Czech, English (optimized for Czech invoices)

## 🐛 **Troubleshooting**

### **Common Issues:**

1. **"Invalid base64 data"**
   - Ujistěte se, že `data` field obsahuje správný base64 string
   - Zkontrolujte, že neposíláte data URL prefix (`data:application/pdf;base64,`)

2. **"Invalid file type"**
   - Zkontrolujte `mimetype` field
   - Podporované typy: `application/pdf`, `image/png`, `image/jpeg`, `image/jpg`

3. **"File too large"**
   - Maximum je 10MB
   - Pro větší soubory použijte kompresní/resize před odesláním

4. **Timeout**
   - Nastavte timeout na min 30 sekund
   - OCR + AI processing trvá 15-20 sekund

### **Debug Tips:**
1. Použijte `/health/detailed` endpoint pro kontrolu služby
2. Zkontrolujte logy v N8N pro podrobné error zprávy
3. Otestujte s menším PDF souborem nejprve

## 🔗 **Další endpointy**

### **Health Check**
```
GET /health/detailed
```
Response:
```json
{
  "status": "ok",
  "timestamp": "2025-09-09T14:28:11.575Z",
  "services": {
    "cache": "ok",
    "ai_service": "ok", 
    "ocr": "ok"
  },
  "endpoints": ["/health", "/health/detailed", "/extract", "/extract-n8n", "/extract-simple"],
  "supported_file_types": ["application/pdf", "image/png", "image/jpeg", "image/jpg"],
  "max_file_size_mb": 10
}
```

---

## 💡 **Tips pro optimální výsledky:**

1. **Kvalitní PDF:** Použijte PDF s čitelným textem
2. **Správný formát:** Elektronické faktury fungují lépe než skenované
3. **Český obsah:** Služba je optimalizovaná pro české faktury
4. **Caching:** Stejné soubory jsou cachovány pro rychlejší odpověď

**🎯 Pro nejlepší výsledky použijte `/extract-simple` endpoint s čistým JSON formátem!**