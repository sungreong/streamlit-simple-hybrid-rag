import os
import json
import pickle
import numpy as np
from kiwipiepy import Kiwi
from sentence_transformers import SentenceTransformer
import faiss

# 1. 인덱스 로딩 전용 클래스
class HybridSearcher:
    def __init__(self, index_dir):
        self.index_dir = index_dir
        self.kiwi = Kiwi()
        self.model = SentenceTransformer('jhgan/ko-sroberta-multitask')
        
        print("📂 인덱스 로딩 중...")
        with open(os.path.join(index_dir, "metadata.json"), "r", encoding="utf-8") as f:
            self.documents = json.load(f)
            
        with open(os.path.join(index_dir, "bm25.pkl"), "rb") as f:
            self.bm25 = pickle.load(f)
            
        self.faiss_index = faiss.read_index(os.path.join(index_dir, "index.faiss"))
        print("✅ 로딩 완료!")

    def search(self, query, top_k=5, w_bm25=0.5, w_sem=0.5):
        # 1. BM25 검색
        query_tokens = [t.form for t in self.kiwi.tokenize(query) if t.tag.startswith(('N', 'V', 'J'))]
        bm25_scores = self.bm25.get_scores(query_tokens)
        
        # 2. Semantic 검색
        query_emb = self.model.encode([query])
        faiss.normalize_L2(query_emb)
        sem_scores, sem_indices = self.faiss_index.search(query_emb, len(self.documents))
        
        # FAISS 결과는 (1, N) 형태이므로 1차원으로 변환하고 문서 인덱스에 맞게 매핑
        full_sem_scores = np.zeros(len(self.documents))
        for score, idx in zip(sem_scores[0], sem_indices[0]):
            full_sem_scores[idx] = score

        # 3. 정규화 (Min-Max)
        def normalize(scores):
            s_min, s_max = np.min(scores), np.max(scores)
            if s_max - s_min == 0: return scores
            return (scores - s_min) / (s_max - s_min)

        bm25_norm = normalize(bm25_scores)
        sem_norm = normalize(full_sem_scores)

        # 4. Hybrid Fusion
        final_scores = (w_bm25 * bm25_norm) + (w_sem * sem_norm)
        
        # 정렬 후 Top-k 반환
        top_indices = np.argsort(final_scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append({
                "text": self.documents[idx]['text'],
                "score": float(final_scores[idx]),
                "bm25": float(bm25_norm[idx]),
                "semantic": float(sem_norm[idx]),
                "source": self.documents[idx]['doc_id']
            })
        return results

def main():
    index_dir = "./index_output"
    if not os.path.exists(index_dir):
        print("❌ 인덱스가 없습니다. 먼저 vectorize.py를 실행하세요.")
        return

    searcher = HybridSearcher(index_dir)
    
    while True:
        query = input("\n🔍 검색어를 입력하세요 (종료: q): ")
        if query.lower() == 'q':
            break
            
        results = searcher.search(query)
        
        print(f"\n--- '{query}' 검색 결과 ---")
        for i, res in enumerate(results):
            print(f"[{i+1}] 점수: {res['score']:.4f} (BM25: {res['bm25']:.2f}, Sem: {res['semantic']:.2f})")
            print(f"📄 내용: {res['text']}")
            print(f"📍 출처: {res['source']}\n")

if __name__ == "__main__":
    main()
