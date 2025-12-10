"""
HaberMetrik - Yapılandırma Dosyası
"""

import os

# Veritabanı ayarları
DATABASE_PATH = 'habermetre.db'

# Flask session için gizli anahtar
SECRET_KEY = os.environ.get('SECRET_KEY', 'habermetrik-secret-key-change-in-production-2024')

# RSS/Sitemap güncelleme aralığı (saniye)
UPDATE_INTERVAL = 30

# HTTP istek ayarları
REQUEST_TIMEOUT = 15
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Habertürk için retry ayarları
MAX_RETRIES = 3
RETRY_DELAY = 5

# Tekilleştirme eşiği
SIMILARITY_THRESHOLD = 0.70

# Arama sonuç limiti
SEARCH_LIMIT = 50

# GNews ayarları
GNEWS_LANGUAGE = 'tr'
GNEWS_COUNTRY = 'TR'
GNEWS_MAX_RESULTS = 20

# Haber kaynakları - ESKİ KAYNAKLAR (mevcut parser'lar)
RSS_SOURCES = {
    'hurriyet': {
        'name': 'Hürriyet',
        'url': 'https://www.hurriyet.com.tr/rss/anasayfa',
        'type': 'rss',
        'lang': 'tr'
    },
    'milliyet': {
        'name': 'Milliyet',
        'url': 'https://www.milliyet.com.tr/milliyet-sm/haber',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'ntv': {
        'name': 'NTV',
        'url': 'https://www.ntv.com.tr/sitemaps/news-sitemap.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'fanatik': {
        'name': 'Fanatik',
        'url': 'https://www.fanatik.com.tr/fanatik-sp/haber',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'vatan': {
        'name': 'Vatan',
        'url': 'https://www.gazetevatan.com/vatan-vt/haber',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'mynet': {
        'name': 'Mynet',
        'url': 'https://www.mynet.com/sitemaps/news/GoogleNews.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'haberturk': {
        'name': 'Habertürk',
        'url': 'https://www.haberturk.com/sitemap_google_news.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'cnnturk': {
        'name': 'CNN Türk',
        'url': 'https://www.cnnturk.com/feed/rss/news',
        'type': 'rss',
        'lang': 'tr'
    },
    'sozcu': {
        'name': 'Sözcü',
        'url': 'https://www.sozcu.com.tr/feeds-haberler',
        'type': 'rss',
        'lang': 'tr'
    },
    'takvim': {
        'name': 'Takvim',
        'url': 'https://www.takvim.com.tr/sitemap/news.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },

    # ============================================================================
    # YENİ KAYNAKLAR - siteler.txt'den test edilip eklendi
    # ============================================================================

    # RSS Kaynakları
    'aksam': {
        'name': 'Akşam',
        'url': 'https://www.aksam.com.tr/rss/rss.asp',
        'type': 'rss',
        'lang': 'tr'
    },
    't24': {
        'name': 'T24',
        'url': 'https://t24.com.tr/rss',
        'type': 'rss',
        'lang': 'tr'
    },

    # Google News Sitemap Kaynakları
    'bianet': {
        'name': 'Bianet',
        'url': 'https://bianet.org/sitemap/haberler',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'bloomberght': {
        'name': 'BloombergHT',
        'url': 'https://www.bloomberght.com/sitemap_google_news.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'cumhuriyet': {
        'name': 'Cumhuriyet',
        'url': 'https://www.cumhuriyet.com.tr/sitemaps/news.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'diken': {
        'name': 'Diken',
        'url': 'https://www.diken.com.tr/news-sitemap.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'dirilispostasi': {
        'name': 'Diriliş Postası',
        'url': 'https://www.dirilispostasi.com/sitemap-news.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'dunya': {
        'name': 'Dünya',
        'url': 'https://www.dunya.com/export/sitemap',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'ensonhaber': {
        'name': 'Ensonhaber',
        'url': 'https://www.ensonhaber.com/sitemaps/google-news.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'evrensel': {
        'name': 'Evrensel',
        'url': 'https://www.evrensel.net/sitemap-news.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'f5haber': {
        'name': 'F5 Haber',
        'url': 'https://www.f5haber.com/export/sitemap',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'fotomac': {
        'name': 'Fotomaç',
        'url': 'https://www.fotomac.com.tr/sitemap/news.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'haber7': {
        'name': 'Haber7',
        'url': 'https://www.haber7.com/sitemaps/haber7/news-sitemap.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'haberler': {
        'name': 'Haberler.com',
        'url': 'https://www.haberler.com/sitemap_google_news.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'habervaktim': {
        'name': 'Haber Vaktim',
        'url': 'https://www.habervaktim.com/sitemap.xsd',
        'type': 'sitemap_index',
        'lang': 'tr'
    },
    'habervitrini': {
        'name': 'Haber Vitrini',
        'url': 'https://www.habervitrini.com/sitemap-google-news.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'haberx': {
        'name': 'HaberX',
        'url': 'https://www.haberx.com/wp-sitemap.xml',
        'type': 'sitemap_index',
        'lang': 'tr'
    },
    'hurhaber': {
        'name': 'Hür Haber',
        'url': 'https://www.hurhaber.com/static/sitemap/sitemap.xml',
        'type': 'sitemap_index',
        'lang': 'tr'
    },
    'internethaber': {
        'name': 'İnternet Haber',
        'url': 'https://www.internethaber.com/googlenews.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'karar': {
        'name': 'Karar',
        'url': 'https://www.karar.com/sitemap-news-01.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'medyascope': {
        'name': 'Medyascope',
        'url': 'https://medyascope.tv/news-sitemap.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'memurlar': {
        'name': 'Memurlar.net',
        'url': 'https://www.memurlar.net/sitemap-news.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'milatgazetesi': {
        'name': 'Milat Gazetesi',
        'url': 'https://www.milatgazetesi.com/sitemap-news.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'milligazete': {
        'name': 'Milli Gazete',
        'url': 'https://www.milligazete.com.tr/sitemap-news.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'neoldu': {
        'name': 'Neoldu',
        'url': 'https://www.neoldu.com.tr/sitemap-news-01.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'ntvspor': {
        'name': 'NTV Spor',
        'url': 'https://www.ntvspor.net/news-sitemap',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'odatv': {
        'name': 'Oda TV',
        'url': 'https://www.odatv.com/sitemap.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'onedio': {
        'name': 'Onedio',
        'url': 'https://onedio.com/siteMapNews.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'posta': {
        'name': 'Posta',
        'url': 'https://www.posta.com.tr/posta-sp/haber',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'sabah': {
        'name': 'Sabah',
        'url': 'https://www.sabah.com.tr/sitemap/news.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'sondakika': {
        'name': 'Sondakika.com',
        'url': 'https://www.sondakika.com/sitemaps/sitemap_google_news.aspx',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'star': {
        'name': 'Star',
        'url': 'https://www.star.com.tr/sitemap-news.asp',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'superhaber': {
        'name': 'Süper Haber',
        'url': 'https://www.superhaber.com/google-news.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'tgrthaber': {
        'name': 'TGRT Haber',
        'url': 'https://www.tgrthaber.com/sitemap/google-news-sitemap',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'timeturk': {
        'name': 'Timetürk',
        'url': 'https://www.timeturk.com/timenews.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'trthaber': {
        'name': 'TRT Haber',
        'url': 'https://www.trthaber.com/sitemap_haber.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'turkiyegazetesi': {
        'name': 'Türkiye Gazetesi',
        'url': 'https://www.turkiyegazetesi.com.tr/sitemap/google-news-sitemap',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'turktime': {
        'name': 'Turktime',
        'url': 'https://www.turktime.com/news.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'tv100': {
        'name': 'TV100',
        'url': 'https://www.tv100.com/export/newsmap',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'veryansintv': {
        'name': 'Veryansın TV',
        'url': 'https://www.veryansintv.com/news-sitemap.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'yeniakit': {
        'name': 'Yeni Akit',
        'url': 'https://www.yeniakit.com.tr/sitemap_google_news.php',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'yenisafak': {
        'name': 'Yeni Şafak',
        'url': 'https://www.yenisafak.com/sitemap?contenttypes=news&contenttypes=official-announcement&name=standart&take=200',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'gazeteduvar': {
        'name': 'Gazete Duvar',
        'url': 'https://www.gazeteduvar.com.tr/export/sitemap',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'haberglobal': {
        'name': 'Haber Global',
        'url': 'https://haberglobal.com/sitemap/sitemap_google_news.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'halktv': {
        'name': 'Halk TV',
        'url': 'https://halktv.com.tr/sitemap-google-news',
        'type': 'sitemap',
        'lang': 'tr'
    },

    # Yerel/Bölgesel Haber Kaynakları
    'antalyahaber': {
        'name': 'Antalya Haber',
        'url': 'https://www.antalyahaber.net/sitemap-news.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'kayserihaber': {
        'name': 'Kayseri Haber',
        'url': 'https://kayserihaber.com.tr/sitemap-news.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'mersinhaber': {
        'name': 'Mersin Haber',
        'url': 'https://www.mersinhaber.com/sitemap/news',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'gaziantephaberler': {
        'name': 'Gaziantep Haberler',
        'url': 'https://www.gaziantephaberler.com/sitemap.xml',
        'type': 'sitemap_index',
        'lang': 'tr'
    },
    'vansesigazetesi': {
        'name': 'Van Sesi Gazetesi',
        'url': 'https://www.vansesigazetesi.com/sitemap_google_news.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },

    # Diğer Kaynaklar
    'nefes': {
        'name': 'Nefes',
        'url': 'https://www.nefes.com.tr/export/newsmap',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'birgun': {
        'name': 'Birgün',
        'url': 'https://www.birgun.net/sitemap/haberler',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'kamudanhaber': {
        'name': 'Kamudan Haber',
        'url': 'https://www.kamudanhaber.net/sitemap-news.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'airporthaber': {
        'name': 'Airport Haber',
        'url': 'https://www.airporthaber2.com/sitemap.news.php',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'gzt': {
        'name': 'GZT',
        'url': 'https://www.gzt.com/rss?xml=newssitemap',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'mansethaber': {
        'name': 'Manşet Haber',
        'url': 'https://mansethaber.com/sitemap-news.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'gazeteoksijen': {
        'name': 'Gazete Oksijen',
        'url': 'https://gazeteoksijen.com/export/sitemap',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'saraymedya': {
        'name': 'Saray Medya',
        'url': 'https://www.saraymedya.com/sitemap/',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'habertS': {
        'name': 'HaberTS',
        'url': 'https://www.haberts.com/sitemap.xml',
        'type': 'sitemap_index',
        'lang': 'tr'
    },
    
    # Alternatif Sitemap URL'leri
    'internethaber_alt': {
        'name': 'İnternet Haber (Alt)',
        'url': 'https://www.internethaber.com/googlesitemap.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'gazeteduvar_alt': {
        'name': 'Gazete Duvar (Newsmap)',
        'url': 'https://www.gazeteduvar.com.tr/export/newsmap',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'yenisafak_alt': {
        'name': 'Yeni Şafak (Genişletilmiş)',
        'url': 'https://www.yenisafak.com/sitemap?contenttypes=news&contenttypes=official-announcement&name=mobile&take=500',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'hurhaber_alt': {
        'name': 'Hür Haber (Güncel)',
        'url': 'https://www.hurhaber.com/static/sitemap/page_news_2025-12_1.xml',
        'type': 'sitemap',
        'lang': 'tr'
    },
    'sozcu_alt': {
        'name': 'Sözcü (Gündem)',
        'url': 'https://www.sozcu.com.tr/feeds-rss-category-gundem',
        'type': 'rss',
        'lang': 'tr'
    },
}

# XML Namespace tanımları
XML_NAMESPACES = {
    'news': 'http://www.google.com/schemas/sitemap-news/0.9',
    '': 'http://www.sitemaps.org/schemas/sitemap/0.9',
    'image': 'http://www.google.com/schemas/sitemap-image/1.1'
}
