"""
ARINC 429 Kodlama ve Çözme Modülü
Havacılık verilerini ARINC 429 formatında kodlar ve çözer
"""

import struct
import math
from typing import Dict, List, Tuple
from utils.data_models import ARINC429Message, FlightData


class ARINC429Encoder:
    """ARINC 429 veri kodlayıcı"""
    
    # ARINC 429 Label tanımları
    LABELS = {
        "latitude": "6A",      # 0x6A - Enlem
        "longitude": "6B",     # 0x6B - Boylam
        "altitude": "6C",      # 0x6C - İrtifa
        "airspeed": "6D",      # 0x6D - Hava hızı
        "heading": "6E",       # 0x6E - Yön
        "vertical_speed": "6F" # 0x6F - Dikey hız
    }
    
    def __init__(self):
        self.sdi = "00"  # Source/Destination Identifier
        self.ssm = "00"  # Sign/Status Matrix
    
    def encode_latitude(self, latitude: float) -> str:
        """Enlem değerini ARINC 429 formatında kodla"""
        # Enlem: -90 ile +90 arası, 0.0001 derece hassasiyet
        if latitude < -90 or latitude > 90:
            raise ValueError("Enlem -90 ile +90 arasında olmalıdır")
        
        # Pozitif değer için SSM = 00, negatif için SSM = 11
        if latitude >= 0:
            self.ssm = "00"
            data_value = int(abs(latitude) * 10000)  # 0.0001 hassasiyet
        else:
            self.ssm = "11"
            data_value = int(abs(latitude) * 10000)
        
        # 19-bit data field
        data_binary = format(data_value & 0x7FFFF, '019b')
        return data_binary
    
    def encode_longitude(self, longitude: float) -> str:
        """Boylam değerini ARINC 429 formatında kodla"""
        # Boylam: -180 ile +180 arası, 0.0001 derece hassasiyet
        if longitude < -180 or longitude > 180:
            raise ValueError("Boylam -180 ile +180 arasında olmalıdır")
        
        if longitude >= 0:
            self.ssm = "00"
            data_value = int(abs(longitude) * 10000)
        else:
            self.ssm = "11"
            data_value = int(abs(longitude) * 10000)
        
        data_binary = format(data_value & 0x7FFFF, '019b')
        return data_binary
    
    def encode_altitude(self, altitude: float) -> str:
        """İrtifa değerini ARINC 429 formatında kodla"""
        # İrtifa: 0-50000 feet, 1 foot hassasiyet
        if altitude < 0 or altitude > 50000:
            raise ValueError("İrtifa 0-50000 feet arasında olmalıdır")
        
        self.ssm = "00"  # Pozitif değer
        data_value = int(altitude)
        data_binary = format(data_value & 0x7FFFF, '019b')
        return data_binary
    
    def encode_airspeed(self, airspeed: float) -> str:
        """Hava hızını ARINC 429 formatında kodla"""
        # Hava hızı: 0-1000 knots, 0.1 knot hassasiyet
        if airspeed < 0 or airspeed > 1000:
            raise ValueError("Hava hızı 0-1000 knots arasında olmalıdır")
        
        self.ssm = "00"
        data_value = int(airspeed * 10)  # 0.1 knot hassasiyet
        data_binary = format(data_value & 0x7FFFF, '019b')
        return data_binary
    
    def encode_heading(self, heading: float) -> str:
        """Yön değerini ARINC 429 formatında kodla"""
        # Yön: 0-360 derece, 0.1 derece hassasiyet
        if heading < 0 or heading > 360:
            raise ValueError("Yön 0-360 derece arasında olmalıdır")
        
        self.ssm = "00"
        data_value = int(heading * 10)  # 0.1 derece hassasiyet
        data_binary = format(data_value & 0x7FFFF, '019b')
        return data_binary
    
    def encode_vertical_speed(self, vertical_speed: float) -> str:
        """Dikey hızı ARINC 429 formatında kodla"""
        # Dikey hız: -10000 ile +10000 feet/dakika, 1 foot/dakika hassasiyet
        if vertical_speed < -10000 or vertical_speed > 10000:
            raise ValueError("Dikey hız -10000 ile +10000 feet/dakika arasında olmalıdır")
        
        if vertical_speed >= 0:
            self.ssm = "00"
            data_value = int(abs(vertical_speed))
        else:
            self.ssm = "11"
            data_value = int(abs(vertical_speed))
        
        data_binary = format(data_value & 0x7FFFF, '019b')
        return data_binary
    
    def calculate_parity(self, label: str, sdi: str, data: str, ssm: str) -> str:
        """Parity bit hesapla (odd parity)"""
        # 32-bit ARINC 429 word: [8-bit label][2-bit SDI][19-bit data][2-bit SSM][1-bit parity]
        word = int(label, 16) << 24 | int(sdi, 2) << 22 | int(data, 2) << 3 | int(ssm, 2) << 1
        
        # Parity hesapla (odd parity)
        bit_count = bin(word).count('1')
        parity = '1' if bit_count % 2 == 0 else '0'
        return parity
    
    def encode_flight_data(self, flight_data: FlightData) -> List[ARINC429Message]:
        """Uçuş verilerini ARINC 429 mesajlarına kodla"""
        messages = []
        
        # Her veri tipi için ARINC 429 mesajı oluştur
        encodings = [
            ("latitude", flight_data.latitude, self.encode_latitude),
            ("longitude", flight_data.longitude, self.encode_longitude),
            ("altitude", flight_data.altitude, self.encode_altitude),
            ("airspeed", flight_data.airspeed, self.encode_airspeed),
            ("heading", flight_data.heading, self.encode_heading),
            ("vertical_speed", flight_data.vertical_speed, self.encode_vertical_speed)
        ]
        
        for data_type, value, encoder_func in encodings:
            try:
                data_binary = encoder_func(value)
                label = self.LABELS[data_type]
                
                # Parity hesapla
                parity = self.calculate_parity(label, self.sdi, data_binary, self.ssm)
                
                # ARINC 429 mesajı oluştur
                message = ARINC429Message(
                    label=label,
                    sdi=self.sdi,
                    data=data_binary,
                    ssm=self.ssm,
                    parity=parity,
                    timestamp=flight_data.timestamp
                )
                messages.append(message)
                
            except Exception as e:
                print(f"Hata: {data_type} kodlanırken hata oluştu: {e}")
        
        return messages


class ARINC429Decoder:
    """ARINC 429 veri çözücü"""
    
    def decode_latitude(self, data: str, ssm: str) -> float:
        """ARINC 429 enlem verisini çöz"""
        data_value = int(data, 2)
        latitude = data_value / 10000.0  # 0.0001 hassasiyet
        
        if ssm == "11":  # Negatif değer
            latitude = -latitude
        
        return latitude
    
    def decode_longitude(self, data: str, ssm: str) -> float:
        """ARINC 429 boylam verisini çöz"""
        data_value = int(data, 2)
        longitude = data_value / 10000.0
        
        if ssm == "11":  # Negatif değer
            longitude = -longitude
        
        return longitude
    
    def decode_altitude(self, data: str, ssm: str) -> float:
        """ARINC 429 irtifa verisini çöz"""
        data_value = int(data, 2)
        return float(data_value)  # 1 foot hassasiyet
    
    def decode_airspeed(self, data: str, ssm: str) -> float:
        """ARINC 429 hava hızı verisini çöz"""
        data_value = int(data, 2)
        return data_value / 10.0  # 0.1 knot hassasiyet
    
    def decode_heading(self, data: str, ssm: str) -> float:
        """ARINC 429 yön verisini çöz"""
        data_value = int(data, 2)
        return data_value / 10.0  # 0.1 derece hassasiyet
    
    def decode_vertical_speed(self, data: str, ssm: str) -> float:
        """ARINC 429 dikey hız verisini çöz"""
        data_value = int(data, 2)
        vertical_speed = float(data_value)
        
        if ssm == "11":  # Negatif değer
            vertical_speed = -vertical_speed
        
        return vertical_speed
    
    def decode_message(self, message: ARINC429Message) -> Tuple[str, float]:
        """ARINC 429 mesajını çöz"""
        label = message.label
        data = message.data
        ssm = message.ssm
        
        decoders = {
            "6A": ("latitude", self.decode_latitude),
            "6B": ("longitude", self.decode_longitude),
            "6C": ("altitude", self.decode_altitude),
            "6D": ("airspeed", self.decode_airspeed),
            "6E": ("heading", self.decode_heading),
            "6F": ("vertical_speed", self.decode_vertical_speed)
        }
        
        if label in decoders:
            data_type, decoder_func = decoders[label]
            value = decoder_func(data, ssm)
            return data_type, value
        else:
            raise ValueError(f"Bilinmeyen label: {label}")


def create_arinc429_word(label: str, sdi: str, data: str, ssm: str, parity: str) -> str:
    """32-bit ARINC 429 word oluştur"""
    # Format: [8-bit label][2-bit SDI][19-bit data][2-bit SSM][1-bit parity]
    word = f"{label:08b}{sdi}{data}{ssm}{parity}"
    return word


def validate_arinc429_word(word: str) -> bool:
    """ARINC 429 word'ünün geçerliliğini kontrol et"""
    if len(word) != 32:
        return False
    
    # Parity kontrolü
    bit_count = word.count('1')
    return bit_count % 2 == 1  # Odd parity
