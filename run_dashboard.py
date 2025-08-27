#!/usr/bin/env python3
"""
ARINC 429 Dashboard Başlatma Scripti
Projeyi kolayca çalıştırmak için
"""

import subprocess
import sys
import time
import os
import signal
import threading
from typing import List

def check_dependencies():
    """Gerekli paketlerin yüklü olup olmadığını kontrol et"""
    required_packages = [
        "fastapi", "uvicorn", "websockets", "streamlit", 
        "pandas", "plotly", "requests", "pydantic", "numpy"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Eksik paketler bulundu:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Paketleri yüklemek için:")
        print("   pip install -r requirements.txt")
        return False
    
    print("✅ Tüm gerekli paketler yüklü")
    return True

def start_api_server():
    """API sunucusunu başlat"""
    print("🚀 API sunucusu başlatılıyor...")
    try:
        process = subprocess.Popen([
            sys.executable, "api_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process
    except Exception as e:
        print(f"❌ API sunucusu başlatılamadı: {e}")
        return None

def start_dashboard():
    """Streamlit dashboard'unu başlat"""
    print("📊 Dashboard başlatılıyor...")
    try:
        process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", "viewer_dashboard.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process
    except Exception as e:
        print(f"❌ Dashboard başlatılamadı: {e}")
        return None

def wait_for_api_server():
    """API sunucusunun hazır olmasını bekle"""
    import requests
    import time
    
    print("⏳ API sunucusunun hazır olması bekleniyor...")
    
    for i in range(30):  # 30 saniye bekle
        try:
            response = requests.get("http://localhost:8000/", timeout=2)
            if response.status_code == 200:
                print("✅ API sunucusu hazır")
                return True
        except:
            pass
        
        time.sleep(1)
        print(f"   {i+1}/30 saniye...")
    
    print("❌ API sunucusu başlatılamadı")
    return False

def print_status(api_process, dashboard_process):
    """Durum bilgilerini yazdır"""
    print("\n" + "="*60)
    print("🎯 ARINC 429 Dashboard Durumu")
    print("="*60)
    
    if api_process and api_process.poll() is None:
        print("✅ API Sunucusu: Çalışıyor (http://localhost:8000)")
        print("   - REST API: http://localhost:8000/api/current-data")
        print("   - WebSocket: ws://localhost:8000/ws")
        print("   - Dokümantasyon: http://localhost:8000/docs")
    else:
        print("❌ API Sunucusu: Çalışmıyor")
    
    if dashboard_process and dashboard_process.poll() is None:
        print("✅ Dashboard: Çalışıyor (http://localhost:8501)")
    else:
        print("❌ Dashboard: Çalışmıyor")
    
    print("\n📋 Kullanım:")
    print("   1. API sunucusu otomatik olarak ARINC 429 verileri üretir")
    print("   2. Dashboard'da gerçek zamanlı verileri görüntüleyin")
    print("   3. Kontrol panelinden uçuş parametrelerini ayarlayın")
    print("   4. Harita ve grafiklerde uçuş rotasını takip edin")
    
    print("\n🔧 Kontroller:")
    print("   - Ctrl+C: Tüm servisleri durdur")
    print("   - Dashboard'da sidebar'dan parametreleri ayarlayın")
    
    print("="*60)

def cleanup(processes: List[subprocess.Popen]):
    """Tüm süreçleri temizle"""
    print("\n🛑 Servisler durduruluyor...")
    
    for process in processes:
        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
    
    print("✅ Tüm servisler durduruldu")

def main():
    """Ana fonksiyon"""
    print("✈️ ARINC 429 Uçuş Verisi Dashboard")
    print("="*50)
    
    # Bağımlılıkları kontrol et
    if not check_dependencies():
        sys.exit(1)
    
    processes = []
    
    try:
        # API sunucusunu başlat
        api_process = start_api_server()
        if not api_process:
            sys.exit(1)
        processes.append(api_process)
        
        # API sunucusunun hazır olmasını bekle
        if not wait_for_api_server():
            cleanup(processes)
            sys.exit(1)
        
        # Dashboard'u başlat
        dashboard_process = start_dashboard()
        if not dashboard_process:
            cleanup(processes)
            sys.exit(1)
        processes.append(dashboard_process)
        
        # Durum bilgilerini yazdır
        print_status(api_process, dashboard_process)
        
        # Ana döngü
        print("\n🔄 Servisler çalışıyor... (Ctrl+C ile durdurun)")
        
        while True:
            time.sleep(1)
            
            # Süreçlerin durumunu kontrol et
            if api_process.poll() is not None:
                print("❌ API sunucusu durdu")
                break
            
            if dashboard_process.poll() is not None:
                print("❌ Dashboard durdu")
                break
    
    except KeyboardInterrupt:
        print("\n🛑 Kullanıcı tarafından durduruldu")
    
    finally:
        cleanup(processes)

if __name__ == "__main__":
    main()
