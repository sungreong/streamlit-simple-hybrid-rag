"""
하이브리드 검색 엔진 모듈
BM25 + Semantic 검색을 결합한 검색 시스템
"""
import os
import json
import pickle
import numpy as np
import faiss
from kiwipiepy import Kiwi
from sentence_transformers import SentenceTransformer


class HybridSearcher:
    def __init__(self, index_dir):
        self.index_dir = index_dir
        self.kiwi = Kiwi()
        self.model = SentenceTransformer('jhgan/ko-sroberta-multitask')
        
        # Load indices
        with open(os.path.join(index_dir, "metadata.json"), "r", encoding="utf-8") as f:
            self.documents = json.load(f)
            
        with open(os.path.join(index_dir, "bm25.pkl"), "rb") as f:
            self.bm25 = pickle.load(f)
            
        self.faiss_index = faiss.read_index(os.path.join(index_dir, "index.faiss"))
        
        # Helper map
        self.chunk_map = {d['chunk_id']: d for d in self.documents}
        self.doc_map = {}
        for d in self.documents:
            if d['doc_id'] not in self.doc_map:
                self.doc_map[d['doc_id']] = []
            self.doc_map[d['doc_id']].append(d)
        
        for doc_id in self.doc_map:
            self.doc_map[doc_id].sort(key=lambda x: x['metadata']['index'])

    def search(self, query, top_k=5, w_bm25=0.6, w_sem=0.4):
        # 1. BM25
        query_tokens = [t.form for t in self.kiwi.tokenize(query) if t.tag.startswith(('N', 'V', 'J'))]
        bm25_scores = self.bm25.get_scores(query_tokens)
        
        # 2. Semantic
        query_emb = self.model.encode([query])
        faiss.normalize_L2(query_emb)
        sem_scores, sem_indices = self.faiss_index.search(query_emb, len(self.documents))
        
        full_sem_scores = np.zeros(len(self.documents))
        for score, idx in zip(sem_scores[0], sem_indices[0]):
            full_sem_scores[idx] = score

        # 3. Normalization
        def normalize(scores):
            s_min, s_max = np.min(scores), np.max(scores)
            if s_max - s_min == 0: return np.zeros_like(scores)
            return (scores - s_min) / (s_max - s_min)

        bm25_norm = normalize(bm25_scores)
        sem_norm = normalize(full_sem_scores)

        # 4. Hybrid Fusion
        final_scores = (w_bm25 * bm25_norm) + (w_sem * sem_norm)
        top_indices = np.argsort(final_scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = float(final_scores[idx])
            # 관련도 레벨 계산
            if score > 0.7:
                relevance = "high"
            elif score > 0.4:
                relevance = "medium"
            else:
                relevance = "low"
                
            results.append({
                "chunk_id": self.documents[idx]['chunk_id'],
                "doc_id": self.documents[idx]['doc_id'],
                "text": self.documents[idx]['text'],
                "score": score,
                "relevance": relevance,
                "metadata": self.documents[idx]['metadata']
            })
        return results
