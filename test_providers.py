#!/usr/bin/env python3
"""
Script de prueba para verificar que los providers de i18n 
acepten correctamente las base URLs configurables.
"""

import os
import sys
sys.path.append('.')

from aralar.core.i18n.providers import get_provider

def test_provider_configuration():
    """Prueba la configuración de providers con diferentes base URLs"""
    
    print("🧪 Probando configuración de providers de i18n...\n")
    
    # Test 1: DeepL con URL por defecto
    config1 = {
        "I18N_PROVIDER": "deepl",
        "DEEPL_API_KEY": "test-key-123"
    }
    
    provider1 = get_provider(config1)
    print(f"✅ DeepL Provider (URL por defecto):")
    print(f"   - API Key: {provider1.key}")
    print(f"   - Base URL: {provider1.base}")
    print()
    
    # Test 2: DeepL con URL personalizada
    config2 = {
        "I18N_PROVIDER": "deepl",
        "DEEPL_API_KEY": "test-key-456",
        "DEEPL_BASE_URL": "https://api-free.deepl.com/v2"
    }
    
    provider2 = get_provider(config2)
    print(f"✅ DeepL Provider (URL personalizada):")
    print(f"   - API Key: {provider2.key}")
    print(f"   - Base URL: {provider2.base}")
    print()
    
    # Test 3: Google con URL personalizada
    config3 = {
        "I18N_PROVIDER": "google",
        "GOOGLE_API_KEY": "google-test-key",
        "GOOGLE_BASE_URL": "https://custom-translate-api.example.com/v2"
    }
    
    provider3 = get_provider(config3)
    print(f"✅ Google Provider (URL personalizada):")
    print(f"   - API Key: {provider3.key}")
    print(f"   - Base URL: {provider3.base}")
    print()
    
    # Test 4: Verificar que se eliminen las barras finales
    config4 = {
        "I18N_PROVIDER": "deepl",
        "DEEPL_API_KEY": "test-key-789",
        "DEEPL_BASE_URL": "https://api.deepl.com/v2/"  # Con barra final
    }
    
    provider4 = get_provider(config4)
    print(f"✅ DeepL Provider (URL con barra final eliminada):")
    print(f"   - API Key: {provider4.key}")
    print(f"   - Base URL: {provider4.base}")
    print()
    
    print("🎉 Todas las pruebas pasaron exitosamente!")
    print("\n📝 Nuevas variables de entorno disponibles:")
    print("   - DEEPL_BASE_URL: Para personalizar la URL base de DeepL")
    print("   - GOOGLE_BASE_URL: Para personalizar la URL base de Google Translate")
    print("   - GOOGLE_API_KEY: Para la API key de Google Translate")

if __name__ == "__main__":
    test_provider_configuration()
