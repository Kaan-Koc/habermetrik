"""
HaberMetrik - RSS/Sitemap Parser Modülü
"""

import requests
import xml.etree.ElementTree as ET
import re
from datetime import datetime, timedelta, timezone
from config import REQUEST_TIMEOUT, REQUEST_HEADERS, XML_NAMESPACES


class BaseParser:
    """Temel parser sınıfı"""
    
    def __init__(self, source_key, url):
        self.source_key = source_key
        self.url = url
    
    def get_items(self):
        """Haberleri getir"""
        raise NotImplementedError


import email.utils
import urllib.parse

def extract_title_from_url(url):
    """
    URL'den okunabilir başlık çıkar
    Örnek: 'https://site.com/gundem-haberleri/sehit-polis-memuru-albayrak-a-veda-490601'
         -> 'Şehit Polis Memuru Albayrak A Veda'
    """
    if not url:
        return url
    
    try:
        # URL'den path'i al
        parsed = urllib.parse.urlparse(url)
        path = parsed.path
        
        # Son segmenti al (genellikle haber başlığını içerir)
        segments = path.strip('/').split('/')
        if not segments:
            return url
        
        # Son segment genellikle haber slug'ıdır
        slug = segments[-1]
        
        # Dosya uzantılarını temizle
        slug = slug.split('.')[0]
        
        # Sayıları ve ID'leri temizle (sonunda olan)
        # Örnek: "baslik-123456" -> "baslik"
        parts = slug.split('-')
        cleaned_parts = []
        for part in parts:
            # Sadece rakamlardan oluşan parçaları atla (ID'ler genellikle sondadır)
            if not part.isdigit():
                cleaned_parts.append(part)
        
        if not cleaned_parts:
            return url
        
        # Kelimeleri birleştir ve her kelimenin ilk harfini büyüt
        title = ' '.join(cleaned_parts)
        
        # Türkçe karakter dönüşümleri için basit bir yaklaşım
        title = title.replace('_', ' ')
        
        # Her kelimenin ilk harfini büyük yap
        title = ' '.join(word.capitalize() for word in title.split())
        
        return title
    except Exception as e:
        # Hata durumunda orijinal URL'i döndür
        return url

def parse_date(date_str):
    """
    Farklı formatlardaki tarih stringlerini YYYY-MM-DD HH:MM:SS formatına çevir
    Timezone bilgisi varsa UTC'ye çevirir.
    """
    if not date_str:
        return None
        
    try:
        # 1. RSS Formatı (RFC 822) - örn: Tue, 09 Dec 2025 12:00:00 GMT  
        parsed = email.utils.parsedate_to_datetime(date_str)
        if parsed:
            # Eğer timezone bilgisi varsa, UTC'ye çevir
            if parsed.tzinfo is not None:
                utc_time = parsed.astimezone(timezone.utc)
                return utc_time.strftime('%Y-%m-%d %H:%M:%S')
            else:
                # Timezone yoksa olduğu gibi kullan (zaten UTC kabul edilir)
                return parsed.strftime('%Y-%m-%d %H:%M:%S')
    except:
        pass
        
    try:
        # 2. ISO 8601 / Sitemap Formatı - örn: 2025-12-09T12:00:00+03:00
        clean_str = date_str.replace('Z', '+00:00')
        parsed = datetime.fromisoformat(clean_str)
        
        # Eğer timezone bilgisi varsa, UTC'ye çevir
        if parsed.tzinfo is not None:
            utc_time = parsed.astimezone(timezone.utc)
            return utc_time.strftime('%Y-%m-%d %H:%M:%S')
        else:
            # Timezone yoksa olduğu gibi kullan (zaten UTC kabul edilir)
            return parsed.strftime('%Y-%m-%d %H:%M:%S')
    except:
        pass
        
    return None


class RSSParser(BaseParser):
    """RSS feed parser"""
    
    def get_items(self):
        try:
            response = requests.get(self.url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            items = []
            
            # Namespace map for finding elements with namespaces like dc:date
            namespaces = {
                'dc': 'http://purl.org/dc/elements/1.1/',
                'content': 'http://purl.org/rss/1.0/modules/content/',
                'media': 'http://search.yahoo.com/mrss/'
            }
            
            for item in root.findall('.//item'):
                title = item.find('title')
                link = item.find('link')
                description = item.find('description')
                
                # pubDate (Standard) or dc:date (Dublin Core)
                pub_date_elem = item.find('pubDate')
                if pub_date_elem is None:
                    pub_date_elem = item.find('dc:date', namespaces)
                
                pub_date_str = pub_date_elem.text if pub_date_elem is not None else None
                formatted_date = parse_date(pub_date_str)
                
                # Image extraction
                image_url = None
                
                # 1. Try media:content
                media_content = item.find('media:content', namespaces)
                if media_content is not None:
                    image_url = media_content.get('url')
                
                # 2. Try media:thumbnail
                if not image_url:
                    media_thumb = item.find('media:thumbnail', namespaces)
                    if media_thumb is not None:
                        image_url = media_thumb.get('url')
                
                # 3. Try enclosure
                if not image_url:
                    enclosure = item.find('enclosure')
                    if enclosure is not None and enclosure.get('type', '').startswith('image'):
                        image_url = enclosure.get('url')
                
                # 4. Try regex in description
                if not image_url and description is not None and description.text:
                    img_match = re.search(r'<img.*?src=["\'](.*?)["\']', description.text)
                    if img_match:
                        image_url = img_match.group(1)

                if title is not None and link is not None:
                    items.append({
                        'title': title.text or '',
                        'link': link.text or '',
                        'description': description.text if description is not None else '',
                        'source': self.source_key,
                        'pub_date': formatted_date,
                        'image_url': image_url
                    })
            
            return items
        except Exception as e:
            print(f"[{self.source_key}] RSS parse error: {e}")
            return []


class SitemapParser(BaseParser):
    """Sitemap XML parser"""
    
    def get_items(self):
        try:
            response = requests.get(self.url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            items = []
            
            # Google News Sitemap formatı
            for url_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                loc = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                news = url_elem.find('{http://www.google.com/schemas/sitemap-news/0.9}news')
                
                if loc is not None and news is not None:
                    title_elem = news.find('{http://www.google.com/schemas/sitemap-news/0.9}title')
                    pub_date_elem = news.find('{http://www.google.com/schemas/sitemap-news/0.9}publication_date')
                    
                    if title_elem is not None:
                        formatted_date = parse_date(pub_date_elem.text) if pub_date_elem is not None else None
                        
                        items.append({
                            'title': title_elem.text or '',
                            'link': loc.text or '',
                            'description': '',
                            'source': self.source_key,
                            'pub_date': formatted_date
                        })
            
            # Basit sitemap formatı
            if not items:
                for url_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                    loc = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                    if loc is not None:
                        # lastmod could be used as pub_date
                        lastmod = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod')
                        formatted_date = parse_date(lastmod.text) if lastmod is not None else None
                        
                        # URL'den başlık çıkar
                        url_text = loc.text or ''
                        extracted_title = extract_title_from_url(url_text)
                        
                        items.append({
                            'title': extracted_title,
                            'link': url_text,
                            'description': '',
                            'source': self.source_key,
                            'pub_date': formatted_date
                        })
            
            return items
        except Exception as e:
            print(f"[{self.source_key}] Sitemap parse error: {e}")
            return []


class SitemapIndexParser(BaseParser):
    """Sitemap Index parser - birden fazla sitemap içeren ana dosya"""
    
    def get_items(self):
        try:
            response = requests.get(self.url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            all_items = []
            
            # Sitemap index içindeki tüm sitemap'leri bul
            for sitemap in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap'):
                loc = sitemap.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                if loc is not None:
                    # Her bir sitemap'i parse et
                    parser = SitemapParser(self.source_key, loc.text)
                    items = parser.get_items()
                    all_items.extend(items)
                    
                    # İlk 100 haber yeterli
                    if len(all_items) >= 100:
                        break
            
            return all_items[:100]
        except Exception as e:
            print(f"[{self.source_key}] Sitemap index parse error: {e}")
            return []


class DynamicSitemapParser(BaseParser):
    """Dinamik sitemap parser (Sözcü gibi siteler için)"""
    
    def get_items(self):
        # Sözcü için özel parser
        return SitemapParser(self.source_key, self.url).get_items()


def get_parser(source_key):
    """Kaynak için uygun parser'ı getir"""
    from config import RSS_SOURCES
    
    source_config = RSS_SOURCES.get(source_key)
    if not source_config:
        return None
    
    url = source_config['url']
    parser_type = source_config.get('type', 'rss')
    
    if parser_type == 'rss':
        return RSSParser(source_key, url)
    elif parser_type == 'sitemap':
        return SitemapParser(source_key, url)
    elif parser_type == 'sitemap_index':
        return SitemapIndexParser(source_key, url)
    elif parser_type == 'dynamic_sitemap':
        return DynamicSitemapParser(source_key, url)
    else:
        return RSSParser(source_key, url)
