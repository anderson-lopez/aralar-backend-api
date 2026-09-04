# 🌍 Ejemplos Prácticos: Google Translate API

## 🚀 Configuración Rápida

### **1. Configurar Variables de Entorno**
```bash
# En tu archivo .env
I18N_PROVIDER=google
GOOGLE_API_KEY=AIzaSyC-tu-api-key-aqui
GOOGLE_BASE_URL=https://translation.googleapis.com/language/translate/v2
```

### **2. Obtener API Key de Google**
1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un proyecto o selecciona uno existente
3. Habilita la **Cloud Translation API**
4. Ve a **Credenciales** → **Crear credenciales** → **Clave de API**
5. Copia la clave y úsala como `GOOGLE_API_KEY`

---

## 📋 Casos de Uso Reales

### **Caso 1: Restaurante Asiático**
```bash
# Crear glosario para restaurante chino
POST /i18n/glossaries
{
  "tenant_id": "dragon-palace",
  "source_lang": "zh",
  "target_lang": "es",
  "pairs": [
    {"宫保鸡丁": "Pollo Kung Pao"},
    {"麻婆豆腐": "Tofu Ma Po"},
    {"北京烤鸭": "Pato Pekinés"}
  ]
}

# Traducir menú chino
POST /i18n/translate
{
  "texts": ["宫保鸡丁配米饭", "麻婆豆腐很辣", "北京烤鸭特色菜"],
  "source_lang": "zh",
  "target_lang": "es",
  "tenant_id": "dragon-palace",
  "use_glossary": true
}

# Resultado esperado:
{
  "items": [
    {
      "source": "宫保鸡丁配米饭",
      "translated": "Pollo Kung Pao con arroz",
      "cached": false
    },
    {
      "source": "麻婆豆腐很辣", 
      "translated": "Tofu Ma Po muy picante",
      "cached": false
    },
    {
      "source": "北京烤鸭特色菜",
      "translated": "Pato Pekinés plato especial",
      "cached": false
    }
  ]
}
```

---

### **Caso 2: Restaurante Árabe**
```bash
# DeepL NO soporta árabe, pero Google SÍ
POST /i18n/glossaries
{
  "tenant_id": "al-andalus",
  "source_lang": "ar", 
  "target_lang": "es",
  "pairs": [
    {"حمص": "Hummus Tradicional"},
    {"فلافل": "Falafel Casero"},
    {"تبولة": "Tabulé Libanés"}
  ]
}

POST /i18n/translate
{
  "texts": ["حمص بالطحينة", "فلافل مع الخضار", "تبولة طازجة"],
  "source_lang": "ar",
  "target_lang": "es", 
  "tenant_id": "al-andalus",
  "use_glossary": true
}
```

---

### **Caso 3: Detección Automática de Idioma**
```bash
# Google es mejor para detectar idiomas
POST /i18n/detect
{
  "texts": [
    "สวัสดี",           # Tailandés
    "こんにちは",         # Japonés  
    "مرحبا",            # Árabe
    "Xin chào",         # Vietnamita
    "नमस्ते"            # Hindi
  ]
}

# Resultado:
{
  "items": [
    {"text": "สวัสดี", "lang": "th"},
    {"text": "こんにちは", "lang": "ja"},
    {"text": "مرحبا", "lang": "ar"},
    {"text": "Xin chào", "lang": "vi"},
    {"text": "नमस्ते", "lang": "hi"}
  ]
}
```

---

## 🔄 Comparación DeepL vs Google

### **Ejemplo: Restaurante Italiano**

#### **Texto Original:**
```
"Pasta alla carbonara con guanciale autentico y pecorino romano"
```

#### **Con DeepL (I18N_PROVIDER=deepl):**
```bash
POST /i18n/translate
{
  "texts": ["Pasta alla carbonara con guanciale autentico y pecorino romano"],
  "source_lang": "es",
  "target_lang": "en"
}

# Resultado DeepL:
"Pasta alla carbonara with authentic guanciale and pecorino romano"
```

#### **Con Google (I18N_PROVIDER=google):**
```bash
# Mismo request, diferente resultado
"Carbonara pasta with authentic guanciale and pecorino romano"
```

**Análisis:**
- **DeepL**: Mantiene "Pasta alla carbonara" (más auténtico)
- **Google**: Traduce a "Carbonara pasta" (más genérico)

---

## 🌏 Idiomas Únicos de Google

### **Idiomas que SOLO Google Soporta:**
```json
{
  "asiáticos": ["th", "vi", "hi", "bn", "ta", "te", "ml", "kn", "gu"],
  "africanos": ["sw", "zu", "xh", "af", "ig", "yo", "ha"],
  "otros": ["he", "fa", "ur", "ka", "am", "my", "km", "lo"]
}
```

### **Ejemplo Multi-idioma:**
```bash
POST /i18n/translate
{
  "texts": ["Bienvenidos a nuestro restaurante"],
  "source_lang": "es",
  "target_lang": "th",  # Tailandés - Solo Google
  "tenant_id": "global-restaurant"
}

# Resultado:
"ยินดีต้อนรับสู่ร้านอาหารของเรา"
```

---

## ⚡ Optimización de Costos

### **Estrategia Híbrida:**
```python
# Pseudocódigo para optimizar costos
def choose_provider(source_lang, target_lang):
    # Usar DeepL para calidad premium en idiomas europeos
    if source_lang in ['es', 'fr', 'de', 'it'] and target_lang == 'en':
        return "deepl"
    
    # Usar Google para idiomas que DeepL no soporta
    if source_lang in ['ar', 'th', 'vi', 'hi', 'zh'] or target_lang in ['ar', 'th', 'vi', 'hi']:
        return "google"
    
    # Usar Google como fallback (más barato)
    return "google"
```

---

## 🔧 Troubleshooting

### **Error Común: API Key Inválida**
```json
{
  "error": {
    "code": 400,
    "message": "API key not valid. Please pass a valid API key."
  }
}
```
**Solución:** Verifica que `GOOGLE_API_KEY` esté correctamente configurada.

### **Error: Idioma No Soportado**
```json
{
  "error": {
    "code": 400, 
    "message": "Invalid Value"
  }
}
```
**Solución:** Usa códigos ISO 639-1 (es, en, fr) no ISO 639-2 (spa, eng, fra).

### **Error: Cuota Excedida**
```json
{
  "error": {
    "code": 429,
    "message": "Quota exceeded"
  }
}
```
**Solución:** Implementar rate limiting o aumentar cuota en Google Cloud.

---

## 💰 Comparación de Costos (Estimado)

| Proveedor | Costo por 1M caracteres | Idiomas | Calidad |
|-----------|-------------------------|---------|---------|
| **DeepL** | $20-25 | ~30 | ⭐⭐⭐⭐⭐ |
| **Google** | $10-15 | 100+ | ⭐⭐⭐⭐ |

**Recomendación:** Usa Google para volumen alto y DeepL para calidad premium.
