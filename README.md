# ARINC 429 Uçuş Verisi Dashboard Projesi

Bu proje, gerçek zamanlı ARINC 429 uçuş verisi üreten ve görüntüleyen iki ayrı dashboard'dan oluşur.

## Proje Yapısı

```
Arinc429_Automation/
├── requirements.txt
├── README.md
├── data_generator.py      # ARINC 429 veri üretici
├── api_server.py          # FastAPI WebSocket/REST API sunucusu
├── viewer_dashboard.py    # Streamlit görüntüleme dashboard'u
├── config.py              # Konfigürasyon ayarları
└── utils/
    ├── __init__.py
    ├── arinc429.py        # ARINC 429 kodlama/çözme mantığı
    └── data_models.py     # Veri modelleri
```

## Kurulum

1. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

## Kullanım

### 1. Veri Üretici ve API Sunucusu
```bash
python api_server.py
```
Bu komut hem ARINC 429 verilerini üretir hem de WebSocket/REST API sunucusunu başlatır.

### 2. Görüntüleme Dashboard'u
```bash
streamlit run viewer_dashboard.py
```

## Özellikler

- **Gerçek zamanlı ARINC 429 veri üretimi**: Enlem, boylam, irtifa, hava hızı, yön, dikey hız
- **WebSocket desteği**: Gerçek zamanlı veri iletimi
- **REST API**: HTTP endpoint'leri ile veri erişimi
- **Streamlit dashboard**: Kullanıcı dostu görsel arayüz
- **Harici dashboard entegrasyonu**: Verileri başka sistemlere gönderme
- **Gerçekçi havacılık verileri**: ARINC 429 standartlarına uygun kodlama

## ARINC 429 Label'ları

- **0x6A**: Enlem (Latitude)
- **0x6B**: Boylam (Longitude)  
- **0x6C**: İrtifa (Altitude)
- **0x6D**: Hava Hızı (Airspeed)
- **0x6E**: Yön (Heading)
- **0x6F**: Dikey Hız (Vertical Speed)

## API Endpoint'leri

- `GET /api/current-data`: Mevcut verileri al
- `GET /api/historical-data`: Geçmiş verileri al
- `WebSocket /ws`: Gerçek zamanlı veri akışı
- `POST /api/send-external`: Harici sisteme veri gönder
# Arinc_429TestAutomation
