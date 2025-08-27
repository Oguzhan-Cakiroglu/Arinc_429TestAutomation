"""
ARINC 429 Manuel Veri Girişi Dashboard
Kullanıcının manuel olarak uçuş verilerini girdiği ve ARINC 429 formatında işleyen dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime
import time

from utils.data_models import FlightData, ARINC429Data
from utils.arinc429 import ARINC429Encoder
from config import AVIATION_RANGES


class ManualARINC429Dashboard:
    """Manuel ARINC 429 Dashboard sınıfı"""
    
    def __init__(self):
        self.encoder = ARINC429Encoder()
        self.flight_history = []
        
        # Dashboard ayarları
        st.set_page_config(
            page_title="ARINC 429 Manuel Veri Girişi",
            page_icon="✈️",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def create_data_input_form(self):
        """Veri giriş formu oluştur"""
        st.header("📝 Uçuş Verisi Girişi")
        
        with st.form("flight_data_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Konum Bilgileri")
                latitude = st.number_input(
                    "Enlem (Latitude)",
                    min_value=-90.0,
                    max_value=90.0,
                    value=41.2622,
                    step=0.0001,
                    format="%.4f",
                    help="Enlem değeri (-90 ile +90 arası)"
                )
                
                longitude = st.number_input(
                    "Boylam (Longitude)",
                    min_value=-180.0,
                    max_value=180.0,
                    value=28.7278,
                    step=0.0001,
                    format="%.4f",
                    help="Boylam değeri (-180 ile +180 arası)"
                )
                
                altitude = st.number_input(
                    "İrtifa (Altitude) - feet",
                    min_value=0.0,
                    max_value=50000.0,
                    value=35000.0,
                    step=100.0,
                    help="İrtifa değeri (0-50000 feet)"
                )
            
            with col2:
                st.subheader("Uçuş Parametreleri")
                airspeed = st.number_input(
                    "Hava Hızı (Airspeed) - knots",
                    min_value=0.0,
                    max_value=1000.0,
                    value=450.0,
                    step=1.0,
                    help="Hava hızı (0-1000 knots)"
                )
                
                heading = st.number_input(
                    "Yön (Heading) - derece",
                    min_value=0.0,
                    max_value=360.0,
                    value=270.0,
                    step=0.1,
                    help="Yön değeri (0-360 derece)"
                )
                
                vertical_speed = st.number_input(
                    "Dikey Hız (Vertical Speed) - feet/dakika",
                    min_value=-10000.0,
                    max_value=10000.0,
                    value=0.0,
                    step=10.0,
                    help="Dikey hız (-10000 ile +10000 feet/dakika)"
                )
            
            # Form gönder butonu
            submitted = st.form_submit_button("🚀 Veriyi İşle ve ARINC 429'da Kodla")
            
            if submitted:
                return self.process_flight_data(
                    latitude, longitude, altitude, airspeed, heading, vertical_speed
                )
        
        return None
    
    def process_flight_data(self, latitude, longitude, altitude, airspeed, heading, vertical_speed):
        """Uçuş verisini işle ve ARINC 429 formatında kodla"""
        try:
            # FlightData oluştur
            flight_data = FlightData(
                latitude=latitude,
                longitude=longitude,
                altitude=altitude,
                airspeed=airspeed,
                heading=heading,
                vertical_speed=vertical_speed,
                timestamp=datetime.now()
            )
            
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
            
            # ARINC 429 veri paketi oluştur
            arinc_data = ARINC429Data(
                flight_data=flight_data,
                arinc_messages=arinc_messages,
                raw_data=raw_data
            )
            
            # Geçmişe ekle
            self.flight_history.append(arinc_data)
            
            st.success("✅ Veri başarıyla işlendi ve ARINC 429 formatında kodlandı!")
            return arinc_data
            
        except Exception as e:
            st.error(f"❌ Veri işlenirken hata oluştu: {e}")
            return None
    
    def display_current_data(self, arinc_data):
        """Mevcut veriyi görüntüle"""
        if not arinc_data:
            return
        
        st.header("📊 Mevcut Uçuş Verileri")
        
        flight_data = arinc_data.flight_data
        
        # Metrik kartları
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Enlem",
                value=f"{flight_data.latitude:.6f}°",
                delta=None
            )
            st.metric(
                label="Boylam",
                value=f"{flight_data.longitude:.6f}°",
                delta=None
            )
        
        with col2:
            st.metric(
                label="İrtifa",
                value=f"{flight_data.altitude:.1f} feet",
                delta=None
            )
            st.metric(
                label="Hava Hızı",
                value=f"{flight_data.airspeed:.1f} knots",
                delta=None
            )
        
        with col3:
            st.metric(
                label="Yön",
                value=f"{flight_data.heading:.1f}°",
                delta=None
            )
            st.metric(
                label="Dikey Hız",
                value=f"{flight_data.vertical_speed:.1f} ft/min",
                delta=None
            )
        
        # Zaman damgası
        st.caption(f"Son güncelleme: {flight_data.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def display_arinc429_data(self, arinc_data):
        """ARINC 429 verilerini görüntüle"""
        if not arinc_data:
            return
        
        st.header("🔧 ARINC 429 Kodlanmış Veriler")
        
        # ARINC 429 mesaj tablosu
        st.subheader("ARINC 429 Mesajları")
        
        arinc_messages = arinc_data.arinc_messages
        arinc_data_list = []
        
        for msg in arinc_messages:
            arinc_data_list.append({
                "Label": f"0x{msg.label}",
                "SDI": msg.sdi,
                "Data (Binary)": msg.data,
                "Data (Hex)": f"0x{int(msg.data, 2):05X}",
                "SSM": msg.ssm,
                "Parity": msg.parity,
                "32-bit Word": f"0x{int(msg.label, 16):02X}{int(msg.sdi, 2):02X}{int(msg.data, 2):05X}{int(msg.ssm, 2):02X}{int(msg.parity, 2):02X}"
            })
        
        df = pd.DataFrame(arinc_data_list)
        st.dataframe(df, use_container_width=True)
        
        # Label açıklamaları
        st.subheader("Label Açıklamaları")
        label_descriptions = {
            "6A": "Enlem (Latitude)",
            "6B": "Boylam (Longitude)",
            "6C": "İrtifa (Altitude)",
            "6D": "Hava Hızı (Airspeed)",
            "6E": "Yön (Heading)",
            "6F": "Dikey Hız (Vertical Speed)"
        }
        
        for label, description in label_descriptions.items():
            st.write(f"**0x{label}**: {description}")
        
        # JSON formatında dışa aktarma
        st.subheader("📤 Veri Dışa Aktarma")
        
        # JSON formatı
        json_data = {
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
        
        st.json(json_data)
        
        # JSON indirme butonu
        st.download_button(
            label="📥 JSON Dosyası İndir",
            data=json.dumps(json_data, indent=2),
            file_name=f"arinc429_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    def display_map(self, arinc_data):
        """Harita görüntüleme"""
        if not arinc_data:
            return
        
        st.header("🗺️ Uçak Konumu")
        
        flight_data = arinc_data.flight_data
        
        # Harita verisi
        map_data = pd.DataFrame({
            "latitude": [flight_data.latitude],
            "longitude": [flight_data.longitude],
            "altitude": [flight_data.altitude],
            "airspeed": [flight_data.airspeed]
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
                center=dict(lat=flight_data.latitude, lon=flight_data.longitude)
            ),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def display_history(self):
        """Geçmiş verileri görüntüle"""
        if not self.flight_history:
            return
        
        st.header("📈 Veri Geçmişi")
        
        # Geçmiş verileri DataFrame'e çevir
        history_data = []
        for arinc_data in self.flight_history:
            flight_data = arinc_data.flight_data
            history_data.append({
                "timestamp": flight_data.timestamp,
                "latitude": flight_data.latitude,
                "longitude": flight_data.longitude,
                "altitude": flight_data.altitude,
                "airspeed": flight_data.airspeed,
                "heading": flight_data.heading,
                "vertical_speed": flight_data.vertical_speed
            })
        
        df = pd.DataFrame(history_data)
        
        # Geçmiş veri tablosu
        st.subheader("Geçmiş Veriler")
        st.dataframe(df, use_container_width=True)
        
        # Zaman serisi grafikleri
        if len(history_data) > 1:
            st.subheader("Zaman Serisi Grafikleri")
            
            fig = make_subplots(
                rows=3, cols=2,
                subplot_titles=("İrtifa", "Hava Hızı", "Yön", "Dikey Hız", "Enlem", "Boylam")
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
    
    def create_sidebar_controls(self):
        """Sidebar kontrolleri"""
        st.sidebar.header("⚙️ Kontroller")
        
        # Geçmişi temizle
        if st.sidebar.button("🗑️ Geçmişi Temizle"):
            self.flight_history.clear()
            st.success("Geçmiş temizlendi!")
            st.rerun()
        
        # Geçmiş veri sayısı
        st.sidebar.subheader("Geçmiş Veri Sayısı")
        st.sidebar.write(f"📊 {len(self.flight_history)} kayıt")
        
        # Hızlı veri girişi
        st.sidebar.subheader("🚀 Hızlı Veri Girişi")
        
        # Önceden tanımlanmış konumlar
        preset_locations = {
            "İstanbul Havalimanı": (41.2622, 28.7278),
            "Ankara Esenboğa": (40.1281, 32.9951),
            "İzmir Adnan Menderes": (38.2921, 27.1567),
            "Antalya Havalimanı": (36.8981, 30.8006)
        }
        
        selected_location = st.sidebar.selectbox(
            "Önceden Tanımlı Konumlar",
            list(preset_locations.keys())
        )
        
        if st.sidebar.button("📍 Seçili Konumu Kullan"):
            lat, lon = preset_locations[selected_location]
            st.session_state.preset_lat = lat
            st.session_state.preset_lon = lon
            st.success(f"{selected_location} konumu seçildi!")
    
    def run_dashboard(self):
        """Dashboard'u çalıştır"""
        st.title("✈️ ARINC 429 Manuel Veri Girişi Dashboard")
        st.markdown("---")
        
        # Sidebar kontrolleri
        self.create_sidebar_controls()
        
        # Ana içerik
        tab1, tab2, tab3, tab4 = st.tabs(["📝 Veri Girişi", "📊 Mevcut Veri", "🔧 ARINC 429", "📈 Geçmiş"])
        
        with tab1:
            # Veri giriş formu
            arinc_data = self.create_data_input_form()
            
            # Eğer veri işlendiyse, diğer tablarda göster
            if arinc_data:
                st.session_state.current_data = arinc_data
        
        with tab2:
            # Mevcut veriyi göster
            current_data = st.session_state.get('current_data', None)
            if current_data:
                self.display_current_data(current_data)
                self.display_map(current_data)
            else:
                st.info("📝 Lütfen önce 'Veri Girişi' sekmesinden veri girin.")
        
        with tab3:
            # ARINC 429 verilerini göster
            current_data = st.session_state.get('current_data', None)
            if current_data:
                self.display_arinc429_data(current_data)
            else:
                st.info("📝 Lütfen önce 'Veri Girişi' sekmesinden veri girin.")
        
        with tab4:
            # Geçmiş verileri göster
            self.display_history()
        
        # Alt bilgi
        st.markdown("---")
        st.caption("ARINC 429 Manuel Veri Girişi Dashboard v1.0.0 | Manuel havacılık verisi girişi ve ARINC 429 kodlama sistemi")


def main():
    """Ana fonksiyon"""
    dashboard = ManualARINC429Dashboard()
    dashboard.run_dashboard()


if __name__ == "__main__":
    main()
