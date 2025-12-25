import os
import json
import pickle
import numpy as np
import re
from kiwipiepy import Kiwi
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
import faiss

# 1. 문서 로드 및 전처리
def chunk_markdown_hierarchical(text, filename):
    """
    마크다운 파일을 계층 구조를 유지하면서 청크로 분리합니다.
    각 청크는 상위 헤더를 포함하여 컨텍스트를 유지합니다.
    """
    lines = text.split('\n')
    chunks = []
    current_headers = {1: None, 2: None, 3: None}  # H1, H2, H3 추적
    current_content = []
    
    for line in lines:
        # 헤더 감지 (# , ## , ###)
        header_match = re.match(r'^(#{1,3})\s+(.+)$', line)
        
        if header_match:
            # 이전 청크 저장
            if current_content:
                chunk_text = '\n'.join(current_content).strip()
                if chunk_text:
                    chunks.append(chunk_text)
                current_content = []
            
            # 헤더 레벨 파악
            level = len(header_match.group(1))
            header_text = header_match.group(2).strip()
            
            # 현재 레벨 업데이트
            current_headers[level] = line
            # 하위 레벨 초기화
            for i in range(level + 1, 4):
                current_headers[i] = None
            
            # 상위 헤더들을 포함하여 새 청크 시작
            for i in range(1, 4):
                if current_headers[i]:
                    current_content.append(current_headers[i])
        else:
            # 일반 콘텐츠
            if line.strip():
                current_content.append(line)
    
    # 마지막 청크 저장
    if current_content:
        chunk_text = '\n'.join(current_content).strip()
        if chunk_text:
            chunks.append(chunk_text)
    
    return chunks

def chunk_simple(text):
    """
    간단한 줄바꿈 기반 청킹 (기존 방식)
    """
    return [c.strip() for c in text.split('\n') if c.strip()]

def load_documents(data_dir, use_hierarchical=True):
    """
    문서를 로드하고 청킹합니다.
    
    Args:
        data_dir: 데이터 디렉토리 경로
        use_hierarchical: True면 마크다운 계층 구조 유지, False면 단순 청킹
    """
    documents = []
    files = [f for f in os.listdir(data_dir) if f.endswith((".txt", ".md"))]
    
    print(f"   발견된 파일: {len(files)}개")
    print()
    
    for idx, filename in enumerate(files, 1):
        path = os.path.join(data_dir, filename)
        
        # 파일 처리 시작 표시
        print(f"   [{idx}/{len(files)}] 📄 {filename} 처리 중...", end=" ")
        
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
            
            # 청킹 전략 선택
            if use_hierarchical and filename.endswith(".md"):
                chunks = chunk_markdown_hierarchical(text, filename)
                strategy = "계층구조"
            else:
                chunks = chunk_simple(text)
                strategy = "단순"
            
            # 문서 엔트리 생성
            for i, chunk in enumerate(chunks):
                doc_entry = {
                    "doc_id": filename,
                    "chunk_id": f"{filename}::chunk::{i}",
                    "text": chunk,
                    "metadata": {
                        "source": path,
                        "index": i,
                        "total_chunks": len(chunks),
                        "prev_chunk_id": f"{filename}::chunk::{i-1}" if i > 0 else None,
                        "next_chunk_id": f"{filename}::chunk::{i+1}" if i < len(chunks) - 1 else None,
                        "chunking_strategy": "hierarchical" if (use_hierarchical and filename.endswith(".md")) else "simple"
                    }
                }
                documents.append(doc_entry)
            
            # 처리 완료 표시
            print(f"✅ {len(chunks)}개 청크 생성 ({strategy})")
    
    print()
    return documents

# 2. BM25 인덱싱 (명사/동사 위주 토큰화)
def build_bm25(documents):
    kiwi = Kiwi()
    tokenized_corpus = []
    for doc in documents:
        # 형태소 분석 후 명사(N), 동사(V), 형용사(J) 추출
        tokens = [t.form for t in kiwi.tokenize(doc['text']) if t.tag.startswith(('N', 'V', 'J'))]
        tokenized_corpus.append(tokens)
    
    bm25 = BM25Okapi(tokenized_corpus)
    return bm25, tokenized_corpus

# 3. Semantic 인덱싱 (벡터라이징)
def build_faiss(documents):
    model = SentenceTransformer('jhgan/ko-sroberta-multitask') # 한국어 성능이 좋은 모델
    texts = [doc['text'] for doc in documents]
    embeddings = model.encode(texts)
    
    # Cosine Similarity를 위해 L2 정규화 후 Inner Product 사용
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    faiss.normalize_L2(embeddings)
    index.add(embeddings)
    
    return index, model

def main():
    data_dir = "./data"
    output_dir = "./index_output"
    os.makedirs(output_dir, exist_ok=True)

    # 청킹 전략 선택 (기본값: hierarchical=True)
    use_hierarchical = True  # False로 변경하면 기존 단순 청킹 사용
    
    print("🚀 문서 로드 중...")
    print(f"   청킹 전략: {'계층 구조 유지 (마크다운)' if use_hierarchical else '단순 줄바꿈'}")
    docs = load_documents(data_dir, use_hierarchical=use_hierarchical)
    
    print("🚀 BM25 인덱스 생성 중...")
    bm25, tokenized_corpus = build_bm25(docs)
    
    print("🚀 Semantic (FAISS) 인덱스 생성 중...")
    faiss_index, model = build_faiss(docs)

    # 저장
    print("📂 인덱스 저장 중...")
    # 1. 메타데이터 및 문서 원문
    with open(os.path.join(output_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)
    
    # 2. BM25 (Object 자체 저장 또는 토큰 저장)
    with open(os.path.join(output_dir, "bm25.pkl"), "wb") as f:
        pickle.dump(bm25, f)
    
    # 3. FAISS Index
    faiss.write_index(faiss_index, os.path.join(output_dir, "index.faiss"))

    print(f"✅ 인덱싱 완료! (문서 수: {len(docs)})") 
    print(f"📍 저장 위치: {output_dir}")
    
    # 청킹 전략별 통계
    hierarchical_count = sum(1 for d in docs if d['metadata'].get('chunking_strategy') == 'hierarchical')
    simple_count = len(docs) - hierarchical_count
    print(f"📊 청킹 통계: 계층구조={hierarchical_count}, 단순={simple_count}")

if __name__ == "__main__":
    main()
