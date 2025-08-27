"""
ARINC 429 API Sunucusu
FastAPI tabanlı WebSocket ve REST API sunucusu
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import threading
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from data_generator import FlightDataGenerator
from utils.data_models import FlightData, ARINC429Data, ExternalConfig
from utils.arinc429 import ARINC429Encoder
from config import API_HOST, API_PORT, API_DEBUG, WEBSOCKET_PING_INTERVAL, WEBSOCKET_PING_TIMEOUT


class ARINC429APIServer:
    """ARINC 429 API Sunucusu"""
    
    def __init__(self):
        self.app = FastAPI(
            title="ARINC 429 Uçuş Verisi API",
            description="Gerçek zamanlı ARINC 429 uçuş verisi API'si",
            version="1.0.0"
        )
        
        # CORS ayarları
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Veri üretici
        self.data_generator = FlightDataGenerator()
        self.encoder = ARINC429Encoder()
        
        # WebSocket bağlantıları
        self.active_connections: List[WebSocket] = []
        
        # Harici sistem konfigürasyonları
        self.external_configs: List[ExternalConfig] = []
        
        # Logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # API endpoint'lerini tanımla
        self._setup_routes()
        
        # Veri üretim thread'i
        self.data_thread = None
        self.running = False
    
    def _setup_routes(self):
        """API route'larını tanımla"""
        
        @self.app.get("/")
        async def root():
            """Ana sayfa"""
            return {
                "message": "ARINC 429 Uçuş Verisi API",
                "version": "1.0.0",
                "endpoints": {
                    "current_data": "/api/current-data",
                    "historical_data": "/api/historical-data",
                    "websocket": "/ws",
                    "external_config": "/api/external-config"
                }
            }
        
        @self.app.get("/api/current-data")
        async def get_current_data():
            """Mevcut uçuş verisini döndür"""
            try:
                current_data = self.data_generator.get_current_data()
                if current_data:
                    return {
                        "status": "success",
                        "data": {
                            "latitude": current_data.latitude,
                            "longitude": current_data.longitude,
                            "altitude": current_data.altitude,
                            "airspeed": current_data.airspeed,
                            "heading": current_data.heading,
                            "vertical_speed": current_data.vertical_speed,
                            "timestamp": current_data.timestamp.isoformat()
                        }
                    }
                else:
                    raise HTTPException(status_code=404, detail="Veri bulunamadı")
            except Exception as e:
                self.logger.error(f"Veri alınırken hata: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/historical-data")
        async def get_historical_data(limit: Optional[int] = 100):
            """Geçmiş uçuş verilerini döndür"""
            try:
                history = self.data_generator.get_history(limit)
                return {
                    "status": "success",
                    "count": len(history),
                    "data": [
                        {
                            "latitude": data.latitude,
                            "longitude": data.longitude,
                            "altitude": data.altitude,
                            "airspeed": data.airspeed,
                            "heading": data.heading,
                            "vertical_speed": data.vertical_speed,
                            "timestamp": data.timestamp.isoformat()
                        }
                        for data in history
                    ]
                }
            except Exception as e:
                self.logger.error(f"Geçmiş veri alınırken hata: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/arinc429-data")
        async def get_arinc429_data():
            """ARINC 429 formatında veri döndür"""
            try:
                arinc_data = self.data_generator.generate_arinc429_data()
                return {
                    "status": "success",
                    "flight_data": {
                        "latitude": arinc_data.flight_data.latitude,
                        "longitude": arinc_data.flight_data.longitude,
                        "altitude": arinc_data.flight_data.altitude,
                        "airspeed": arinc_data.flight_data.airspeed,
                        "heading": arinc_data.flight_data.heading,
                        "vertical_speed": arinc_data.flight_data.vertical_speed,
                        "timestamp": arinc_data.flight_data.timestamp.isoformat()
                    },
                    "arinc_messages": [
                        {
                            "label": msg.label,
                            "sdi": msg.sdi,
                            "data": msg.data,
                            "ssm": msg.ssm,
                            "parity": msg.parity,
                            "timestamp": msg.timestamp.isoformat()
                        }
                        for msg in arinc_data.arinc_messages
                    ],
                    "raw_data": arinc_data.raw_data
                }
            except Exception as e:
                self.logger.error(f"ARINC 429 veri alınırken hata: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/reset-position")
        async def reset_position(latitude: float = 41.2622, longitude: float = 28.7278):
            """Uçak pozisyonunu sıfırla"""
            try:
                self.data_generator.reset_position(latitude, longitude)
                return {"status": "success", "message": f"Pozisyon sıfırlandı: {latitude}, {longitude}"}
            except Exception as e:
                self.logger.error(f"Pozisyon sıfırlanırken hata: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/set-flight-parameters")
        async def set_flight_parameters(
            heading_change: float = 0.0,
            altitude_change: float = 0.0,
            speed_change: float = 0.0
        ):
            """Uçuş parametrelerini ayarla"""
            try:
                self.data_generator.set_flight_parameters(heading_change, altitude_change, speed_change)
                return {
                    "status": "success",
                    "parameters": {
                        "heading_change": heading_change,
                        "altitude_change": altitude_change,
                        "speed_change": speed_change
                    }
                }
            except Exception as e:
                self.logger.error(f"Uçuş parametreleri ayarlanırken hata: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/external-config")
        async def get_external_configs():
            """Harici sistem konfigürasyonlarını döndür"""
            return {
                "status": "success",
                "configs": [
                    {
                        "url": config.url,
                        "interval": config.interval,
                        "enabled": config.enabled,
                        "headers": config.headers
                    }
                    for config in self.external_configs
                ]
            }
        
        @self.app.post("/api/external-config")
        async def add_external_config(config: ExternalConfig):
            """Harici sistem konfigürasyonu ekle"""
            try:
                self.external_configs.append(config)
                self.logger.info(f"Harici sistem konfigürasyonu eklendi: {config.url}")
                return {"status": "success", "message": "Konfigürasyon eklendi"}
            except Exception as e:
                self.logger.error(f"Konfigürasyon eklenirken hata: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/api/external-config/{index}")
        async def remove_external_config(index: int):
            """Harici sistem konfigürasyonu kaldır"""
            try:
                if 0 <= index < len(self.external_configs):
                    removed_config = self.external_configs.pop(index)
                    self.logger.info(f"Harici sistem konfigürasyonu kaldırıldı: {removed_config.url}")
                    return {"status": "success", "message": "Konfigürasyon kaldırıldı"}
                else:
                    raise HTTPException(status_code=404, detail="Konfigürasyon bulunamadı")
            except Exception as e:
                self.logger.error(f"Konfigürasyon kaldırılırken hata: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint'i"""
            await self.connect_websocket(websocket)
            try:
                while True:
                    # Ping-pong kontrolü
                    await websocket.ping()
                    await asyncio.sleep(WEBSOCKET_PING_INTERVAL)
            except WebSocketDisconnect:
                self.disconnect_websocket(websocket)
            except Exception as e:
                self.logger.error(f"WebSocket hatası: {e}")
                self.disconnect_websocket(websocket)
    
    async def connect_websocket(self, websocket: WebSocket):
        """WebSocket bağlantısını kabul et"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.logger.info(f"WebSocket bağlantısı eklendi. Toplam: {len(self.active_connections)}")
    
    def disconnect_websocket(self, websocket: WebSocket):
        """WebSocket bağlantısını kapat"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        self.logger.info(f"WebSocket bağlantısı kaldırıldı. Toplam: {len(self.active_connections)}")
    
    async def broadcast_data(self, data: Dict):
        """Tüm WebSocket bağlantılarına veri gönder"""
        if not self.active_connections:
            return
        
        message = json.dumps(data)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                self.logger.error(f"WebSocket veri gönderirken hata: {e}")
                disconnected.append(connection)
        
        # Bağlantısı kesilenleri kaldır
        for connection in disconnected:
            self.disconnect_websocket(connection)
    
    def _data_generation_loop(self):
        """Veri üretim döngüsü"""
        while self.running:
            try:
                # Yeni veri üret
                arinc_data = self.data_generator.generate_arinc429_data()
                
                # WebSocket'lere gönder
                asyncio.run(self.broadcast_data({
                    "type": "flight_data",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "latitude": arinc_data.flight_data.latitude,
                        "longitude": arinc_data.flight_data.longitude,
                        "altitude": arinc_data.flight_data.altitude,
                        "airspeed": arinc_data.flight_data.airspeed,
                        "heading": arinc_data.flight_data.heading,
                        "vertical_speed": arinc_data.flight_data.vertical_speed
                    },
                    "arinc_messages": [
                        {
                            "label": msg.label,
                            "sdi": msg.sdi,
                            "data": msg.data,
                            "ssm": msg.ssm,
                            "parity": msg.parity
                        }
                        for msg in arinc_data.arinc_messages
                    ]
                }))
                
                # Harici sistemlere gönder
                self._send_to_external_systems(arinc_data)
                
                time.sleep(1)  # 1 saniye bekle
                
            except Exception as e:
                self.logger.error(f"Veri üretim döngüsünde hata: {e}")
                time.sleep(1)
    
    def _send_to_external_systems(self, arinc_data: ARINC429Data):
        """Harici sistemlere veri gönder"""
        import requests
        
        for config in self.external_configs:
            if not config.enabled:
                continue
            
            try:
                # Veriyi hazırla
                payload = {
                    "timestamp": arinc_data.flight_data.timestamp.isoformat(),
                    "flight_data": {
                        "latitude": arinc_data.flight_data.latitude,
                        "longitude": arinc_data.flight_data.longitude,
                        "altitude": arinc_data.flight_data.altitude,
                        "airspeed": arinc_data.flight_data.airspeed,
                        "heading": arinc_data.flight_data.heading,
                        "vertical_speed": arinc_data.flight_data.vertical_speed
                    },
                    "arinc_messages": [
                        {
                            "label": msg.label,
                            "sdi": msg.sdi,
                            "data": msg.data,
                            "ssm": msg.ssm,
                            "parity": msg.parity
                        }
                        for msg in arinc_data.arinc_messages
                    ]
                }
                
                # POST isteği gönder
                response = requests.post(
                    config.url,
                    json=payload,
                    headers=config.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.logger.debug(f"Veri başarıyla gönderildi: {config.url}")
                else:
                    self.logger.warning(f"Veri gönderilirken hata: {config.url} - {response.status_code}")
                    
            except Exception as e:
                self.logger.error(f"Harici sisteme veri gönderilirken hata: {config.url} - {e}")
    
    def start_data_generation(self):
        """Veri üretimini başlat"""
        if not self.running:
            self.running = True
            self.data_thread = threading.Thread(target=self._data_generation_loop, daemon=True)
            self.data_thread.start()
            self.logger.info("Veri üretimi başlatıldı")
    
    def stop_data_generation(self):
        """Veri üretimini durdur"""
        self.running = False
        if self.data_thread:
            self.data_thread.join(timeout=5)
        self.logger.info("Veri üretimi durduruldu")
    
    def run(self):
        """API sunucusunu çalıştır"""
        self.start_data_generation()
        
        uvicorn.run(
            self.app,
            host=API_HOST,
            port=API_PORT,
            log_level="info"
        )


if __name__ == "__main__":
    # API sunucusunu başlat
    server = ARINC429APIServer()
    
    try:
        print("ARINC 429 API Sunucusu başlatılıyor...")
        print(f"Host: {API_HOST}")
        print(f"Port: {API_PORT}")
        print(f"Debug: {API_DEBUG}")
        print("=" * 50)
        
        server.run()
        
    except KeyboardInterrupt:
        print("\nSunucu durduruluyor...")
        server.stop_data_generation()
    except Exception as e:
        print(f"Sunucu hatası: {e}")
        server.stop_data_generation()
