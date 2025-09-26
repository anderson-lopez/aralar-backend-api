# 🌐 Comparación de Proveedores de Traducción

## DeepL vs Google Translate - ¿Cuál Usar?

### 🔥 DeepL Provider

#### **Ventajas:**
- ✅ **Mejor calidad** para idiomas europeos (ES, EN, FR, DE, IT)
- ✅ **Traducciones más naturales** y contextuales
- ✅ **Menos errores** en textos largos
- ✅ **Mejor para contenido profesional**

#### **Desventajas:**
- ❌ **Idiomas limitados** (solo ~30 idiomas)
- ❌ **Más caro** que Google
- ❌ **No soporta algunos idiomas** (árabe, chino, japonés limitado)

#### **Idiomas Soportados por DeepL:**
```
es, en, fr, de, it, pt, nl, pl, ru, ja, zh, ko
da, sv, no, fi, et, lv, lt, cs, sk, sl, hu, ro, bg, el, tr
```

---

### 🌍 Google Translate Provider

#### **Ventajas:**
- ✅ **Más de 100 idiomas** soportados
- ✅ **Mejor detección de idioma**
- ✅ **Más barato** que DeepL
- ✅ **Mejor para idiomas asiáticos** y menos comunes
- ✅ **API más estable** y rápida

#### **Desventajas:**
- ❌ **Calidad inferior** para idiomas europeos
- ❌ **Traducciones menos naturales**
- ❌ **Más errores contextuales**

#### **Idiomas Adicionales que Google Soporta:**
```
ar, hi, th, vi, he, fa, ur, bn, ta, te, ml, kn, gu, mr, ne, si, my, km, lo, ka, am, sw, zu, xh, af, ig, yo, ha, mg, ny, sn, st, tn, ts, ve, ss, nr, nso, etc.
```

---

## 🛠️ Configuración de Proveedores

### **Variables de Entorno:**

```bash
# Para usar DeepL (por defecto)
I18N_PROVIDER=deepl
DEEPL_API_KEY=tu-deepl-api-key
DEEPL_BASE_URL=https://api.deepl.com/v2  # o https://api-free.deepl.com/v2

# Para usar Google Translate
I18N_PROVIDER=google
GOOGLE_API_KEY=tu-google-api-key
GOOGLE_BASE_URL=https://translation.googleapis.com/language/translate/v2
```

---

## 🎯 Casos de Uso Recomendados

### **Usar DeepL Cuando:**
- 🍽️ **Restaurante europeo** (ES→EN, FR→EN, etc.)
- 📄 **Contenido profesional** (menús, descripciones)
- 🎨 **Calidad es prioritaria** sobre costo
- 📝 **Textos largos** y complejos

### **Usar Google Translate Cuando:**
- 🌏 **Restaurante asiático** (chino, japonés, tailandés)
- 🌍 **Múltiples idiomas** necesarios
- 💰 **Presupuesto limitado**
- 🔍 **Detección automática** de idioma importante
- 🚀 **Velocidad** es prioritaria

---

## 📊 Ejemplo de Comparación

### **Texto Original (Español):**
```
"Paella Valenciana tradicional con mariscos frescos y azafrán auténtico"
```

### **DeepL Result:**
```
"Traditional Valencian Paella with fresh seafood and authentic saffron"
```
**Calidad:** ⭐⭐⭐⭐⭐ (Excelente, muy natural)

### **Google Translate Result:**
```
"Traditional Valencian paella with fresh seafood and authentic saffron"
```
**Calidad:** ⭐⭐⭐⭐ (Muy buena, ligeras diferencias)

---

## 🔄 Cambiar de Proveedor

### **Opción 1: Variable de Entorno**
```bash
# Cambiar en .env
I18N_PROVIDER=google  # o deepl
```

### **Opción 2: Por Request (Futuro)**
```json
{
  "texts": ["Hola mundo"],
  "source_lang": "es",
  "target_lang": "en",
  "tenant_id": "restaurant-123",
  "provider": "google"  // Override temporal
}
```

---

## 🚨 Limitaciones por Proveedor

### **DeepL Limitaciones:**
- ❌ No soporta: árabe, hindi, tailandés, vietnamita
- ❌ Detección de idioma limitada
- ❌ Más caro por carácter

### **Google Translate Limitaciones:**
- ❌ Calidad inferior en ES→EN
- ❌ Menos natural para contenido profesional
- ❌ Puede ser menos preciso en contexto gastronómico

---

## 💡 Recomendación Híbrida

Para **máxima flexibilidad**, puedes usar ambos:

```python
# Configuración inteligente
if target_lang in ['ar', 'hi', 'th', 'vi', 'zh', 'ja', 'ko']:
    # Usar Google para idiomas asiáticos
    provider = "google"
elif source_lang in ['es', 'fr', 'de', 'it'] and target_lang == 'en':
    # Usar DeepL para calidad premium europeo→inglés
    provider = "deepl"  
else:
    # Usar Google como fallback
    provider = "google"
```

**Resultado:** Mejor calidad + máxima cobertura de idiomas
