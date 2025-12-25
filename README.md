# 🚀 AI Hybrid Document Search System

가장 가볍고 효율적인 오픈소스 스택으로 구축된 한글 하이브리드 검색 시스템입니다.

## ✨ 주요 기능

- 🔍 **하이브리드 검색**: BM25(키워드) + Semantic(의미) 검색 결합
- 🇰🇷 **한글 최적화**: Kiwi 형태소 분석기 사용
- 🔐 **비밀번호 인증**: 안전한 접근 제어
- 📄 **문서 뷰어**: 검색 결과의 전체 문맥 확인
- 🎨 **프리미엄 UI**: 현대적이고 직관적인 인터페이스

## 🛠️ 기술 스택

- **검색 엔진**: `rank-bm25` + `FAISS` + `Kiwi`
- **임베딩 모델**: `jhgan/ko-sroberta-multitask`
- **웹 프레임워크**: Streamlit
- **컨테이너**: Docker + Docker Compose
- **언어**: Python 3.12

## 📦 설치 및 실행

### 1. 저장소 클론
```bash
git clone <repository-url>
cd SimpleRetrievalDOC
```

### 2. Secrets 파일 설정
```bash
# 템플릿을 복사하여 secrets.toml 생성
cp .streamlit/secrets.toml.template .streamlit/secrets.toml

# (선택) 비밀번호 변경 (PASSWORD_GUIDE.md 참조)
```

### 3. 샘플 데이터 준비
`data/` 폴더에 `.txt` 또는 `.md` 파일을 추가하세요.

### 4. 인덱싱
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
브라우저에서 `http://localhost:8501` 접속 후 비밀번호 입력 (기본: `admin123`)

## 📁 프로젝트 구조

```
SimpleRetrievalDOC/
├── app.py                  # Streamlit 메인 앱
├── auth.py                 # 인증 모듈
├── vectorize.py            # 오프라인 인덱싱 스크립트
├── search.py               # CLI 검색 테스트 스크립트
├── requirements.txt        # Python 의존성
├── Dockerfile              # Docker 이미지 정의
├── docker-compose.yml      # Docker Compose 설정
├── GUIDE.md               # 시스템 설계 가이드
├── PASSWORD_GUIDE.md      # 비밀번호 변경 가이드
├── .streamlit/
│   ├── secrets.toml       # 비밀번호 설정 (Git 제외)
│   └── secrets.toml.template  # 설정 템플릿
├── data/                  # 문서 저장 폴더
│   └── README.md
└── index_output/          # 생성된 인덱스 (Git 제외)
    ├── metadata.json
    ├── bm25.pkl
    └── index.faiss
```

## 🔒 보안 주의사항

⚠️ **반드시 확인하세요!**

1. `.streamlit/secrets.toml` 파일은 Git에 커밋되지 않습니다.
2. 기본 비밀번호(`admin123`)를 반드시 변경하세요.
3. 민감한 데이터는 `data/` 폴더에 저장하지 마세요.

## 📖 사용 가이드

### 비밀번호 변경
`PASSWORD_GUIDE.md` 파일을 참조하세요.

### 새 문서 추가
1. `data/` 폴더에 문서 추가
2. `python vectorize.py` 실행
3. 앱 새로고침

### 검색 가중치 조절
사이드바에서 BM25/Semantic 가중치를 조절하여 검색 결과를 최적화할 수 있습니다.

## 🤝 기여

이슈 및 풀 리퀘스트를 환영합니다!

## 📄 라이선스

MIT License

## 🙏 감사의 말

- [Kiwi](https://github.com/bab2min/kiwipiepy) - 한글 형태소 분석
- [FAISS](https://github.com/facebookresearch/faiss) - 벡터 검색
- [Sentence Transformers](https://www.sbert.net/) - 임베딩 모델
- [Streamlit](https://streamlit.io/) - 웹 프레임워크
