"""
HaberMetrik - Ana Flask Uygulaması

Türk haber sitelerinden haber toplayan ve anahtar kelime araması yapan uygulama.
"""

import threading
import time
import signal
import sys
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify

from config import RSS_SOURCES, UPDATE_INTERVAL, SECRET_KEY
from database import (
    init_db, insert_many_news, verify_user, ensure_admin_exists,
    get_all_users, create_user, delete_user, get_user_by_id,
    get_news_count, delete_news_by_source, delete_news_by_age,
    get_random_news_24h, get_word_frequencies
)
from parsers import get_parser
from failed_sources import (
    log_failed_source, log_success_source, should_skip_source
)
from api.routes import api_bp
from auth import login_required, admin_required, get_current_user, is_admin

# Flask uygulaması
app = Flask(__name__)
app.secret_key = SECRET_KEY
app.register_blueprint(api_bp)

# Arka plan thread'lerini takip et
background_threads = []
stop_event = threading.Event()


def update_feed(source_key):
    """
    Belirli bir kaynağı güncelle

    Args:
        source_key: Kaynak anahtarı (hurriyet, ntv, vs.)
    """
    source_config = RSS_SOURCES.get(source_key, {})
    source_url = source_config.get('url', '')

    parser = get_parser(source_key)
    if not parser:
        print(f"[{source_key}] Parser bulunamadı")
        log_failed_source(source_key, source_url, 'no_parser', 'Parser bulunamadı')
        return

    while not stop_event.is_set():
        # Çok fazla ardışık hata varsa atla
        if should_skip_source(source_key, max_consecutive=10):
            print(f"[{source_key}] Çok fazla hata - geçici olarak atlanıyor")
            stop_event.wait(UPDATE_INTERVAL * 5)  # Daha uzun bekle
            continue

        try:
            items = parser.get_items()

            if items:
                inserted = insert_many_news(items)
                if inserted > 0:
                    print(f"[{source_key}] {inserted} yeni haber eklendi")
                # Başarılı - hata sayacını sıfırla
                log_success_source(source_key)
            else:
                # Veri gelmedi
                log_failed_source(source_key, source_url, 'no_data', 'Haber bulunamadı')

        except ConnectionError as e:
            log_failed_source(source_key, source_url, 'connection', str(e))
            print(f"[{source_key}] Bağlantı hatası: {e}")
        except Exception as e:
            error_msg = str(e)
            if 'timeout' in error_msg.lower():
                error_type = 'timeout'
            elif '404' in error_msg:
                error_type = 'http_404'
            elif '403' in error_msg:
                error_type = 'http_403'
            elif 'parse' in error_msg.lower() or 'xml' in error_msg.lower():
                error_type = 'parse_error'
            else:
                error_type = 'unknown'

            log_failed_source(source_key, source_url, error_type, error_msg)
            print(f"[{source_key}] Güncelleme hatası: {e}")

        # Bir sonraki güncellemeyi bekle
        stop_event.wait(UPDATE_INTERVAL)


def start_background_updates():
    """Tüm kaynaklar için arka plan güncelleme thread'lerini başlat"""
    print("Arka plan güncellemeleri başlatılıyor...")

    for source_key in RSS_SOURCES.keys():
        thread = threading.Thread(
            target=update_feed,
            args=(source_key,),
            name=f"update_{source_key}",
            daemon=True
        )
        thread.start()
        background_threads.append(thread)
        print(f"  - {source_key} thread başlatıldı")

    print(f"Toplam {len(background_threads)} güncelleme thread'i başlatıldı")


def stop_background_updates():
    """Arka plan güncellemelerini durdur"""
    print("\nArka plan güncellemeleri durduruluyor...")
    stop_event.set()

    for thread in background_threads:
        thread.join(timeout=2)

    print("Tüm thread'ler durduruldu")


def signal_handler(signum, frame):
    """SIGINT/SIGTERM için handler"""
    print("\nKapatma sinyali alındı...")
    stop_background_updates()
    sys.exit(0)


@app.before_request
def require_login():
    """Tüm isteklerde giriş kontrolü yap"""
    allowed_routes = ['login', 'static', 'api.trending_topics', 'api.search_grouped', 'api.live_feed']
    if request.endpoint and request.endpoint not in allowed_routes and 'user_id' not in session:
        return redirect(url_for('login'))

# ============ Kimlik Doğrulama Rotaları ============

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Giriş sayfası"""
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
        if user:
            return redirect(url_for('virtual_newspaper'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = verify_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']

            next_url = request.form.get('next') or request.args.get('next')
            if next_url:
                return redirect(next_url)

            return redirect(url_for('virtual_newspaper'))
        else:
            error = 'Kullanıcı adı veya şifre hatalı.'

    return render_template('login.html', error=error, next=request.args.get('next'))


@app.route('/logout')
def logout():
    """Çıkış"""
    session.clear()
    return redirect(url_for('login'))


# ============ User Dashboard ============

@app.route('/dashboard')
@admin_required
def dashboard():
    """Kullanıcı dashboard"""
    user = get_current_user()
    return render_template('user_dashboard.html', user=user)


# ============ Admin Paneli ============

@app.route('/admin')
@admin_required
def admin_panel():
    """Admin paneli"""
    user = get_current_user()
    users = get_all_users()
    news_count = get_news_count()
    return render_template('admin.html',
                           user=user,
                           users=users,
                           news_count=news_count,
                           sources=RSS_SOURCES)


@app.route('/admin/users', methods=['POST'])
@admin_required
def admin_add_user():
    """Yeni kullanıcı ekle"""
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    role = request.form.get('role', 'user')

    if not username or not password:
        flash('Kullanıcı adı ve şifre gerekli.', 'error')
        return redirect(url_for('admin_panel'))

    if len(password) < 6:
        flash('Şifre en az 6 karakter olmalı.', 'error')
        return redirect(url_for('admin_panel'))

    user_id = create_user(username, password, role)
    if user_id:
        flash(f'Kullanıcı "{username}" başarıyla oluşturuldu.', 'success')
    else:
        flash(f'Kullanıcı "{username}" zaten mevcut.', 'error')

    return redirect(url_for('admin_panel'))


@app.route('/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def admin_delete_user(user_id):
    """Kullanıcı sil"""
    # Kendini silemesin
    if user_id == session.get('user_id'):
        return jsonify({'success': False, 'message': 'Kendinizi silemezsiniz.'}), 400

    # Admin sayısını kontrol et
    user = get_user_by_id(user_id)
    if user and user['role'] == 'admin':
        admins = [u for u in get_all_users() if u['role'] == 'admin']
        if len(admins) <= 1:
            return jsonify({'success': False, 'message': 'Son admin silinemez.'}), 400

    if delete_user(user_id):
        return jsonify({'success': True, 'message': 'Kullanıcı silindi.'})
    return jsonify({'success': False, 'message': 'Kullanıcı bulunamadı.'}), 404


@app.route('/admin/news/delete', methods=['POST'])
@admin_required
def admin_delete_news():
    """Haber sil (rate limited)"""
    delete_type = request.form.get('type', 'source')
    limit = min(int(request.form.get('limit', 100)), 100)  # Max 100

    if delete_type == 'source':
        source = request.form.get('source', '')
        if not source:
            flash('Kaynak seçmelisiniz.', 'error')
            return redirect(url_for('admin_panel'))
        deleted = delete_news_by_source(source, limit)
        flash(f'{deleted} haber silindi (kaynak: {source}).', 'success')

    elif delete_type == 'age':
        hours = int(request.form.get('hours', 24))
        deleted = delete_news_by_age(hours, limit)
        flash(f'{deleted} haber silindi ({hours} saatten eski).', 'success')

    return redirect(url_for('admin_panel'))


# ============ Ana Sayfalar (Login Required) ============

@app.route('/')
@login_required
def index():
    """Ana sayfa - Arama arayüzü"""
    user = get_current_user()
    return render_template('index.html', user=user)


@app.route('/search-grouped')
@login_required
def search_grouped_page():
    """Arama bazlı gruplandırma arayüzü"""
    user = get_current_user()
    trending_topics = get_word_frequencies(limit=10, hours=24)
    return render_template('search_grouped.html', user=user, trending_topics=trending_topics)





@app.route('/sanal-gazete')
@login_required
def virtual_newspaper():
    """Sanal Gazetem - Gündemdeki (Gruplanmış) Haberler"""
    from clustering import get_clusterer
    from database import get_recent_news
    
    user = get_current_user()
    
    # 1. Son 24 saatin haberlerini çek
    raw_news = get_recent_news(hours=24, limit=1000)
    
    # 2. Kümeleme yap
    clusterer = get_clusterer()
    # eps küçültüldü (0.40 -> 0.25) daha hassas gruplama için
    clusters = clusterer.cluster_news(raw_news, eps=0.25, min_samples=2)
    
    # 3. Her kümeden en iyi temsili haberi seç
    news_items = []
    seen_titles = set()
    
    for cluster in clusters.values():
        cluster_news = cluster['news']
        if not cluster_news:
            continue
            
        # ---------------------------------------------------------
        # HYBRID SELECTION STRATEGY FOR VARIETY
        # ---------------------------------------------------------
        
        # 1. Categorize candidates
        rich_candidates = []      # Image + Long Description
        fallback_candidates = []  # Others (Text only, short desc, etc.)
        
        for n in cluster_news:
            has_image = bool(n.get('image_url'))
            desc_len = len(n.get('description', '') or '')
            
            if has_image and desc_len > 20:
                rich_candidates.append(n)
            elif desc_len > 10:
                # Only accept fallbacks if they have at least some description
                # This prevents "empty description" cards
                fallback_candidates.append(n)
                
        # 2. Sort both lists by quality
        # Sort key: Image (1/0) -> Desc Length -> Date
        def sort_key(x):
            return (
                1 if x.get('image_url') else 0,
                len(x.get('description', '') or ''),
                x.get('pub_date', '')
            )
            
        rich_candidates.sort(key=sort_key, reverse=True)
        fallback_candidates.sort(key=sort_key, reverse=True)
        
        # 3. Determine Selection Pool (Weighted for Visuals)
        import random
        pool = []
        
        # Strategy: Prioritize Visuals but allow Variety
        if rich_candidates:
            # If we have plenty of rich news (>=3), stick to them for max quality
            if len(rich_candidates) >= 3:
                pool = rich_candidates[:10]
            else:
                # If rich news is scarce (1-2 items), we mix in text-only for variety
                # BUT we weight the rich items heavily so images appear most of the time
                
                # Add rich candidates multiple times (Weight: 5x)
                # This ensures ~60-70% chance of seeing an image
                for rc in rich_candidates:
                    pool.extend([rc] * 5)
                    
                # Add a few high-quality fallbacks (Limit to top 4)
                pool.extend(fallback_candidates[:4])
        else:
            # No images at all? Use best text-only news
            pool = fallback_candidates[:5]
            
        if not pool:
            continue
            
        # 4. Pick One Randomly
        best_news = random.choice(pool)
        
        if best_news['title'] not in seen_titles:
            # Add cluster metadata
            best_news['cluster_size'] = cluster['count']
            best_news['cluster_title'] = cluster['title']
            
            news_items.append(best_news)
            seen_titles.add(best_news['title'])
    
    # Haberleri küme büyüklüğüne göre sırala (en çok konuşulan en üstte)
    news_items.sort(key=lambda x: x.get('cluster_size', 0), reverse=True)
    
    return render_template('virtual_newspaper.html', user=user, news=news_items)


@app.route('/canli-akis')
@login_required
def live_feed():
    """Canlı Akış - Anlık haberler"""
    user = get_current_user()
    return render_template('live_feed.html', user=user)


@app.route('/depremler')
@login_required
def earthquakes():
    """Son Depremler - Kandilli ve AFAD verileri"""
    from earthquake_service import get_earthquakes
    user = get_current_user()
    earthquake_data = get_earthquakes()
    return render_template('earthquakes.html', user=user, earthquakes=earthquake_data)


if __name__ == '__main__':
    # Sinyal handler'larını ayarla
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Veritabanını başlat
    print("Veritabanı başlatılıyor...")
    init_db()

    # Varsayılan admin kullanıcısını oluştur
    ensure_admin_exists()

    # Arka plan güncellemelerini başlat
    start_background_updates()

    # Flask uygulamasını başlat
    print("\nFlask uygulaması başlatılıyor...")
    print("API: http://localhost:5001")
    print("Arama: http://localhost:5001/api/search?q=keyword")
    print("\nÇıkmak için Ctrl+C\n")

    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
