"""
HaberMetrik - API Routes
"""

from flask import Blueprint, request, jsonify
from database import search_news
from config import SEARCH_LIMIT

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/search', methods=['GET'])
def search():
    """Haber arama API"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'error': 'Arama terimi gerekli'}), 400
    
    limit = min(int(request.args.get('limit', SEARCH_LIMIT)), 100)
    
    results = search_news(query, limit)
    
    return jsonify({
        'query': query,
        'count': len(results),
        'results': results
    })


@api_bp.route('/search-grouped', methods=['GET'])
def search_grouped():
    """
    Gruplama ile haber arama
    
    GET /api/search-grouped?q=deprem&eps=0.35&min_samples=2
    
    Query Params:
        q: Arama terimi
        eps: DBSCAN epsilon (0-1, düşük = sıkı gruplama)
        min_samples: Minimum haber sayısı
    
    Returns:
        {
            "query": "deprem",
            "total": 45,
            "cluster_count": 5,
            "clusters": [...]
        }
    """
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'error': 'Arama terimi gerekli'}), 400
    
    # Parametreler
    eps = float(request.args.get('eps', 0.35))
    min_samples = int(request.args.get('min_samples', 2))
    limit = min(int(request.args.get('limit', 100)), 200)
    
    # Arama
    results = search_news(query, limit)
    
    if not results:
        return jsonify({
            'query': query,
            'total': 0,
            'cluster_count': 0,
            'clusters': []
        })
    
    # Clustering
    try:
        from clustering import get_clusterer
        clusterer = get_clusterer()
        clusters_dict = clusterer.cluster_news(results, eps=eps, min_samples=min_samples)
        
        # ID'leri string'e çevir (JSON serialization için)
        for cluster in clusters_dict.values():
            cluster['id'] = str(cluster['id'])
        
        # Sıralı liste olarak dönüştür
        clusters = sorted(
            clusters_dict.values(),
            key=lambda x: x['count'],
            reverse=True
        )
        
        return jsonify({
            'query': query,
            'total': len(results),
            'cluster_count': len(clusters),
            'clusters': clusters
        })
    except Exception as e:
        import traceback
        print(f"Clustering hatası: {e}")
        print(traceback.format_exc())
        return jsonify({
            'query': query,
            'total': len(results),
            'cluster_count': 0,
            'clusters': [],
            'error': f'Clustering failed: {str(e)}'
        })


@api_bp.route('/dashboard-stats', methods=['GET'])
def dashboard_stats():
    """Dashboard istatistikleri"""
    from failed_sources import get_all_sources_status as get_source_stats
    from database import (
        get_today_news_count, get_news_by_source_today,
        get_total_news_count, get_news_by_source_all_time
    )
    
    # Kaynak limit parametresini al (default 50, max 10000)
    limit_sources = min(int(request.args.get('limit_sources', 50)), 10000)
    
    # Kaynak durumları
    sources_status = get_source_stats()
    
    # Bugünün istatistikleri
    today_count = get_today_news_count()
    today_by_source = get_news_by_source_today(limit=limit_sources)
    
    # Toplam haberler
    total_count = get_total_news_count()
    all_time_by_source = get_news_by_source_all_time(limit=limit_sources)
    
    return jsonify({
        'sources': {
            'total': sources_status['total'],
            'working': len(sources_status['working']),
            'failed': len(sources_status['failed']),
            'working_list': sources_status['working'],
            'failed_list': sources_status['failed']
        },
        'today': {
            'count': today_count,
            'by_source': today_by_source
        },
        'all_time': {
            'count': total_count,
            'by_source': all_time_by_source
        }
    })


@api_bp.route('/trending-topics', methods=['GET'])
def trending_topics():
    """
    Otomatik kümeleme ile trending topics
    
    GET /api/trending-topics
    
    Returns:
        {
            "clusters": [...],
            "total_news": 100
        }
    """
    from database import get_latest_news
    
    # Son 100 haberi al
    limit = min(int(request.args.get('limit', 100)), 200)
    recent_news = get_latest_news(limit=limit)
    
    if len(recent_news) < 5:
        return jsonify({
            'clusters': [],
            'total_news': len(recent_news),
            'message': 'Yeterli haber yok'
        })
    
    # Clustering yap
    try:
        from clustering import get_clusterer
        clusterer = get_clusterer()
        clusters = clusterer.cluster_news(recent_news, eps=0.32, min_samples=2)
        
        # En büyük 5 kümeyi al
        sorted_clusters = sorted(
            clusters.values(),
            key=lambda x: x['count'],
            reverse=True
        )[:5]
        
        # Her küme için tüm haberleri 'articles' olarak gönder ve main_topic/keywords ekle
        for cluster in sorted_clusters:
            # ID'yi string'e çevir (JSON serialization için)
            cluster['id'] = str(cluster['id'])
            # 'news' anahtarını 'articles' olarak yeniden adlandır
            cluster['articles'] = cluster['news']
            del cluster['news']
            
            # Frontend'in beklediği alanları ekle
            cluster['main_topic'] = cluster['title']  # main_topic = title
            
            # Keywords: title'dan kelimeleri ayır
            title_words = cluster['title'].split()
            cluster['keywords'] = title_words[:3] if len(title_words) >= 3 else title_words
        
        return jsonify({
            'clusters': sorted_clusters,
            'total_news': len(recent_news)
        })
    except Exception as e:
        import traceback
        print(f"Clustering hatası: {e}")
        print(traceback.format_exc())
        return jsonify({
            'clusters': [],
            'total_news': len(recent_news),
            'error': f'Clustering failed: {str(e)}'
        })


# ============= NEW ADVANCED DASHBOARD ENDPOINTS =============

@api_bp.route('/news-flow-rate', methods=['GET'])
def news_flow_rate():
    """Haber akış hızı metrikleri"""
    from database import get_news_flow_rate
    
    minutes = min(int(request.args.get('minutes', 60)), 1440)  # Max 24 hours
    result = get_news_flow_rate(minutes=minutes)
    
    return jsonify(result)


@api_bp.route('/time-series', methods=['GET'])
def time_series():
    """24 saatlik zaman serisi grafiği"""
    from database import get_hourly_distribution
    
    hours = min(int(request.args.get('hours', 24)), 168)  # Max 7 days
    result = get_hourly_distribution(hours=hours)
    
    return jsonify({
        'hours': hours,
        'data': result
    })


@api_bp.route('/word-cloud', methods=['GET'])
def word_cloud():
    """En sık geçen kelimeler"""
    from database import get_word_frequencies
    
    limit = min(int(request.args.get('limit', 50)), 100)
    hours = min(int(request.args.get('hours', 6)), 48)
    
    result = get_word_frequencies(limit=limit, hours=hours)
    
    return jsonify({
        'words': result,
        'total': len(result)
    })


@api_bp.route('/live-feed', methods=['GET'])
def live_feed():
    """Canlı haber akışı - Son 15 dakika (Strict)"""
    from database import get_latest_news
    from datetime import datetime, timedelta
    import pytz
    
    limit = min(int(request.args.get('limit', 50)), 100)
    
    # Fetch raw news - Prefer quantity to find recent items
    raw_limit = 500
    raw_news = get_latest_news(limit=raw_limit)
    
    # Timezone setup
    turkey_tz = pytz.timezone('Europe/Istanbul')
    now_turkey = datetime.now(turkey_tz)
    
    filtered_news = []
    
    for item in raw_news:
        # Skip if no title
        if not item.get('title'):
            continue
            
        try:
            # Parse date (Prioritize pub_date, fall back to created_at)
            date_str = item.get('pub_date') or item.get('created_at')
            if not date_str:
                continue
                
            # Handle string formats (SQLite default often 'YYYY-MM-DD HH:MM:SS')
            if isinstance(date_str, str):
                # Try standard format first
                try:
                    dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    # Try ISO format if needed
                    try:
                        dt = datetime.fromisoformat(date_str.replace('Z', ''))
                    except ValueError:
                        continue
            else:
                # Already datetime?
                dt = date_str
                
            # Assume database dates are naive UTC (common in this app context)
            if dt.tzinfo is None:
                dt = pytz.utc.localize(dt)
            
            # Convert to Turkey time for comparison
            dt_turkey = dt.astimezone(turkey_tz)
            
            # Calculate difference
            delta = now_turkey - dt_turkey
            total_seconds = delta.total_seconds()
            
            # STRICT FILTER: Max 15 minutes (900 seconds)
            # User asked for "max 10 dk", we give 15 as buffer/safety.
            if total_seconds > 900: 
                continue
            
            # Format time string
            if total_seconds < 60:
                time_ago_str = "Az önce"
            else:
                mins = int(total_seconds // 60)
                time_ago_str = f"{mins} dakika önce"
                
            item['time_ago'] = time_ago_str
            filtered_news.append(item)
            
        except Exception as e:
            # If date parsing fails, skip item to be safe
            continue
            
    # Apply requested limit to our strictly filtered list
    results = filtered_news[:limit]
    
    return jsonify({
        'news': results,
        'count': len(results)
    })


@api_bp.route('/source-performance', methods=['GET'])
def source_performance():
    """Kaynak performans metrikleri"""
    from database import get_source_speed_metrics
    
    results = get_source_speed_metrics()
    
    return jsonify({
        'sources': results,
        'total': len(results)
    })


@api_bp.route('/comparison', methods=['GET'])
def comparison():
    """Bugün (Son 24s) vs Dün (Önceki 24s) karşılaştırma"""
    from database import get_comparison_stats
    
    stats = get_comparison_stats()
    
    return jsonify(stats)


@api_bp.route('/sentiment', methods=['GET'])
def sentiment():
    """Duygu analizi dağılımı"""
    from database import get_sentiment_distribution
    
    result = get_sentiment_distribution()
    total = sum(result.values())
    
    # Add percentages
    result['total'] = total
    if total > 0:
        result['positive_percent'] = round((result['positive'] / total) * 100, 1)
        result['negative_percent'] = round((result['negative'] / total) * 100, 1)
        result['neutral_percent'] = round((result['neutral'] / total) * 100, 1)
    
    return jsonify(result)
