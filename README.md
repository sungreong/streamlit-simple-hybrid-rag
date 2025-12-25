# 🚀 AI Hybrid Document Search System

가장 가볍고 효율적인 오픈소스 스택으로 구축된 한글 하이브리드 검색 시스템입니다.
BM25(키워드 검색)와 Semantic(의미 기반 검색)을 결합하여 최적의 검색 결과를 제공하며, OpenAI 및 Google Gemini LLM을 지원합니다.

## ✨ 주요 기능

- 🔍 **하이브리드 검색**: BM25(키워드 정확도) + Semantic(문맥 이해)의 장점 결합 (`searcher.py`)
- 🤖 **멀티 LLM 지원**: OpenAI(GPT) 및 Google Gemini 연동 지원 (`llm.py`)
- 🇰🇷 **한글 최적화**: Kiwi 형태소 분석기를 이용한 정교한 토큰화
- 🔐 **보안 강화**: 비밀번호 인증 및 간편한 비밀번호 변경 도구 제공 (`change_password.py`)
- 🎨 **프리미엄 UI**: Streamlit 기반의 현대적이고 직관적인 사용자 인터페이스 (`ui_components.py`)
- 📄 **문서 뷰어**: 검색된 원본 문서의 전체 내용을 바로 확인 가능

## 🛠️ 기술 스택

- **Core**: Python 3.12
- **Search Engine**: `rank-bm25` + `FAISS` + `Kiwi` (Hybrid)
- **Embedding**: `jhgan/ko-sroberta-multitask` (SBERT)
- **Framework**: Streamlit
- **LLM Client**: `requests` (Lightweight REST API calls)
- **Container**: Docker + Docker Compose

## 📦 설치 및 실행

### 1. 저장소 클론
```bash
git clone <repository-url>
cd SimpleRetrievalDOC
```

### 2. 환경 설정 (Secrets)
`.streamlit/secrets.toml` 파일을 생성하여 비밀번호와 API 키를 설정합니다.

```bash
# 템플릿 복사
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
```

`secrets.toml` 파일을 열어 API 키를 입력하세요.
```toml
password = "..." 
openai_api_key = "sk-..." 
gemini_api_key = "..."
```

### 3. 샘플 데이터 준비
`data/` 폴더에 검색하고 싶은 `.txt` 또는 `.md` 파일을 넣습니다.

### 4. 인덱싱 (데이터 벡터화)
새로운 문서가 추가될 때마다 실행해야 합니다.

```bash
# Docker 환경
docker-compose run --rm streamlit-app python vectorize.py

# 또는 로컬 환경
python vectorize.py
```

### 5. 앱 실행
```bash
# Docker 환경
docker-compose up --build

# 또는 로컬 환경
streamlit run app.py
```

### 6. 접속
브라우저에서 `http://localhost:8501` 접속 후 설정한 비밀번호 입력.

## 📁 프로젝트 구조

```
SimpleRetrievalDOC/
├── app.py                  # Streamlit 메인 앱 (UI 및 로직 통합)
├── auth.py                 # 비밀번호 인증 및 세션 관리
├── change_password.py      # 비밀번호 변경 유틸리티
├── vectorize.py            # 문서 임베딩 및 인덱싱 스크립트
├── search.py               # CLI 기반 검색 테스트 스크립트
├── searcher.py             # 하이브리드 검색 엔진 (BM25 + Semantic)
├── llm.py                  # LLM 연동 모듈 (OpenAI, Gemini)
├── ui_components.py        # UI 스타일 및 컴포넌트 정의
├── requirements.txt        # 필요한 Python 패키지 목록
├── Dockerfile              # Docker 이미지 빌드 설정
├── docker-compose.yml      # Docker 서비스 오케스트레이션
├── GUIDE.md                # 상세 시스템 가이드
├── PASSWORD_GUIDE.md       # 비밀번호 관리 가이드
├── .streamlit/             # Streamlit 설정
│   ├── secrets.toml        # (자동생성) 비밀번호 및 API 키
│   └── secrets.toml.template # secrets.toml 템플릿
├── data/                   # 검색 대상 문서 저장소
│   └── README.md
└── index_output/           # 생성된 검색 인덱스 데이터
    ├── metadata.json
    ├── bm25.pkl
    └── index.faiss
```

## 🔒 보안 및 비밀번호 변경

### 비밀번호 변경 도구 사용
내장된 스크립트를 사용하여 안전하게 비밀번호를 변경할 수 있습니다.

```bash
python change_password.py
```
위 명령어를 실행하면 비밀번호를 입력받아 해시(SHA-256) 처리 후 `secrets.toml`을 자동으로 업데이트합니다.

## 📖 사용 가이드

1. **문서 추가**: `data/` 폴더에 파일 추가 -> `python vectorize.py` 실행.
2. **검색**: 키워드 또는 문장으로 질문 입력.
3. **가중치 조절**: 사이드바에서 BM25(키워드)와 Semantic(의미) 검색의 반영 비율 조절 가능.
4. **LLM 선택**: 사이드바에서 사용할 AI 모델(OpenAI/Gemini) 선택 가능.

## 🤝 기여

이슈 및 풀 리퀘스트를 환영합니다!

## 📄 라이선스

MIT License

## 🙏 감사의 말

- [Kiwi](https://github.com/bab2min/kiwipiepy) - 한글 형태소 분석
- [FAISS](https://github.com/facebookresearch/faiss) - 고속 벡터 검색
- [Sentence Transformers](https://www.sbert.net/) - 임베딩 모델
- [Streamlit](https://streamlit.io/) - 웹 프레임워크
