# 🏔️ Ejemplo Práctico: Traducción con Euskera

## ✅ Problema Solucionado

**Antes:** Error 422 - "Must be one of: es, en, fr, de, it, pt, ru, ja, ko, zh, ar, auto"
**Ahora:** ✅ Euskera (eu) soportado junto con 100+ idiomas

---

## 🔧 Configuración Necesaria

### **1. Cambiar a Google Translate**
```bash
# En tu archivo .env
I18N_PROVIDER=google
GOOGLE_API_KEY=tu-api-key-de-google-cloud
GOOGLE_BASE_URL=https://translation.googleapis.com/language/translate/v2
```

**¿Por qué Google?** DeepL NO soporta euskera, pero Google SÍ.

### **2. Obtener API Key de Google**
1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea/selecciona un proyecto
3. Habilita **Cloud Translation API**
4. Crea credenciales → **API Key**
5. Copia la key a `GOOGLE_API_KEY`

---

## 🍽️ Ejemplo: Restaurante Vasco

### **Paso 1: Crear Glosario Euskera**
```bash
POST /i18n/glossaries
Content-Type: application/json

{
  "tenant_id": "etxe-berri-jatetxea",
  "source_lang": "eu",
  "target_lang": "es", 
  "pairs": [
    {"pintxo": "pincho"},
    {"txuleta": "chuletón"},
    {"bacalao al pil pil": "bacalao al pil pil"},
    {"marmitako": "marmitako"},
    {"txakoli": "txakolí"},
    {"idiazabal": "queso idiazábal"}
  ]
}
```

### **Paso 2: Traducir Menú Vasco**
```bash
POST /i18n/translate
Content-Type: application/json

{
  "texts": [
    "Gure pintxoak oso goxoak dira",
    "Txuleta erretzailea daukagu",
    "Marmitako tradizionala",
    "Idiazabal gazta eta txakoli"
  ],
  "source_lang": "eu",
  "target_lang": "es",
  "tenant_id": "etxe-berri-jatetxea",
  "use_glossary": true
}
```

### **Resultado Esperado:**
```json
{
  "provider": "google",
  "source_lang": "eu",
  "target_lang": "es",
  "items": [
    {
      "source": "Gure pintxoak oso goxoak dira",
      "translated": "Nuestros pinchos están muy ricos",
      "cached": false
    },
    {
      "source": "Txuleta erretzailea daukagu", 
      "translated": "Tenemos chuletón a la parrilla",
      "cached": false
    },
    {
      "source": "Marmitako tradizionala",
      "translated": "Marmitako tradicional",
      "cached": false
    },
    {
      "source": "Idiazabal gazta eta txakoli",
      "translated": "Queso idiazábal y txakolí", 
      "cached": false
    }
  ]
}
```

---

## 🔄 Detección Automática de Euskera

### **Detectar si un texto es euskera:**
```bash
POST /i18n/detect
Content-Type: application/json

{
  "texts": [
    "Kaixo, zer moduz?",
    "Pintxo bat mesedez",
    "Eskerrik asko",
    "Agur!"
  ]
}
```

### **Resultado:**
```json
{
  "items": [
    {"text": "Kaixo, zer moduz?", "lang": "eu"},
    {"text": "Pintxo bat mesedez", "lang": "eu"}, 
    {"text": "Eskerrik asko", "lang": "eu"},
    {"text": "Agur!", "lang": "eu"}
  ]
}
```

---

## 🌍 Otros Idiomas Regionales Españoles

### **Catalán (ca):**
```bash
POST /i18n/translate
{
  "texts": ["Pa amb tomàquet i pernil ibèric"],
  "source_lang": "ca",
  "target_lang": "es",
  "tenant_id": "restaurant-catala"
}

# Resultado: "Pan con tomate y jamón ibérico"
```

### **Gallego (gl):**
```bash
POST /i18n/translate
{
  "texts": ["Polbo á feira con cachelos"],
  "source_lang": "gl", 
  "target_lang": "es",
  "tenant_id": "marisqueria-galega"
}

# Resultado: "Pulpo a la gallega con patatas"
```

---

## 🎯 Casos de Uso Reales

### **1. Restaurante Vasco Tradicional**
- **Euskera → Español**: Para turistas españoles
- **Euskera → Inglés**: Para turistas internacionales
- **Español → Euskera**: Para clientes locales

### **2. App Turística del País Vasco**
- **Detección automática**: Identificar si el usuario habla euskera
- **Traducción contextual**: Menús, direcciones, información turística
- **Glosario especializado**: Términos gastronómicos únicos

### **3. Cadena de Restaurantes Multiregional**
- **Euskera** en Bilbao
- **Catalán** en Barcelona  
- **Gallego** en Santiago
- **Español** como idioma común

---

## 💡 Consejos para Euskera

### **Términos que NO traducir (mantener originales):**
```json
{
  "pairs": [
    {"pintxo": "pintxo"},           // Mejor que "pincho"
    {"txakoli": "txakolí"},         // Nombre del vino específico
    {"sagardoa": "sagardoa"},       // Sidra vasca tradicional
    {"kalimotxo": "kalimotxo"},     // Bebida específica
    {"txistorra": "txistorra"}      // Embutido vasco
  ]
}
```

### **Términos que SÍ traducir:**
```json
{
  "pairs": [
    {"txuleta": "chuletón"},
    {"arraina": "pescado"},
    {"haragia": "carne"},
    {"barazkiak": "verduras"}
  ]
}
```

---

## 🔧 Troubleshooting

### **Error: "API key not valid"**
- Verifica que `GOOGLE_API_KEY` esté correcta
- Asegúrate de que Cloud Translation API esté habilitada
- Revisa que el proyecto tenga facturación activa

### **Error: "Language not supported"**
- Usa `eu` (no `eus` o `euskera`)
- Verifica que `I18N_PROVIDER=google` (no `deepl`)

### **Traducciones de mala calidad:**
- Usa glosarios para términos específicos
- Google Translate para euskera es bueno pero no perfecto
- Considera revisión manual para contenido crítico

---

## 📊 Comparación DeepL vs Google para Euskera

| Aspecto | DeepL | Google Translate |
|---------|-------|------------------|
| **Soporte Euskera** | ❌ No | ✅ Sí |
| **Calidad General** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Calidad Euskera** | N/A | ⭐⭐⭐ |
| **Costo** | Más caro | Más barato |
| **Detección** | Limitada | ✅ Excelente |

**Conclusión:** Para euskera, Google Translate es la única opción viable.
