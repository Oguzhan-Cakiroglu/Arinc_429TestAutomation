"""
ARINC 429 Veri Modelleri
Havacılık verilerini temsil eden Pydantic modelleri
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
import json


class ARINC429Message(BaseModel):
    """ARINC 429 mesaj modeli"""
    label: str = Field(..., description="ARINC 429 label (hex)")
    sdi: str = Field(..., description="Source/Destination Identifier")
    data: str = Field(..., description="Data field (binary)")
    ssm: str = Field(..., description="Sign/Status Matrix")
    parity: str = Field(..., description="Parity bit")
    timestamp: datetime = Field(default_factory=datetime.now)


class FlightData(BaseModel):
    """Uçuş verisi modeli"""
    latitude: float = Field(..., ge=-90, le=90, description="Enlem (derece)")
    longitude: float = Field(..., ge=-180, le=180, description="Boylam (derece)")
    altitude: float = Field(..., ge=0, le=50000, description="İrtifa (feet)")
    airspeed: float = Field(..., ge=0, le=1000, description="Hava hızı (knots)")
    heading: float = Field(..., ge=0, le=360, description="Yön (derece)")
    vertical_speed: float = Field(..., ge=-10000, le=10000, description="Dikey hız (feet/dakika)")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ARINC429Data(BaseModel):
    """ARINC 429 veri paketi"""
    flight_data: FlightData
    arinc_messages: List[ARINC429Message]
    raw_data: Dict[str, Dict] = Field(..., description="Ham ARINC 429 verileri")


class ExternalConfig(BaseModel):
    """Harici sistem konfigürasyonu"""
    url: str = Field(..., description="Hedef URL")
    interval: int = Field(..., ge=1, le=3600, description="Gönderim aralığı (saniye)")
    enabled: bool = Field(default=True, description="Aktif/Pasif")
    headers: Dict[str, str] = Field(default_factory=dict, description="HTTP başlıkları")


class DashboardConfig(BaseModel):
    """Dashboard konfigürasyonu"""
    update_interval: int = Field(default=1, ge=1, le=60, description="Güncelleme aralığı (saniye)")
    max_history: int = Field(default=1000, ge=100, le=10000, description="Maksimum geçmiş veri sayısı")
    external_configs: List[ExternalConfig] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


def flight_data_to_dict(flight_data: FlightData) -> Dict:
    """FlightData'yı dictionary'e çevir"""
    return {
        "latitude": flight_data.latitude,
        "longitude": flight_data.longitude,
        "altitude": flight_data.altitude,
        "airspeed": flight_data.airspeed,
        "heading": flight_data.heading,
        "vertical_speed": flight_data.vertical_speed,
        "timestamp": flight_data.timestamp.isoformat()
    }


def dict_to_flight_data(data: Dict) -> FlightData:
    """Dictionary'i FlightData'ya çevir"""
    return FlightData(
        latitude=data["latitude"],
        longitude=data["longitude"],
        altitude=data["altitude"],
        airspeed=data["airspeed"],
        heading=data["heading"],
        vertical_speed=data["vertical_speed"],
        timestamp=datetime.fromisoformat(data["timestamp"])
    )
