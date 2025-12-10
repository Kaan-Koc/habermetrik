"""
HaberMetrik - Veritabanı İşlemleri
"""

import sqlite3
import hashlib
from datetime import datetime, timedelta
from config import DATABASE_PATH, SIMILARITY_THRESHOLD
from collections import Counter
import re


def get_connection():
    """Veritabanı bağlantısı al"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Veritabanını başlat"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Kullanıcılar tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Haberler tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            link TEXT UNIQUE NOT NULL,
            description TEXT,
            source TEXT NOT NULL,
            pub_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # İndeksler
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_source ON news(source)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_pub_date ON news(pub_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_created_at ON news(created_at)')
    
    conn.commit()
    conn.close()
    print("Veritabanı başlatıldı")


def hash_password(password):
    """Şifreyi hashle"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_user(username, password):
    """Kullanıcı doğrula"""
    conn = get_connection()
    cursor = conn.cursor()
    
    password_hash = hash_password(password)
    cursor.execute(
        'SELECT * FROM users WHERE username = ? AND password_hash = ?',
        (username, password_hash)
    )
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return dict(user)
    return None


def ensure_admin_exists():
    """Varsayılan admin kullanıcısını oluştur"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        password_hash = hash_password('admin123')
        cursor.execute(
            'INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
            ('admin', password_hash, 'admin')
        )
        conn.commit()
        print("Varsayılan admin oluşturuldu (kullanıcı: admin, şifre: admin123)")
    
    conn.close()


def get_all_users():
    """Tüm kullanıcıları getir"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, role, created_at FROM users ORDER BY created_at DESC')
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return users


def create_user(username, password, role='user'):
    """Yeni kullanıcı oluştur"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        password_hash = hash_password(password)
        cursor.execute(
            'INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
            (username, password_hash, role)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None


def delete_user(user_id):
    """Kullanıcı sil"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def get_user_by_id(user_id):
    """ID'ye göre kullanıcı getir"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return dict(user)
    return None


def insert_many_news(items):
    """Toplu haber ekle"""
    if not items:
        return 0
    
    conn = get_connection()
    cursor = conn.cursor()
    inserted = 0
    
    # Gelecek kontrolü (Güvenlik) - Maksimim 15 dakika tolerans
    from datetime import datetime, timedelta
    cutoff_date = datetime.utcnow() + timedelta(minutes=15)
    
    for item in items:
        # Tarih kontrolü: Eğer tarih 1 günden daha ileriyse (hatalı parser/sistem saati) KAYDETME.
        pub_date_str = item.get('pub_date')
        if pub_date_str:
            try:
                # Format: YYYY-MM-DD HH:MM:SS (parsers.py bu formatı garantiler)
                pd = datetime.strptime(pub_date_str, '%Y-%m-%d %H:%M:%S')
                if pd > cutoff_date:
                    continue # Hatalı gelecek verisi, atla
            except:
                pass # Parse edilemediyse (nadiren), olduğu gibi devam etsin (veya atlasın?)

        try:
            cursor.execute(
                'INSERT INTO news (title, link, description, source, pub_date, image_url) VALUES (?, ?, ?, ?, ?, ?)',
                (item['title'], item['link'], item.get('description', ''), 
                 item['source'], item.get('pub_date'), item.get('image_url'))
            )
            inserted += 1
        except sqlite3.IntegrityError:
            # Link zaten var
            pass
    
    conn.commit()
    conn.close()
    return inserted


def get_news_count():
    """Toplam haber sayısı"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as count FROM news')
    count = cursor.fetchone()['count']
    conn.close()
    return count


def delete_news_by_source(source, limit=100):
    """Kaynağa göre haber sil"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM news WHERE source = ? LIMIT ?', (source, limit))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted


def delete_news_by_age(hours, limit=100):
    """Yaşa göre haber sil"""
    conn = get_connection()
    cursor = conn.cursor()
    cutoff_date = datetime.utcnow() - timedelta(hours=hours)
    cursor.execute(
        'DELETE FROM news WHERE created_at < ? LIMIT ?',
        (cutoff_date, limit)
    )
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted


def search_news(query, limit=200):
    """Haber ara"""
    conn = get_connection()
    cursor = conn.cursor()
    
    search_term = f'%{query}%'
    cursor.execute(
        '''SELECT * FROM news 
           WHERE title LIKE ? OR description LIKE ?
           ORDER BY pub_date DESC LIMIT ?''',
        (search_term, search_term, limit)
    )
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_today_news_count():
    """Son 6 saatte eklenen haber sayısı"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Son 6 saat
    from datetime import datetime, timedelta
    six_hours_ago = datetime.utcnow() - timedelta(hours=6)
    
    cursor.execute(
        'SELECT COUNT(*) as count FROM news WHERE COALESCE(pub_date, created_at) >= ?',
        (six_hours_ago,)
    )
    count = cursor.fetchone()['count']
    conn.close()
    return count


def get_total_news_count():
    """Toplam haber sayısı (tüm zamanlar)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as count FROM news')
    count = cursor.fetchone()['count']
    conn.close()
    return count


def get_news_by_source_today(limit=10):
    """Kaynaklara göre son 6 saatin haber sayıları (aktif toplama)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    from datetime import datetime, timedelta
    # Son 6 saat (aktif toplanan haberler)
    six_hours_ago = datetime.utcnow() - timedelta(hours=6)
    
    cursor.execute(
        '''SELECT source, COUNT(*) as count 
           FROM news 
           WHERE COALESCE(pub_date, created_at) >= ?
           GROUP BY source 
           ORDER BY count DESC 
           LIMIT ?''',
        (six_hours_ago, limit)
    )
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_news_by_source_all_time(limit=10):
    """Kaynaklara göre tüm zamanların haber sayıları"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        '''SELECT source, COUNT(*) as count 
           FROM news 
           GROUP BY source 
           ORDER BY count DESC 
           LIMIT ?''',
        (limit,)
    )
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


# ============= NEW FUNCTIONS FOR ADVANCED DASHBOARD =============

def get_news_flow_rate(minutes=60):
    """
    Haber akış hızını hesapla
    
    Returns:
        {
            'news_per_minute': float,
            'news_per_hour': int,
            'total_in_period': int,
            'peak_minute': {'minute': str, 'count': int}
        }
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    time_ago = datetime.utcnow() - timedelta(minutes=minutes)
    
    MAX_FLOW_LIMIT = 50000 
    cursor.execute(
        'SELECT COUNT(*) as count FROM news WHERE COALESCE(pub_date, created_at) >= ? LIMIT ?',
        (time_ago, MAX_FLOW_LIMIT)
    )
    total = cursor.fetchone()['count']
    
    # News per minute breakdown
    cursor.execute(
        '''SELECT 
            strftime('%Y-%m-%d %H:%M', COALESCE(pub_date, created_at)) as minute,
            COUNT(*) as count
           FROM news 
           WHERE COALESCE(pub_date, created_at) >= ?
           GROUP BY minute
           ORDER BY count DESC
           LIMIT 1''',
        (time_ago,)
    )
    peak = cursor.fetchone()
    
    conn.close()
    
    return {
        'news_per_minute': round(total / minutes, 2) if minutes > 0 else 0,
        'news_per_hour': int((total / minutes) * 60) if minutes > 0 else 0,
        'total_in_period': total,
        'peak_minute': {
            'minute': dict(peak)['minute'] if peak else None,
            'count': dict(peak)['count'] if peak else 0
        }
    }


def get_hourly_distribution(hours=24):
    """
    Saat bazında haber dağılımı
    
    Returns:
        [{'hour': 'YYYY-MM-DD HH:00', 'count': int}, ...]
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    time_ago = datetime.utcnow() - timedelta(hours=hours)
    
    cursor.execute(
        '''SELECT 
            strftime('%Y-%m-%d %H:00', COALESCE(pub_date, created_at)) as hour,
            COUNT(*) as count
           FROM news 
           WHERE COALESCE(pub_date, created_at) >= ?
           GROUP BY hour
           ORDER BY hour ASC''',
        (time_ago,)
    )
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_word_frequencies(limit=50, hours=6):
    """
    En sık geçen kelimeleri çıkar
    
    Returns:
        [{'word': str, 'count': int}, ...]
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    time_ago = datetime.utcnow() - timedelta(hours=hours)
    
    cursor.execute(
        'SELECT title, description FROM news WHERE COALESCE(pub_date, created_at) >= ?',
        (time_ago,)
    )
    
    # Stopwords
    stopwords = {
        've', 'veya', 'ile', 'ama', 'fakat', 'ancak', 'için', 'gibi',
        'bir', 'bu', 'şu', 'o', 'ne', 'nasıl', 'neden', 'niçin',
        'mi', 'mı', 'mu', 'mü', 'de', 'da', 'ki', 'dı', 'di',
        'var', 'yok', 'olan', 'oldu', 'olacak', 'etti', 'ediyor',
        'den', 'dan', 'ten', 'tan', 'e', 'a', 'ye', 'ya', 'daha',
        'çok', 'az', 'her', 'tüm', 'bütün', 'bazı', 'ise', 'son',
        'http', 'https', 'com', 'www', 'href', 'target', 'blank', 'class'
    }
    
    word_list = []
    for row in cursor.fetchall():
        text = (row['title'] or '') + ' ' + (row['description'] or '')
        words = re.findall(r'\b\w+\b', text.lower())
        word_list.extend([w for w in words if w not in stopwords and len(w) > 2])
    
    counter = Counter(word_list)
    results = [{'word': word, 'count': count} for word, count in counter.most_common(limit)]
    
    conn.close()
    return results


def get_latest_news(limit=20):
    """
    En son eklenen haberleri getir
    
    Returns:
        [{'id', 'title', 'source', 'created_at', 'link'}, ...]
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        '''SELECT id, title, source, created_at, link, pub_date, image_url, description
           FROM news 
           ORDER BY created_at DESC 
           LIMIT ?''',
        (limit,)
    )
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_source_speed_metrics():
    """
    Kaynak başına hız ve güvenilirlik metrikleri
    
    Returns:
        [{'source': str, 'avg_per_hour': float, 'total': int, 'success_rate': float}, ...]
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Last 6 hours stats per source
    six_hours_ago = datetime.utcnow() - timedelta(hours=6)
    
    cursor.execute(
        '''SELECT 
            source,
            COUNT(*) as total,
            ROUND(COUNT(*) / 6.0, 2) as avg_per_hour
           FROM news
           WHERE COALESCE(pub_date, created_at) >= ?
           GROUP BY source
           ORDER BY avg_per_hour DESC''',
        (six_hours_ago,)
    )
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results




def get_comparison_stats():
    """
    Bugün ve Dün karşılaştırması (Yayınlanma zamanına göre)
    Today: Son 24 saat
    Yesterday: Önceki 24 saat (24-48 saat önce)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Zaman dilimleri (UTC)
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    prev_24h_start = now - timedelta(hours=48)
    prev_24h_end = last_24h
    
    # Sorgu: pub_date varsa onu kullan, yoksa created_at
    # Today stat
    cursor.execute('''
        SELECT COUNT(*) as count 
        FROM news 
        WHERE COALESCE(pub_date, created_at) >= ?
    ''', (last_24h,))
    today_count = cursor.fetchone()['count']
    
    # Yesterday stat
    cursor.execute('''
        SELECT COUNT(*) as count 
        FROM news 
        WHERE COALESCE(pub_date, created_at) >= ? 
          AND COALESCE(pub_date, created_at) < ?
    ''', (prev_24h_start, prev_24h_end))
    yesterday_count = cursor.fetchone()['count']
    
    conn.close()
    
    # Değişim oranı
    change = today_count - yesterday_count
    
    if yesterday_count > 0:
        change_percent = round((change / yesterday_count) * 100, 1)
    else:
        change_percent = 100 if today_count > 0 else 0
        
    return {
        'today': today_count,
        'yesterday': yesterday_count,
        'change': change,
        'change_percent': change_percent,
        'trending': 'up' if change > 0 else 'down' if change < 0 else 'same'
    }




def get_sentiment_distribution():
    """
    Basit keyword-based sentiment analizi
    
    Returns:
        {'positive': int, 'negative': int, 'neutral': int}
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    six_hours_ago = datetime.utcnow() - timedelta(hours=6)
    
    cursor.execute(
        'SELECT title, description FROM news WHERE COALESCE(pub_date, created_at) >= ?',
        (six_hours_ago,)
    )
    
    positive_words = {'başarı', 'kazandı', 'iyi', 'güzel', 'harika', 'mükemmel', 'zafer', 'galip', 'mutlu'}
    negative_words = {'kötü', 'kaybetti', 'kaza', 'ölüm', 'yaralı', 'tehlike', 'sorun', 'problem', 'yenilgi'}
    
    positive = 0
    negative = 0
    neutral = 0
    
    for row in cursor.fetchall():
        text = ((row['title'] or '') + ' ' + (row['description'] or '')).lower()
        
        has_positive = any(word in text for word in positive_words)
        has_negative = any(word in text for word in negative_words)
        
        if has_positive and not has_negative:
            positive += 1
        elif has_negative and not has_positive:
            negative += 1
        else:
            neutral += 1
    
    conn.close()
    return {'positive': positive, 'negative': negative, 'neutral': neutral}


def get_random_news_24h(limit=30):
    """Son 24 saatten rastgele haberler getir (Sanal Gazete için)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # SQLite'ta tarih karşılaştırması
    yesterday = datetime.utcnow() - timedelta(hours=24)
    
    # Daha fazla haber çek ve client-side filtreleme yap
    cursor.execute('''
        SELECT * FROM news 
        WHERE COALESCE(pub_date, created_at) >= ? 
        ORDER BY 
            CASE WHEN image_url IS NOT NULL AND image_url != '' THEN 0 ELSE 1 END,
            RANDOM() 
        LIMIT ?
    ''', (yesterday, limit * 2))  # 2x çek, filtrelemeden sonra yeterli kalır
    
    news = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Geçersiz başlıkları filtrele
    filtered_news = []
    for item in news:
        title = item.get('title', '')
        
        # URL gibi görünen başlıkları filtrele
        # Eğer başlık http ile başlıyorsa veya .com/.net gibi uzantılar içeriyorsa atla
        if title.startswith('http://') or title.startswith('https://'):
            continue
        if '.com' in title or '.net' in title or '.org' in title or '.tr' in title:
            continue
        
        # Çok kısa başlıkları atla (genellikle hatalı)
        if len(title) < 10:
            continue
            
        filtered_news.append(item)
        
        # İstenen sayıya ulaştık mı?
        if len(filtered_news) >= limit:
            break
    
    return filtered_news


def get_recent_news(hours=24, limit=500):
    """
    Son X saatin haberlerini getir (Clustering için)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    time_ago = datetime.utcnow() - timedelta(hours=hours)
    
    cursor.execute('''
        SELECT * FROM news 
        WHERE COALESCE(pub_date, created_at) >= ? 
        ORDER BY pub_date DESC
        LIMIT ?
    ''', (time_ago, limit))
    
    news = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return news
