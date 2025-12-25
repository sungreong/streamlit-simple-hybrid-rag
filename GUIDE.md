# 한글 문서 검색 및 RAG 시스템 구축 가이드

본 문서는 BM25와 Semantic 검색을 결합한 하이브리드 검색 시스템의 요구사항 및 설계 사양을 정의합니다.

---

## 1. 목표 정의 (Target Definition)

### 1.1 목적
- 한글 문서에서 질문을 입력하면 **BM25(키워드)**와 **Semantic(의미)** 검색을 함께 사용하여 가장 관련성 높은 Top-k 문서를 반환합니다.

### 1.2 범위
- **필수:** 하이브리드 검색 기능 구현
- **옵션:** LLM을 통한 요약 및 답변 생성 (RAG)

### 1.3 성능 목표
| 항목 | 목표치 | 비고 |
| :--- | :--- | :--- |
| **문서 수** | 1만 ~ 10만 건 | 초기 PoC는 1만 건 이하 권장 |
| **응답 시간** | 1초 ~ 3초 내 | 로컬 CPU 기준 Top-k 결과 표시 |

---

## 2. 데이터 요구사항 (Data Requirements)

### 2.1 문서 입력 형태
- **1차 지원:** `.txt`, `.md`
- **추후 확장:** `.pdf` (텍스트 추출), `.docx`

### 2.2 문서 스키마 (Internal Standard)
| 필드명 | 타입 | 설명 |
| :--- | :--- | :--- |
| `doc_id` | string | **필수** 문서 고유 식별자 |
| `title` | string | 제목 (없으면 파일명 사용) |
| `text` | string | 검색 대상 본문 |
| `metadata` | dict | 선택 사항 (source, date, tags, path 등) |

### 2.3 전처리 규칙
- **Chunking:** 문단 단위 분할 (권장: 300 ~ 800자)
- **ID 부여:** `{doc_id}::chunk::{n}` 형식
- **원문 복원:** `doc_id`, `chunk_no`, `offset` 정보를 저장하여 원문 복원 가능 유지

---

## 3. 인덱싱 요구사항 (Indexing Requirements)

### 3.1 BM25 인덱스 (한글 특화)
- **토크나이저:** `Kiwi` (kiwipiepy)
- **토큰 필터:**
    - 품사: 명사(N\*), 동사/형용사(V\*) 위주 추출
    - 길이 1인 토큰 제거 (노이즈 감소 옵션)
- **인덱스 생성:** Chunk 단위 토큰 리스트를 Corpus로 생성하여 `BM25Okapi` 스코어 계산

### 3.2 Semantic 인덱스
- **임베딩 모델:** `sentence-transformers` (multilingual MiniLM 계열, 가벼운 모델 권장)
- **벡터 인덱스:** `FAISS IndexFlatIP` (정규화 후 Cosine Similarity처럼 사용)
- **저장 방식:** 
    - PoC 단계에서는 메모리 유지 및 로컬 파일 저장
    - 메타데이터: `json`
    - FAISS 인덱스: `index.faiss`
    - BM25 토큰: `tokens.pkl` 등

> [!NOTE]
> **아키텍처 참고:** 실제 운영 환경에서는 실시간 벡터라이즈 대신, 정제된 문서를 미리 인덱싱하여 벡터 DB 또는 파일로 저장한 후 검색 시 로드해서 사용하는 방식을 권장합니다.

### 3.3 업데이트 전략
- **MVP:** "전체 재빌드" 기능 제공
- **옵션:** 파일 업로드 시 해당 문서만 부분 업데이트(Incremental Update)

---

## 4. 검색 및 랭킹 (Search & Ranking)

### 4.1 검색 입력 파라미터
- `query`: 사용자 질문 (string)
- `top_k`: 결과 반환 개수 (Default: 10)
- `weights`: `bm25_weight`(0.6) / `semantic_weight`(0.4) 가중치 조절

### 4.2 점수 계산 및 Fusion
1. **BM25:** 전체 Corpus에서 스코어 산출
2. **Semantic:** FAISS를 통해 상위 후보(예: 50~200개) 추출
3. **Score Normalization:** Min-Max 또는 Z-score (초기엔 Min-Max 사용)
4. **Hybrid Fusion:** `(w_bm25 * bm25_norm) + (w_sem * sem_norm)`

### 4.3 결과 반환 정보
- `chunk_id`, `title`, `snippet` (하이라이트), `score_total`, `score_bm25`, `score_sem`
- 관련 메타데이터 일부 표시

---

## 5. UI/UX 요구사항 (Streamlit)

### 5.1 화면 구성
- **사이드바:**
    - 데이터 로드 및 업로드
    - **인덱스 빌드/리빌드** 버튼
    - `top_k` 슬라이더
    - 가중치(BM25/Semantic) 조절 슬라이더
- **메인 영역:**
    - 검색창
    - Top-k 결과 리스트 (확대/축소 지원)

### 5.2 디버깅 도구
- "왜 이 결과가 나왔나?" 기능 (Explainability)
- 상위 매칭 토큰 표시 (BM25)
- 임베딩 유사도 점수 표시 (Semantic)
- 쿼리 형태소 분석 결과(Kiwi) 토글 보기

---

## 6. 운영 및 품질 (Operations)

### 6.1 캐싱 (Caching)
- Streamlit 세션을 활용하여 문서, BM25 객체, FAISS 인덱스, 임베딩 모델 캐싱
- 재시작 시 로딩 시간 단축을 위한 로컬 파일 지속성 유지

### 6.2 품질 점검
- 테스트 쿼리(약 20개)를 통한 정답 문서 노출 여부(Hit Rate@10) 체크
- 가중치 튜닝을 위한 기준 데이터셋 마련

---

## 7. 기술 스택 (Tech Stack)

### 필수 라이브러리
- `streamlit`
- `kiwipiepy`
- `rank-bm25`
- `sentence-transformers`
- `faiss-cpu`
- `numpy`

### 선택 사항
- `pydantic` (데이터 스키마 정의)
- `rapidfuzz` (유사어 보정)
- `duckdb` (메타데이터 저장용)

---

## 8. 완료 정의 (Definition of Done)
1. 문서 폴더 지정/업로드 시 인덱싱 완료
2. 한글 쿼리 입력 시 하이브리드 검색 수행
3. 점수 기반 Top-k 결과 및 원문 확인 가능