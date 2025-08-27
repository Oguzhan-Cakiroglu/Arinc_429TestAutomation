"""
ARINC 429 Uçuş Verisi Dashboard
Streamlit tabanlı gerçek zamanlı veri görüntüleme dashboard'u
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
import time
from datetime import datetime, timedelta
import threading
from typing import Dict, List, Optional
import websocket
import queue

from config import API_HOST, API_PORT, STREAMLIT_CONFIG


class ARINC429Dashboard:
    """ARINC 429 Dashboard sınıfı"""
    
    def __init__(self):
        self.api_url = f"http://{API_HOST}:{API_PORT}"
        self.websocket_url = f"ws://{API_HOST}:{API_PORT}/ws"
        self.data_queue = queue.Queue()
        self.current_data = None
        self.historical_data = []
        self.websocket = None
        self.websocket_thread = None
        self.running = False
        
        # Dashboard ayarları
        st.set_page_config(
            page_title=STREAMLIT_CONFIG["page_title"],
            page_icon=STREAMLIT_CONFIG["page_icon"],
            layout=STREAMLIT_CONFIG["layout"],
            initial_sidebar_state=STREAMLIT_CONFIG["initial_sidebar_state"]
        )
    
    def setup_websocket(self):
        """WebSocket bağlantısını kur"""
        try:
            self.websocket = websocket.WebSocketApp(
                self.websocket_url,
                on_message=self.on_websocket_message,
                on_error=self.on_websocket_error,
                on_close=self.on_websocket_close,
                on_open=self.on_websocket_open
            )
            
            self.websocket_thread = threading.Thread(target=self.websocket.run_forever, daemon=True)
            self.websocket_thread.start()
            self.running = True
            
        except Exception as e:
            st.error(f"WebSocket bağlantısı kurulamadı: {e}")
    
    def on_websocket_message(self, ws, message):
        """WebSocket mesajını işle"""
        try:
            data = json.loads(message)
            self.data_queue.put(data)
        except Exception as e:
            st.error(f"WebSocket mesajı işlenirken hata: {e}")
    
    def on_websocket_error(self, ws, error):
        """WebSocket hatası"""
        st.error(f"WebSocket hatası: {error}")
    
    def on_websocket_close(self, ws, close_status_code, close_msg):
        """WebSocket bağlantısı kapandı"""
        st.warning("WebSocket bağlantısı kapandı")
    
    def on_websocket_open(self, ws):
        """WebSocket bağlantısı açıldı"""
        st.success("WebSocket bağlantısı kuruldu")
    
    def get_current_data(self) -> Optional[Dict]:
        """API'den mevcut veriyi al"""
        try:
            response = requests.get(f"{self.api_url}/api/current-data", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"API hatası: {response.status_code}")
                return None
        except Exception as e:
            st.error(f"Veri alınırken hata: {e}")
            return None
    
    def get_historical_data(self, limit: int = 100) -> List[Dict]:
        """API'den geçmiş verileri al"""
        try:
            response = requests.get(f"{self.api_url}/api/historical-data?limit={limit}", timeout=5)
            if response.status_code == 200:
                return response.json()["data"]
            else:
                st.error(f"Geçmiş veri alınırken hata: {response.status_code}")
                return []
        except Exception as e:
            st.error(f"Geçmiş veri alınırken hata: {e}")
            return []
    
    def reset_position(self, latitude: float, longitude: float):
        """Uçak pozisyonunu sıfırla"""
        try:
            response = requests.post(
                f"{self.api_url}/api/reset-position",
                params={"latitude": latitude, "longitude": longitude},
                timeout=5
            )
            if response.status_code == 200:
                st.success("Pozisyon sıfırlandı")
            else:
                st.error("Pozisyon sıfırlanırken hata oluştu")
        except Exception as e:
            st.error(f"Pozisyon sıfırlanırken hata: {e}")
    
    def set_flight_parameters(self, heading_change: float, altitude_change: float, speed_change: float):
        """Uçuş parametrelerini ayarla"""
        try:
            response = requests.post(
                f"{self.api_url}/api/set-flight-parameters",
                params={
                    "heading_change": heading_change,
                    "altitude_change": altitude_change,
                    "speed_change": speed_change
                },
                timeout=5
            )
            if response.status_code == 200:
                st.success("Uçuş parametreleri güncellendi")
            else:
                st.error("Uçuş parametreleri güncellenirken hata oluştu")
        except Exception as e:
            st.error(f"Uçuş parametreleri güncellenirken hata: {e}")
    
    def create_metrics_display(self, data: Dict):
        """Metrikleri görüntüle"""
        if not data:
            return
        
        flight_data = data.get("data", {})
        
        # Metrik kartları
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Enlem",
                value=f"{flight_data.get('latitude', 0):.6f}°",
                delta=None
            )
            st.metric(
                label="Boylam",
                value=f"{flight_data.get('longitude', 0):.6f}°",
                delta=None
            )
        
        with col2:
            st.metric(
                label="İrtifa",
                value=f"{flight_data.get('altitude', 0):.1f} feet",
                delta=None
            )
            st.metric(
                label="Hava Hızı",
                value=f"{flight_data.get('airspeed', 0):.1f} knots",
                delta=None
            )
        
        with col3:
            st.metric(
                label="Yön",
                value=f"{flight_data.get('heading', 0):.1f}°",
                delta=None
            )
            st.metric(
                label="Dikey Hız",
                value=f"{flight_data.get('vertical_speed', 0):.1f} ft/min",
                delta=None
            )
    
    def create_map_display(self, data: Dict):
        """Harita görüntüleme"""
        if not data:
            return
        
        flight_data = data.get("data", {})
        latitude = flight_data.get("latitude", 0)
        longitude = flight_data.get("longitude", 0)
        
        # Harita verisi
        map_data = pd.DataFrame({
            "latitude": [latitude],
            "longitude": [longitude],
            "altitude": [flight_data.get("altitude", 0)],
            "airspeed": [flight_data.get("airspeed", 0)]
        })
        
        # Plotly harita
        fig = px.scatter_mapbox(
            map_data,
            lat="latitude",
            lon="longitude",
            size="airspeed",
            color="altitude",
            hover_data=["altitude", "airspeed"],
            zoom=10,
            mapbox_style="open-street-map",
            title="Uçak Konumu"
        )
        
        fig.update_layout(
            mapbox=dict(
                center=dict(lat=latitude, lon=longitude)
            ),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def create_trajectory_plot(self, historical_data: List[Dict]):
        """Uçuş rotası grafiği"""
        if not historical_data:
            return
        
        # Veriyi DataFrame'e çevir
        df = pd.DataFrame(historical_data)
        
        # Rota grafiği
        fig = px.line(
            df,
            x="longitude",
            y="latitude",
            title="Uçuş Rotası",
            labels={"longitude": "Boylam", "latitude": "Enlem"}
        )
        
        # Son noktayı vurgula
        fig.add_scatter(
            x=[df["longitude"].iloc[-1]],
            y=[df["latitude"].iloc[-1]],
            mode="markers",
            marker=dict(size=10, color="red"),
            name="Mevcut Konum"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def create_time_series_plots(self, historical_data: List[Dict]):
        """Zaman serisi grafikleri"""
        if not historical_data:
            return
        
        df = pd.DataFrame(historical_data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        # Alt grafikler
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=("İrtifa", "Hava Hızı", "Yön", "Dikey Hız", "Enlem", "Boylam"),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # İrtifa
        fig.add_trace(
            go.Scatter(x=df["timestamp"], y=df["altitude"], name="İrtifa"),
            row=1, col=1
        )
        
        # Hava hızı
        fig.add_trace(
            go.Scatter(x=df["timestamp"], y=df["airspeed"], name="Hava Hızı"),
            row=1, col=2
        )
        
        # Yön
        fig.add_trace(
            go.Scatter(x=df["timestamp"], y=df["heading"], name="Yön"),
            row=2, col=1
        )
        
        # Dikey hız
        fig.add_trace(
            go.Scatter(x=df["timestamp"], y=df["vertical_speed"], name="Dikey Hız"),
            row=2, col=2
        )
        
        # Enlem
        fig.add_trace(
            go.Scatter(x=df["timestamp"], y=df["latitude"], name="Enlem"),
            row=3, col=1
        )
        
        # Boylam
        fig.add_trace(
            go.Scatter(x=df["timestamp"], y=df["longitude"], name="Boylam"),
            row=3, col=2
        )
        
        fig.update_layout(height=600, title_text="Zaman Serisi Grafikleri")
        st.plotly_chart(fig, use_container_width=True)
    
    def create_arinc429_display(self, data: Dict):
        """ARINC 429 verilerini görüntüle"""
        if not data or "arinc_messages" not in data:
            return
        
        st.subheader("ARINC 429 Mesajları")
        
        arinc_messages = data["arinc_messages"]
        
        # ARINC 429 tablosu
        arinc_data = []
        for msg in arinc_messages:
            arinc_data.append({
                "Label": f"0x{msg['label']}",
                "SDI": msg["sdi"],
                "Data": msg["data"],
                "SSM": msg["ssm"],
                "Parity": msg["parity"]
            })
        
        df = pd.DataFrame(arinc_data)
        st.dataframe(df, use_container_width=True)
        
        # Label açıklamaları
        label_descriptions = {
            "6A": "Enlem (Latitude)",
            "6B": "Boylam (Longitude)",
            "6C": "İrtifa (Altitude)",
            "6D": "Hava Hızı (Airspeed)",
            "6E": "Yön (Heading)",
            "6F": "Dikey Hız (Vertical Speed)"
        }
        
        st.subheader("Label Açıklamaları")
        for label, description in label_descriptions.items():
            st.write(f"**0x{label}**: {description}")
    
    def create_control_panel(self):
        """Kontrol paneli"""
        st.sidebar.header("Kontrol Paneli")
        
        # Pozisyon sıfırlama
        st.sidebar.subheader("Pozisyon Sıfırlama")
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            lat = st.number_input("Enlem", value=41.2622, format="%.4f")
        with col2:
            lon = st.number_input("Boylam", value=28.7278, format="%.4f")
        
        if st.sidebar.button("Pozisyonu Sıfırla"):
            self.reset_position(lat, lon)
        
        # Uçuş parametreleri
        st.sidebar.subheader("Uçuş Parametreleri")
        heading_change = st.sidebar.slider("Yön Değişimi (derece/s)", -5.0, 5.0, 0.0, 0.1)
        altitude_change = st.sidebar.slider("İrtifa Değişimi (ft/min)", -1000, 1000, 0, 50)
        speed_change = st.sidebar.slider("Hız Değişimi (knots/s)", -10, 10, 0, 0.5)
        
        if st.sidebar.button("Parametreleri Uygula"):
            self.set_flight_parameters(heading_change, altitude_change, speed_change)
        
        # Bağlantı durumu
        st.sidebar.subheader("Bağlantı Durumu")
        if self.websocket and self.websocket.sock and self.websocket.sock.connected:
            st.sidebar.success("WebSocket Bağlı")
        else:
            st.sidebar.error("WebSocket Bağlantısı Yok")
        
        # Yenileme hızı
        st.sidebar.subheader("Güncelleme Ayarları")
        refresh_rate = st.sidebar.selectbox(
            "Yenileme Hızı",
            ["1 saniye", "2 saniye", "5 saniye", "10 saniye"],
            index=0
        )
        
        return refresh_rate
    
    def run_dashboard(self):
        """Dashboard'u çalıştır"""
        st.title("✈️ ARINC 429 Uçuş Verisi Dashboard")
        st.markdown("---")
        
        # Kontrol paneli
        refresh_rate = self.create_control_panel()
        
        # WebSocket bağlantısını kur
        if not self.websocket or not self.websocket.sock or not self.websocket.sock.connected:
            self.setup_websocket()
        
        # Ana içerik
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Gerçek Zamanlı Veriler", "🗺️ Harita", "📈 Grafikler", "🔧 ARINC 429"])
        
        with tab1:
            st.header("Gerçek Zamanlı Uçuş Verileri")
            
            # WebSocket'ten gelen veriyi kontrol et
            try:
                while not self.data_queue.empty():
                    self.current_data = self.data_queue.get_nowait()
            except queue.Empty:
                pass
            
            # Eğer WebSocket verisi yoksa API'den al
            if not self.current_data:
                self.current_data = self.get_current_data()
            
            if self.current_data:
                self.create_metrics_display(self.current_data)
                
                # Zaman damgası
                timestamp = self.current_data.get("timestamp", datetime.now().isoformat())
                st.caption(f"Son güncelleme: {timestamp}")
            else:
                st.warning("Veri alınamıyor. API sunucusunun çalıştığından emin olun.")
        
        with tab2:
            st.header("Uçak Konumu")
            
            if self.current_data:
                self.create_map_display(self.current_data)
            else:
                st.warning("Harita verisi mevcut değil.")
        
        with tab3:
            st.header("Uçuş Grafikleri")
            
            # Geçmiş verileri al
            historical_data = self.get_historical_data(100)
            
            if historical_data:
                # Rota grafiği
                st.subheader("Uçuş Rotası")
                self.create_trajectory_plot(historical_data)
                
                # Zaman serisi grafikleri
                st.subheader("Zaman Serisi Grafikleri")
                self.create_time_series_plots(historical_data)
            else:
                st.warning("Geçmiş veri mevcut değil.")
        
        with tab4:
            st.header("ARINC 429 Verileri")
            
            if self.current_data:
                self.create_arinc429_display(self.current_data)
            else:
                st.warning("ARINC 429 verisi mevcut değil.")
        
        # Alt bilgi
        st.markdown("---")
        st.caption("ARINC 429 Uçuş Verisi Dashboard v1.0.0 | Gerçek zamanlı havacılık verisi görüntüleme sistemi")


def main():
    """Ana fonksiyon"""
    dashboard = ARINC429Dashboard()
    dashboard.run_dashboard()


if __name__ == "__main__":
    main()
