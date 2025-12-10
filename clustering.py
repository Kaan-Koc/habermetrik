"""
Habermetre - Haber Gruplama (Clustering) Modülü

BERT embeddings kullanarak Türkçe haberleri anlamsal olarak gruplar.
"""


from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from collections import Counter
import re
import numpy as np

class NewsClusterer:
    """Haber gruplama sınıfı (TF-IDF Lightweight Sürümü)"""
    
    def __init__(self, model_name=None):
        """
        Args:
            model_name: Geriye uyumluluk için tutuldu (kullanılmıyor)
        """
        print("📥 TF-IDF Vektörleştirici ile başlatılıyor (Lightweight Mode)")
        self.vectorizer = TfidfVectorizer(
            stop_words=None, # Türkçe stop words aşağıda manuel temizleniyor
            max_features=5000,
            ngram_range=(1, 2)
        )
    
    def extract_keywords(self, text, top_n=3):
        """Metinden anahtar kelimeleri çıkar"""
        stopwords = {
            've', 'veya', 'ile', 'ama', 'fakat', 'ancak', 'için', 'gibi', 
            'bir', 'bu', 'şu', 'o', 'ne', 'nasıl', 'neden', 'niçin',
            'mi', 'mı', 'mu', 'mü', 'de', 'da', 'ki', 'dı', 'di',
            'var', 'yok', 'olan', 'oldu', 'olacak', 'etti', 'ediyor',
            'den', 'dan', 'ten', 'tan', 'e', 'a', 'ye', 'ya', 'ile'
        }
        
        words = re.findall(r'\b\w+\b', text.lower())
        filtered = [w for w in words if w not in stopwords and len(w) > 2]
        
        if not filtered:
            return []
        
        counter = Counter(filtered)
        return [word for word, _ in counter.most_common(top_n)]
    
    def generate_cluster_title(self, news_items):
        """Küme için otomatik başlık oluştur"""
        all_text = ' '.join([item['title'] for item in news_items])
        keywords = self.extract_keywords(all_text, top_n=3)
        
        if keywords:
            return ' '.join(keywords).title()
        else:
            return news_items[0]['title'][:50] + '...'
    
    def cluster_news(self, news_items, eps=0.4, min_samples=2):
        """Haberleri kümelere ayır (TF-IDF + DBSCAN)"""
        if not news_items:
            return {}
        
        titles = [item['title'] for item in news_items]
        
        print(f"🔍 {len(titles)} haber için TF-IDF hesaplanıyor...")
        
        # TF-IDF Matrisi oluştur
        try:
            tfidf_matrix = self.vectorizer.fit_transform(titles)
            
            # DBSCAN (Cosine Similarity = 1 - Cosine Distance)
            # sklearn DBSCAN varsayılan olarak euclidean kullanır. 
            # TF-IDF l2 normalize olduğu için euclidean ~ cosine distance davranır.
            # Ancak biz yine de 'cosine' metriğini kullanalım daha doğru sonuç için.
            
            print(f"📊 Clustering yapılıyor (eps={eps}, min_samples={min_samples})...")
            
            clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine', algorithm='brute')
            labels = clustering.fit_predict(tfidf_matrix) # Sparse matrix destekler
            
            # Kümeleri oluştur
            clusters = {}
            for idx, label in enumerate(labels):
                if label == -1: # Noise
                    label = f"single_{idx}"
                else:
                    label = str(label) # JSON uyumluluğu için string
                
                if label not in clusters:
                    clusters[label] = []
                
                clusters[label].append(news_items[idx])
            
            print(f"✅ {len(clusters)} küme oluşturuldu")
            
            # Sonuçları hazırla
            result = {}
            for cluster_id, items in clusters.items():
                result[cluster_id] = {
                    'id': cluster_id,
                    'title': self.generate_cluster_title(items),
                    'count': len(items),
                    'news': sorted(items, key=lambda x: x.get('pub_date') or '', reverse=True)
                }
            
            # Sırala
            sorted_clusters = dict(sorted(
                result.items(), 
                key=lambda x: x[1]['count'], 
                reverse=True
            ))
            
            return sorted_clusters

        except ValueError:
            # Boş veri vb. durumlarda
            return {}

# Global singleton
_clusterer = None

def get_clusterer():
    global _clusterer
    if _clusterer is None:
        _clusterer = NewsClusterer()
    return _clusterer

