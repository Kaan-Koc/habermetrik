"""
Habermetre - Haber Gruplama (Clustering) Modülü

BERT embeddings kullanarak Türkçe haberleri anlamsal olarak gruplar.
"""

from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
from collections import Counter
import numpy as np
import re


class NewsClusterer:
    """Haber gruplama sınıfı"""
    
    def __init__(self, model_name='paraphrase-multilingual-MiniLM-L12-v2'):
        """
        Args:
            model_name: Sentence transformer model adı
        """
        print(f"📥 BERT modeli yükleniyor: {model_name}")
        self.model = SentenceTransformer(model_name)
        print(f"✅ Model yüklendi ({self.model.get_sentence_embedding_dimension()} boyutlu vektörler)")
    
    def extract_keywords(self, text, top_n=3):
        """
        Metinden anahtar kelimeleri çıkar
        
        Args:
            text: Metin
            top_n: Kaç kelime
            
        Returns:
            En sık kullanılan kelimeler
        """
        # Türkçe stopwords (durdurulması gereken kelimeler)
        stopwords = {
            've', 'veya', 'ile', 'ama', 'fakat', 'ancak', 'için', 'gibi', 
            'bir', 'bu', 'şu', 'o', 'ne', 'nasıl', 'neden', 'niçin',
            'mi', 'mı', 'mu', 'mü', 'de', 'da', 'ki', 'dı', 'di',
            'var', 'yok', 'olan', 'oldu', 'olacak', 'etti', 'ediyor',
            'den', 'dan', 'ten', 'tan', 'e', 'a', 'ye', 'ya'
        }
        
        # Küçük harfe çevir ve sadece harfleri al
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Stopwords ve kısa kelimeleri filtrele
        filtered = [w for w in words if w not in stopwords and len(w) > 2]
        
        # En sık kullanılanları bul
        if not filtered:
            return []
        
        counter = Counter(filtered)
        return [word for word, _ in counter.most_common(top_n)]
    
    def generate_cluster_title(self, news_items):
        """
        Küme için otomatik başlık oluştur
        
        Args:
            news_items: Kümedeki haberler
            
        Returns:
            Küme başlığı
        """
        # Tüm başlıkları birleştir
        all_text = ' '.join([item['title'] for item in news_items])
        
        # En sık kullanılan 2-3 kelimeyi al
        keywords = self.extract_keywords(all_text, top_n=3)
        
        if keywords:
            return ' '.join(keywords).title()
        else:
            return news_items[0]['title'][:50] + '...'
    
    def cluster_news(self, news_items, eps=0.35, min_samples=2):
        """
        Haberleri kümelere ayır
        
        Args:
            news_items: Haber listesi (dict'ler)
            eps: DBSCAN epsilon parametresi (0-1, düşük = sıkı gruplama)
            min_samples: Minimum haber sayısı
            
        Returns:
            {
                cluster_id: {
                    'title': 'Küme Başlığı',
                    'count': 5,
                    'news': [...]
                }
            }
        """
        if not news_items:
            return {}
        
        # Başlıkları al
        titles = [item['title'] for item in news_items]
        
        print(f"🔍 {len(titles)} haber için embedding hesaplanıyor...")
        
        # Embedding'lere çevir
        embeddings = self.model.encode(titles, show_progress_bar=False)
        
        print(f"📊 Clustering yapılıyor (eps={eps}, min_samples={min_samples})...")
        
        # DBSCAN clustering (cosine distance kullan)
        clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine')
        labels = clustering.fit_predict(embeddings)
        
        # Kümeleri oluştur
        clusters = {}
        for idx, label in enumerate(labels):
            # -1 = noise (kümeye girmeyen)
            if label == -1:
                # Tek başına haberler için ayrı kümeler oluştur
                label = f"single_{idx}"
            
            if label not in clusters:
                clusters[label] = []
            
            clusters[label].append(news_items[idx])
        
        print(f"✅ {len(clusters)} küme oluşturuldu")
        
        # Her küme için başlık oluştur
        result = {}
        for cluster_id, items in clusters.items():
            result[cluster_id] = {
                'id': cluster_id,
                'title': self.generate_cluster_title(items),
                'count': len(items),
                'news': sorted(items, key=lambda x: x.get('pub_date') or '', reverse=True)
            }
        
        # Kümeleri haber sayısına göre sırala
        sorted_clusters = dict(sorted(
            result.items(), 
            key=lambda x: x[1]['count'], 
            reverse=True
        ))
        
        return sorted_clusters


# Global singleton
_clusterer = None

def get_clusterer():
    """Global clusterer instance"""
    global _clusterer
    if _clusterer is None:
        _clusterer = NewsClusterer()
    return _clusterer
