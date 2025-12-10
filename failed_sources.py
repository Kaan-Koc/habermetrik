"""
Habermetre - Başarısız Kaynak Takip Modülü
"""

from collections import defaultdict
from datetime import datetime

# Her kaynak için hata sayacı
error_counts = defaultdict(int)
last_errors = {}


def log_failed_source(source_key, url, error_type, error_msg):
    """Başarısız kaynağı logla"""
    error_counts[source_key] += 1
    last_errors[source_key] = {
        'url': url,
        'error_type': error_type,
        'error_msg': error_msg,
        'timestamp': datetime.now(),
        'count': error_counts[source_key]
    }
    
    # Konsola yazdır
    print(f"[{source_key}] HATA #{error_counts[source_key]}: {error_type} - {error_msg[:100]}")


def log_success_source(source_key):
    """Başarılı kaynağı logla - hata sayacını sıfırla"""
    if source_key in error_counts:
        error_counts[source_key] = 0


def should_skip_source(source_key, max_consecutive=10):
    """Çok fazla hata varsa kaynağı atla"""
    return error_counts.get(source_key, 0) >= max_consecutive


def get_failed_sources():
    """Başarısız kaynakları getir"""
    return dict(last_errors)


def get_error_count(source_key):
    """Kaynak için hata sayısını getir"""
    return error_counts.get(source_key, 0)


def get_all_sources_status():
    """
    Tüm kaynakların durumunu getir
    
    Returns:
        {
            'working': [...],  # Çalışan kaynaklar
            'failed': [...],   # Başarısız kaynaklar
            'total': int
        }
    """
    from config import RSS_SOURCES
    
    working = []
    failed = []
    
    for source_key, source_config in RSS_SOURCES.items():
        error_count = get_error_count(source_key)
        
        source_info = {
            'key': source_key,
            'name': source_config['name'],
            'url': source_config['url'],
            'error_count': error_count
        }
        
        # 10+ hata = başarısız
        if error_count >= 10:
            source_info['status'] = 'failed'
            source_info['last_error'] = last_errors.get(source_key, {}).get('error_msg', 'Unknown')
            failed.append(source_info)
        else:
            source_info['status'] = 'working'
            working.append(source_info)
    
    return {
        'working': working,
        'failed': failed,
        'total': len(RSS_SOURCES)
    }

