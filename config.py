"""
ARINC 429 Dashboard Konfigürasyonu
Proje ayarları ve sabitler
"""

import os
from typing import Dict, Any
from utils.data_models import DashboardConfig, ExternalConfig


# API Sunucu Ayarları
API_HOST = "0.0.0.0"
API_PORT = 8000
API_DEBUG = True

# WebSocket Ayarları
WEBSOCKET_PING_INTERVAL = 20
WEBSOCKET_PING_TIMEOUT = 20

# Veri Üretim Ayarları
DATA_UPDATE_INTERVAL = 1  # saniye
MAX_HISTORY_SIZE = 1000

# Havacılık Veri Aralıkları
AVIATION_RANGES = {
    "latitude": {"min": -90.0, "max": 90.0, "unit": "derece"},
    "longitude": {"min": -180.0, "max": 180.0, "unit": "derece"},
    "altitude": {"min": 0.0, "max": 50000.0, "unit": "feet"},
    "airspeed": {"min": 0.0, "max": 1000.0, "unit": "knots"},
    "heading": {"min": 0.0, "max": 360.0, "unit": "derece"},
    "vertical_speed": {"min": -10000.0, "max": 10000.0, "unit": "feet/dakika"}
}

# ARINC 429 Label Tanımları
ARINC429_LABELS = {
    "latitude": "6A",
    "longitude": "6B", 
    "altitude": "6C",
    "airspeed": "6D",
    "heading": "6E",
    "vertical_speed": "6F"
}

# Varsayılan Dashboard Konfigürasyonu
DEFAULT_CONFIG = DashboardConfig(
    update_interval=DATA_UPDATE_INTERVAL,
    max_history=MAX_HISTORY_SIZE,
    external_configs=[
        ExternalConfig(
            url="http://localhost:8080/api/flight-data",
            interval=5,
            enabled=False,
            headers={"Content-Type": "application/json"}
        )
    ]
)

# Logging Ayarları
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Streamlit Dashboard Ayarları
STREAMLIT_CONFIG = {
    "page_title": "ARINC 429 Uçuş Verisi Dashboard",
    "page_icon": "✈️",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Harici Sistem Ayarları
EXTERNAL_SYSTEMS = {
    "test_system": {
        "url": "http://localhost:8080/api/flight-data",
        "interval": 5,
        "enabled": False,
        "headers": {"Content-Type": "application/json", "Authorization": "Bearer test-token"}
    },
    "production_system": {
        "url": "https://api.example.com/flight-data",
        "interval": 10,
        "enabled": False,
        "headers": {"Content-Type": "application/json"}
    }
}

# Veri Kalitesi Ayarları
DATA_QUALITY = {
    "enable_validation": True,
    "enable_smoothing": True,
    "smoothing_factor": 0.8,
    "outlier_threshold": 3.0
}

# Performans Ayarları
PERFORMANCE = {
    "enable_caching": True,
    "cache_ttl": 300,  # 5 dakika
    "max_concurrent_connections": 100,
    "connection_timeout": 30
}

def get_config() -> Dict[str, Any]:
    """Tüm konfigürasyon ayarlarını döndür"""
    return {
        "api": {
            "host": API_HOST,
            "port": API_PORT,
            "debug": API_DEBUG
        },
        "websocket": {
            "ping_interval": WEBSOCKET_PING_INTERVAL,
            "ping_timeout": WEBSOCKET_PING_TIMEOUT
        },
        "data": {
            "update_interval": DATA_UPDATE_INTERVAL,
            "max_history": MAX_HISTORY_SIZE,
            "ranges": AVIATION_RANGES,
            "labels": ARINC429_LABELS
        },
        "logging": {
            "level": LOG_LEVEL,
            "format": LOG_FORMAT
        },
        "streamlit": STREAMLIT_CONFIG,
        "external_systems": EXTERNAL_SYSTEMS,
        "data_quality": DATA_QUALITY,
        "performance": PERFORMANCE
    }


def load_config_from_env():
    """Ortam değişkenlerinden konfigürasyon yükle"""
    global API_HOST, API_PORT, API_DEBUG, DATA_UPDATE_INTERVAL
    
    API_HOST = os.getenv("API_HOST", API_HOST)
    API_PORT = int(os.getenv("API_PORT", API_PORT))
    API_DEBUG = os.getenv("API_DEBUG", "true").lower() == "true"
    DATA_UPDATE_INTERVAL = int(os.getenv("DATA_UPDATE_INTERVAL", DATA_UPDATE_INTERVAL))


# Ortam değişkenlerini yükle
load_config_from_env()
