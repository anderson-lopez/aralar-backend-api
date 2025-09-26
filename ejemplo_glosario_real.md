# 🍽️ Ejemplo Real: Restaurante Casa Pepe

## Problema: Traducir Menú sin Glosario

### Textos Originales:
```
"Jamón Ibérico Casa Pepe"
"Paella Casa Pepe Especial"  
"Tortilla Casa Pepe Premium"
```

### Traducción DeepL (Sin Glosario):
```
"Iberian Ham Casa Pepe"          ❌ (genérico)
"Casa Pepe Special Paella"       ❌ (inconsistente)
"Casa Pepe Premium Tortilla"     ❌ (no suena bien)
```

**Problemas:**
- "Jamón Ibérico" → "Iberian Ham" (suena barato)
- Orden de palabras inconsistente
- No refleja la marca premium

---

## Solución: Crear Glosario Local

### Paso 1: Crear Glosario
```bash
POST /i18n/glossaries
Content-Type: application/json

{
  "tenant_id": "casa-pepe-restaurant",
  "source_lang": "es", 
  "target_lang": "en",
  "pairs": [
    {"Casa Pepe": "Casa Pepe"},
    {"Jamón Ibérico": "Premium Iberico Ham"},
    {"Especial": "Signature"},
    {"Premium": "Premium"},
    {"Paella": "Traditional Paella"},
    {"Tortilla": "Spanish Omelet"}
  ]
}
```

### Paso 2: Traducir con Glosario
```bash
POST /i18n/translate
Content-Type: application/json

{
  "texts": [
    "Jamón Ibérico Casa Pepe",
    "Paella Casa Pepe Especial", 
    "Tortilla Casa Pepe Premium"
  ],
  "source_lang": "es",
  "target_lang": "en", 
  "tenant_id": "casa-pepe-restaurant",
  "use_glossary": true
}
```

### Resultado Final:
```json
{
  "provider": "deepl",
  "source_lang": "es",
  "target_lang": "en",
  "items": [
    {
      "source": "Jamón Ibérico Casa Pepe",
      "translated": "Premium Iberico Ham Casa Pepe",
      "cached": false
    },
    {
      "source": "Paella Casa Pepe Especial", 
      "translated": "Traditional Paella Casa Pepe Signature",
      "cached": false
    },
    {
      "source": "Tortilla Casa Pepe Premium",
      "translated": "Spanish Omelet Casa Pepe Premium", 
      "cached": false
    }
  ]
}
```

---

## ✅ Beneficios del Glosario

### Antes (Sin Glosario):
- ❌ "Iberian Ham" (suena genérico)
- ❌ Inconsistencias en orden de palabras
- ❌ No refleja branding premium
- ❌ Cliente tiene que corregir manualmente

### Después (Con Glosario):
- ✅ "Premium Iberico Ham" (suena premium)
- ✅ Términos consistentes siempre
- ✅ Branding preservado ("Casa Pepe")
- ✅ Traducciones listas para usar

---

## 🔄 Flujo Técnico Interno

### Lo que pasa internamente:

1. **Texto Original:** "Jamón Ibérico Casa Pepe"

2. **Aplicar Glosario Local:** 
   ```
   "Jamón Ibérico Casa Pepe" 
   → "Premium Iberico Ham Casa Pepe"
   ```

3. **Enviar a DeepL:**
   ```
   DeepL recibe: "Premium Iberico Ham Casa Pepe"
   DeepL devuelve: "Premium Iberico Ham Casa Pepe" 
   ```

4. **Verificar Términos:**
   ```
   ✅ "Premium Iberico Ham" está presente
   ✅ "Casa Pepe" está presente
   ```

5. **Resultado Final:** "Premium Iberico Ham Casa Pepe"

---

## 💰 ¿Ahorra Dinero?

### Escenario Real:

**Sin Glosario:**
```
Traducción 1: "Jamón Ibérico" → "Iberian Ham" ($0.002)
Cliente: "No me gusta, cambia a Premium Iberico Ham"
Traducción 2: Manual correction (30 min trabajo = $15)
Traducción 3: "Jamón Ibérico" otra vez → "Iberian Ham" ($0.002)
Cliente: "Otra vez mal!"
Más correcciones manuales...

Total: $0.004 + $30 trabajo manual = $30.004
```

**Con Glosario:**
```
Setup glosario: 5 minutos = $2.50
Traducción 1: "Jamón Ibérico" → "Premium Iberico Ham" ($0.002)
Cliente: "Perfecto!"
Traducción 2: "Jamón Ibérico" → "Premium Iberico Ham" ($0.002)
Cliente: "Consistente, perfecto!"

Total: $2.50 + $0.004 = $2.504
```

**Ahorro: $27.50 por cada término problemático**

---

## 🎯 Casos de Uso Reales

### 1. Restaurante de Sushi
```json
{
  "pairs": [
    {"Sashimi": "Fresh Sashimi"},
    {"Omakase": "Chef's Choice Omakase"},
    {"Nigiri": "Hand-Pressed Nigiri"}
  ]
}
```

### 2. Pizzería Italiana  
```json
{
  "pairs": [
    {"Margherita": "Classic Margherita"},
    {"Quattro Stagioni": "Four Seasons Pizza"},
    {"Prosciutto": "Italian Prosciutto"}
  ]
}
```

### 3. Cadena de Restaurantes
```json
{
  "pairs": [
    {"McBurger": "McBurger"},
    {"Combo Especial": "Special Combo"},
    {"Salsa Secreta": "Secret Sauce"}
  ]
}
```

El glosario NO ahorra peticiones, pero ahorra tiempo, dinero en correcciones manuales y garantiza consistencia de marca.
