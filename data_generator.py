"""
ARINC 429 Uçuş Verisi Üretici
Gerçek zamanlı havacılık verileri üretir ve ARINC 429 formatında kodlar
"""

import random
import time
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from utils.data_models import FlightData, ARINC429Data
from utils.arinc429 import ARINC429Encoder
from config import AVIATION_RANGES, DATA_UPDATE_INTERVAL


class FlightDataGenerator:
    """Gerçek zamanlı uçuş verisi üretici"""
    
    def __init__(self, update_interval: float = 1.0):
        self.update_interval = update_interval
        self.encoder = ARINC429Encoder()
        self.current_data: Optional[FlightData] = None
        self.history: List[FlightData] = []
        self.max_history = 1000
        
        # Başlangıç pozisyonu (İstanbul Havalimanı yakınları)
        self.current_latitude = 41.2622
        self.current_longitude = 28.7278
        self.current_altitude = 35000.0  # feet
        self.current_airspeed = 450.0    # knots
        self.current_heading = 270.0     # derece (batıya doğru)
        self.current_vertical_speed = 0.0 # feet/dakika
        
        # Hareket parametreleri
        self.heading_change_rate = 0.0   # derece/saniye
        self.altitude_change_rate = 0.0  # feet/dakika
        self.speed_change_rate = 0.0     # knots/saniye
        
        # Logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # İlk veriyi oluştur
        self._generate_initial_data()
    
    def _generate_initial_data(self):
        """İlk uçuş verisini oluştur"""
        self.current_data = FlightData(
            latitude=self.current_latitude,
            longitude=self.current_longitude,
            altitude=self.current_altitude,
            airspeed=self.current_airspeed,
            heading=self.current_heading,
            vertical_speed=self.current_vertical_speed,
            timestamp=datetime.now()
        )
        self.history.append(self.current_data)
        self.logger.info("İlk uçuş verisi oluşturuldu")
    
    def _update_position(self):
        """Uçak pozisyonunu güncelle"""
        # Hava hızını knots'tan m/s'ye çevir
        speed_ms = self.current_airspeed * 0.514444
        
        # Zaman aralığını hesapla
        dt = self.update_interval
        
        # Yön değişikliği (derece)
        heading_rad = math.radians(self.current_heading)
        
        # Mesafe hesapla (metre)
        distance = speed_ms * dt
        
        # Enlem değişikliği (derece)
        lat_change = (distance * math.cos(heading_rad)) / 111320.0  # 1 derece ≈ 111.32 km
        self.current_latitude += lat_change
        
        # Boylam değişikliği (derece)
        lon_change = (distance * math.sin(heading_rad)) / (111320.0 * math.cos(math.radians(self.current_latitude)))
        self.current_longitude += lon_change
        
        # Yön güncelle
        self.current_heading += self.heading_change_rate * dt
        if self.current_heading >= 360:
            self.current_heading -= 360
        elif self.current_heading < 0:
            self.current_heading += 360
        
        # İrtifa güncelle
        self.current_altitude += (self.current_vertical_speed / 60.0) * dt  # feet/dakika -> feet/saniye
        
        # Hava hızı güncelle
        self.current_airspeed += self.speed_change_rate * dt
        
        # Sınırları kontrol et
        self._apply_boundaries()
    
    def _apply_boundaries(self):
        """Veri sınırlarını uygula"""
        ranges = AVIATION_RANGES
        
        self.current_latitude = max(ranges["latitude"]["min"], 
                                   min(ranges["latitude"]["max"], self.current_latitude))
        self.current_longitude = max(ranges["longitude"]["min"], 
                                    min(ranges["longitude"]["max"], self.current_longitude))
        self.current_altitude = max(ranges["altitude"]["min"], 
                                   min(ranges["altitude"]["max"], self.current_altitude))
        self.current_airspeed = max(ranges["airspeed"]["min"], 
                                   min(ranges["airspeed"]["max"], self.current_airspeed))
        self.current_heading = max(ranges["heading"]["min"], 
                                  min(ranges["heading"]["max"], self.current_heading))
        self.current_vertical_speed = max(ranges["vertical_speed"]["min"], 
                                         min(ranges["vertical_speed"]["max"], self.current_vertical_speed))
    
    def _add_realistic_variations(self):
        """Gerçekçi rastgele değişiklikler ekle"""
        # Küçük rastgele değişiklikler
        self.current_latitude += random.uniform(-0.001, 0.001)
        self.current_longitude += random.uniform(-0.001, 0.001)
        self.current_altitude += random.uniform(-10, 10)
        self.current_airspeed += random.uniform(-2, 2)
        self.current_heading += random.uniform(-0.5, 0.5)
        self.current_vertical_speed += random.uniform(-50, 50)
        
        # Hareket parametrelerini güncelle
        self.heading_change_rate = random.uniform(-1, 1)  # derece/saniye
        self.altitude_change_rate = random.uniform(-500, 500)  # feet/dakika
        self.speed_change_rate = random.uniform(-5, 5)  # knots/saniye
        
        # Dikey hızı güncelle
        self.current_vertical_speed = self.altitude_change_rate
    
    def generate_flight_data(self) -> FlightData:
        """Yeni uçuş verisi üret"""
        # Pozisyonu güncelle
        self._update_position()
        
        # Gerçekçi değişiklikler ekle
        self._add_realistic_variations()
        
        # Sınırları uygula
        self._apply_boundaries()
        
        # Yeni veriyi oluştur
        new_data = FlightData(
            latitude=round(self.current_latitude, 6),
            longitude=round(self.current_longitude, 6),
            altitude=round(self.current_altitude, 1),
            airspeed=round(self.current_airspeed, 1),
            heading=round(self.current_heading, 1),
            vertical_speed=round(self.current_vertical_speed, 1),
            timestamp=datetime.now()
        )
        
        # Geçmişe ekle
        self.history.append(new_data)
        self.current_data = new_data
        
        # Geçmiş boyutunu kontrol et
        if len(self.history) > self.max_history:
            self.history.pop(0)
        
        return new_data
    
    def generate_arinc429_data(self) -> ARINC429Data:
        """ARINC 429 formatında veri üret"""
        flight_data = self.generate_flight_data()
        
        # ARINC 429 mesajlarını kodla
        arinc_messages = self.encoder.encode_flight_data(flight_data)
        
        # Ham veri sözlüğü oluştur
        raw_data = {}
        for msg in arinc_messages:
            raw_data[f"label_{msg.label}"] = {
                "label": msg.label,
                "sdi": msg.sdi,
                "data": msg.data,
                "ssm": msg.ssm,
                "parity": msg.parity,
                "timestamp": msg.timestamp.isoformat()
            }
        
        return ARINC429Data(
            flight_data=flight_data,
            arinc_messages=arinc_messages,
            raw_data=raw_data
        )
    
    def get_current_data(self) -> Optional[FlightData]:
        """Mevcut veriyi döndür"""
        return self.current_data
    
    def get_history(self, limit: Optional[int] = None) -> List[FlightData]:
        """Geçmiş verileri döndür"""
        if limit is None:
            return self.history.copy()
        return self.history[-limit:].copy()
    
    def reset_position(self, latitude: float = 41.2622, longitude: float = 28.7278):
        """Uçak pozisyonunu sıfırla"""
        self.current_latitude = latitude
        self.current_longitude = longitude
        self.current_altitude = 35000.0
        self.current_airspeed = 450.0
        self.current_heading = 270.0
        self.current_vertical_speed = 0.0
        self.logger.info(f"Pozisyon sıfırlandı: {latitude}, {longitude}")
    
    def set_flight_parameters(self, heading_change: float = 0.0, 
                            altitude_change: float = 0.0, 
                            speed_change: float = 0.0):
        """Uçuş parametrelerini ayarla"""
        self.heading_change_rate = heading_change
        self.altitude_change_rate = altitude_change
        self.speed_change_rate = speed_change
        self.logger.info(f"Uçuş parametreleri güncellendi: heading={heading_change}, altitude={altitude_change}, speed={speed_change}")


class SimulatedFlightDataGenerator(FlightDataGenerator):
    """Simüle edilmiş uçuş verisi üretici (daha karmaşık senaryolar için)"""
    
    def __init__(self, update_interval: float = 1.0):
        super().__init__(update_interval)
        self.flight_phase = "cruise"  # takeoff, climb, cruise, descent, landing
        self.waypoints = []
        self.current_waypoint_index = 0
        
    def add_waypoint(self, latitude: float, longitude: float, altitude: float):
        """Rota noktası ekle"""
        self.waypoints.append({
            "latitude": latitude,
            "longitude": longitude,
            "altitude": altitude
        })
    
    def _navigate_to_waypoint(self):
        """Bir sonraki rota noktasına yönel"""
        if not self.waypoints or self.current_waypoint_index >= len(self.waypoints):
            return
        
        waypoint = self.waypoints[self.current_waypoint_index]
        
        # Hedef yönü hesapla
        target_heading = self._calculate_bearing(
            self.current_latitude, self.current_longitude,
            waypoint["latitude"], waypoint["longitude"]
        )
        
        # Yön farkını hesapla
        heading_diff = target_heading - self.current_heading
        if heading_diff > 180:
            heading_diff -= 360
        elif heading_diff < -180:
            heading_diff += 360
        
        # Yön değişikliği uygula
        max_turn_rate = 3.0  # derece/saniye
        if abs(heading_diff) > 1:
            self.heading_change_rate = max(-max_turn_rate, min(max_turn_rate, heading_diff))
        else:
            self.heading_change_rate = 0
        
        # Mesafe kontrolü
        distance = self._calculate_distance(
            self.current_latitude, self.current_longitude,
            waypoint["latitude"], waypoint["longitude"]
        )
        
        if distance < 0.01:  # 1 km'den yakın
            self.current_waypoint_index += 1
            self.logger.info(f"Rota noktasına ulaşıldı: {waypoint}")
    
    def _calculate_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """İki nokta arasındaki yönü hesapla"""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        lon_diff_rad = math.radians(lon2 - lon1)
        
        y = math.sin(lon_diff_rad) * math.cos(lat2_rad)
        x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(lon_diff_rad)
        
        bearing = math.degrees(math.atan2(y, x))
        return (bearing + 360) % 360
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """İki nokta arasındaki mesafeyi hesapla (km)"""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        lon_diff_rad = math.radians(lon2 - lon1)
        
        a = (math.sin((lat2_rad - lat1_rad) / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(lon_diff_rad / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return 6371 * c  # Dünya yarıçapı (km)


if __name__ == "__main__":
    # Test kodu
    generator = FlightDataGenerator()
    
    print("ARINC 429 Uçuş Verisi Üretici Test")
    print("=" * 40)
    
    for i in range(5):
        data = generator.generate_arinc429_data()
        print(f"\nVeri #{i+1}:")
        print(f"Enlem: {data.flight_data.latitude:.6f}°")
        print(f"Boylam: {data.flight_data.longitude:.6f}°")
        print(f"İrtifa: {data.flight_data.altitude:.1f} feet")
        print(f"Hava Hızı: {data.flight_data.airspeed:.1f} knots")
        print(f"Yön: {data.flight_data.heading:.1f}°")
        print(f"Dikey Hız: {data.flight_data.vertical_speed:.1f} feet/dakika")
        print(f"ARINC Mesaj Sayısı: {len(data.arinc_messages)}")
        
        time.sleep(1)
