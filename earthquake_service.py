"""
Deprem Veri Servisi
Kandilli Rasathanesi ve AFAD verilerini çeker
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

KANDILLI_URL = "http://www.koeri.boun.edu.tr/scripts/lst0.asp"
AFAD_URL = "https://deprem.afad.gov.tr/apiv2/event/filter"

# Cache için
earthquake_cache = {
    'data': [],
    'last_update': None
}

def parse_kandilli():
    """Kandilli Rasathanesi'nden deprem verilerini çek"""
    try:
        response = requests.get(KANDILLI_URL, timeout=10)
        # UTF-8 encoding düzelt
        response.encoding = 'iso-8859-9'  # Turkish encoding
        
        lines = response.text.split('\n')
        earthquakes = []
        
        # HTML içindeki <pre> tagını bul
        in_pre = False
        for line in lines:
            if '<pre>' in line.lower():
                in_pre = True
                continue
            if '</pre>' in line.lower():
                break
            
            if in_pre and line.strip():
                # Başlık satırını atla
                if 'Date' in line or 'Tarih' in line or '----' in line:
                    continue
                
                # Satırı parse et
                parts = line.split()
                if len(parts) >= 8:
                    try:
                        date = parts[0]
                        time = parts[1]
                        lat = float(parts[2])
                        lon = float(parts[3])
                        depth = float(parts[4])
                        magnitude_type = parts[5]
                        magnitude = float(parts[6])
                        
                        # Lokasyon bilgisi (kalan kısım)
                        location = ' '.join(parts[7:])
                        # Gereksiz karakterleri temizle
                        location = location.replace('İlksel', '').replace('Revize01', '').strip()
                        # "-.-" gibi anlamsız kısımları temizle
                        location = location.replace('-.-', '').strip()
                        
                        # Tarih formatı: YYYY.MM.DD HH:MM:SS
                        earthquake_time = datetime.strptime(f"{date} {time}", "%Y.%m.%d %H:%M:%S")
                        
                        earthquakes.append({
                            'source': 'Kandilli',
                            'magnitude': magnitude,
                            'magnitude_type': magnitude_type,
                            'location': location,
                            'latitude': lat,
                            'longitude': lon,
                            'depth': depth,
                            'time': earthquake_time.isoformat(),
                            'time_formatted': earthquake_time.strftime("%d.%m.%Y %H:%M:%S")
                        })
                    except (ValueError, IndexError):
                        continue
        
        return earthquakes[:100]  # Son 100 deprem
    
    except Exception as e:
        print(f"Kandilli hatası: {e}")
        return []


def parse_afad():
    """AFAD'dan deprem verilerini çek - Web scraping"""
    try:
        url = "https://deprem.afad.gov.tr/last-earthquakes.html"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        earthquakes = []
        
        # Tablo satırlarını bul
        table = soup.find('table')
        if not table:
            print("AFAD: Tablo bulunamadı")
            return []
        
        rows = table.find_all('tr')[1:]  # İlk satır başlık
        
        for row in rows[:100]:  # İlk 100 satır
            try:
                cols = row.find_all('td')
                if len(cols) < 7:
                    continue
                
                # AFAD tablo formatı: Tarih(TS) | Enlem | Boylam | Derinlik | Tip | Büyüklük | Yer
                datetime_str = cols[0].text.strip()
                lat = cols[1].text.strip()
                lon = cols[2].text.strip()
                depth = cols[3].text.strip()
                # magnitude_type = cols[4].text.strip()
                magnitude = cols[5].text.strip()
                location = cols[6].text.strip()
                
                # Tarih parse et: YYYY-MM-DD HH:MM:SS
                try:
                    earthquake_time = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
                except:
                    continue
                
                # Sayıları parse et
                mag = float(magnitude)
                latitude = float(lat)
                longitude = float(lon)
                dep = float(depth)
                
                earthquakes.append({
                    'source': 'AFAD',
                    'magnitude': mag,
                    'magnitude_type': 'ML',
                    'location': location,
                    'latitude': latitude,
                    'longitude': longitude,
                    'depth': dep,
                    'time': earthquake_time.isoformat(),
                    'time_formatted': earthquake_time.strftime("%d.%m.%Y %H:%M:%S")
                })
                
            except (ValueError, IndexError, AttributeError) as e:
                continue
        
        print(f"AFAD'dan {len(earthquakes)} deprem verisi çekildi")
        return earthquakes
    
    except Exception as e:
        print(f"AFAD hatası: {e}")
        return []


def get_earthquakes(force_update=False):
    """
    Deprem verilerini getir (cache'li)
    5 dakikada bir günceller
    """
    global earthquake_cache
    
    now = datetime.now()
    
    # Cache kontrolü
    if not force_update and earthquake_cache['last_update']:
        time_diff = (now - earthquake_cache['last_update']).total_seconds()
        if time_diff < 300:  # 5 dakika
            return earthquake_cache['data']
    
    # Kandilli ve AFAD'dan veri çek
    print("Deprem verileri güncelleniyor...")
    kandilli_data = parse_kandilli()
    afad_data = parse_afad()
    
    # Birleştir
    all_earthquakes = kandilli_data + afad_data
    
    # Tekilleştirme: Aynı depremi (zaman ve konum yakınlığı) kontrol et
    unique_earthquakes = []
    
    for eq in all_earthquakes:
        is_duplicate = False
        eq_time = datetime.fromisoformat(eq['time'])
        
        for existing in unique_earthquakes:
            existing_time = datetime.fromisoformat(existing['time'])
            
            # Zaman farkı 2 dakikadan azsa
            time_diff_seconds = abs((eq_time - existing_time).total_seconds())
            
            # Konum farkı (basit mesafe hesabı - yaklaşık)
            lat_diff = abs(eq['latitude'] - existing['latitude'])
            lon_diff = abs(eq['longitude'] - existing['longitude'])
            
            # Büyüklük farkı
            mag_diff = abs(eq['magnitude'] - existing['magnitude'])
            
            # Aynı deprem kriterleri:
            # - 2 dakika içinde
            # - 0.1 derece yakınlık (yaklaşık 10-15 km)
            # - Büyüklük farkı 0.3'ten az
            if (time_diff_seconds < 120 and 
                lat_diff < 0.1 and 
                lon_diff < 0.1 and 
                mag_diff < 0.3):
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_earthquakes.append(eq)
    
    # Zamana göre sırala (en yeni önce)
    unique_earthquakes.sort(key=lambda x: x['time'], reverse=True)
    
    # En son 200 depremi tut
    unique_earthquakes = unique_earthquakes[:200]
    
    # Cache güncelle
    earthquake_cache['data'] = unique_earthquakes
    earthquake_cache['last_update'] = now
    
    print(f"Toplam {len(all_earthquakes)} deprem → Tekilleştirme sonrası {len(unique_earthquakes)} deprem")
    
    return unique_earthquakes


if __name__ == "__main__":
    # Test
    earthquakes = get_earthquakes(force_update=True)
    print(f"\nToplam {len(earthquakes)} deprem bulundu\n")
    
    if earthquakes:
        print("Son 5 deprem:")
        for eq in earthquakes[:5]:
            print(f"{eq['time_formatted']} - M{eq['magnitude']} - {eq['location']} ({eq['source']})")
