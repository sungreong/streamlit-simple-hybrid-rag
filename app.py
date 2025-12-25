import streamlit as st
import os
import re
import markdown
import pandas as pd
from datetime import datetime
from io import BytesIO

# Import custom modules
from auth import check_password, show_logout_button
from searcher import HybridSearcher
from llm import get_ai_answer
from ui_components import APP_STYLES, WELCOME_HTML

# --- Page Config ---
st.set_page_config(
    page_title="문서 검색 시스템",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Authentication Check
if not check_password():
    st.stop()

# Apply Styles
st.markdown(APP_STYLES, unsafe_allow_html=True)

# --- Cached Functions ---
@st.cache_data
def render_markdown(text):
    """마크다운을 HTML로 렌더링 (캐싱)"""
    return markdown.markdown(
        text,
        extensions=['extra', 'codehilite', 'tables', 'fenced_code']
    )

@st.cache_data
def highlight_text(text, query):
    """검색어 하이라이트 (캐싱)"""
    return re.sub(
        f"({re.escape(query)})", 
        r'<span class="highlight">\1</span>', 
        text, 
        flags=re.IGNORECASE
    )

# --- History Persistence ---
HISTORY_FILE = "search_history.json"

def load_history():
    """질문 이력을 파일에서 로드합니다."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading history: {e}")
            return []
    return []

def save_history(history):
    """질문 이력을 파일에 저장합니다."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving history: {e}")

# --- QA Cache Persistence ---
QA_CACHE_FILE = "qa_cache.json"

def load_qa_cache():
    """QA 캐시를 파일에서 로드합니다."""
    if os.path.exists(QA_CACHE_FILE):
        try:
            with open(QA_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading QA cache: {e}")
            return {}
    return {}

def save_qa_cache(cache):
    """QA 캐시를 파일에 저장합니다."""
    try:
        with open(QA_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving QA cache: {e}")

# --- Main App ---
def main():
    index_dir = "./index_output"
    
    # Check if index exists
    if not os.path.exists(index_dir):
        st.error("❌ 검색할 문서가 없습니다.")
        st.info("관리자에게 문의하세요.")
        return

    # Load Searcher (Cached)
    @st.cache_resource
    def get_searcher():
        return HybridSearcher(index_dir)
    
    searcher = get_searcher()
    
    # Session State 초기화 (가장 먼저 실행)
    if 'qa_history' not in st.session_state:
        st.session_state['qa_history'] = load_history()
    
    # QA Cache 로드
    if 'qa_cache' not in st.session_state:
        st.session_state['qa_cache'] = load_qa_cache()
    
    # Sidebar (searcher 로드 후)
    with st.sidebar:
        st.title("📚 문서 검색")
        show_logout_button()
        
        st.markdown("---")
        st.caption(f"📂 총 {len(searcher.doc_map)}개 문서")
        
        # --- History Sidebar Section ---
        if st.session_state['qa_history']:
            st.markdown("---")
            with st.expander(f"📜 최근 질문 ({len(st.session_state['qa_history'])}개)", expanded=True):
                # 질문 이력 Excel 다운로드
                df_history = pd.DataFrame({
                    '번호': range(1, len(st.session_state['qa_history']) + 1),
                    '질문': st.session_state['qa_history']
                })
                
                buffer_hist = BytesIO()
                with pd.ExcelWriter(buffer_hist, engine='openpyxl') as writer:
                    df_history.to_excel(writer, index=False, sheet_name='질문이력')
                
                st.download_button(
                    label="📥 전체 이력 다운로드",
                    data=buffer_hist.getvalue(),
                    file_name=f"질문이력_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="질문 이력을 Excel로 다운로드",
                    use_container_width=True
                )
                
                # 전체 삭제 버튼 (확인 절차 포함)
                if st.button("🗑️ 전체 삭제", use_container_width=True, type="secondary"):
                    st.session_state['confirm_delete_history'] = True
                    st.rerun()

                # 삭제 확인
                if st.session_state.get('confirm_delete_history', False):
                    st.warning("⚠️ 모두 삭제하시겠습니까?")
                    col_confirm1, col_confirm2 = st.columns(2)
                    with col_confirm1:
                        if st.button("✅ 예", use_container_width=True, type="primary"):
                            st.session_state['qa_history'] = []
                            save_history([]) # 파일 초기화
                            st.session_state['confirm_delete_history'] = False
                            st.success("삭제됨")
                            st.rerun()
                    with col_confirm2:
                        if st.button("❌ 아니오", use_container_width=True):
                            st.session_state['confirm_delete_history'] = False
                            st.rerun()
                
                st.markdown("---")
                
                # 이력 리스트 표시 (역순)
                for idx, hist_q in enumerate(reversed(st.session_state['qa_history'][-10:])): # 최근 10개
                    col_hist, col_del = st.columns([4, 1])
                    with col_hist:
                        # 텍스트가 너무 길면 자름
                        btn_label = f"{hist_q[:15]}..." if len(hist_q) > 15 else hist_q
                        if st.button(f"💬 {btn_label}", key=f"hist_btn_{idx}", help=hist_q, use_container_width=True):
                            # 클릭 시 검색창(Tab1)과 질문창(Tab2) 모두 업데이트
                            st.session_state['search_input'] = hist_q
                            st.session_state['qa_question'] = hist_q
                            st.rerun()
                    with col_del:
                        if st.button("🗑️", key=f"hist_del_{idx}"):
                            # 역순이므로 원래 인덱스 계산 필요
                            original_idx = len(st.session_state['qa_history']) - 1 - idx
                            st.session_state['qa_history'].pop(original_idx)
                            save_history(st.session_state['qa_history'])
                            st.rerun()

    # Main UI
    st.title("🔍 문서 검색 & 질문")
    st.markdown("궁금한 내용을 검색하거나 질문하면 AI가 답변해드립니다.")
    
    # Tabs
    tab1, tab2 = st.tabs(["📄 문서 검색", "💬 AI 질문하기"])
    
    # ===== TAB 1: 문서 검색 =====
    with tab1:
        query = st.text_input(
            "검색어 입력",
            placeholder="예: 검색 시스템, BM25, 인덱싱 방법",
            label_visibility="collapsed",
            key="search_input"
        )

        if query:
            with st.spinner("🔍 검색 중..."):
                results = searcher.search(query, top_k=5)
            
            # 검색어도 이력에 저장 (결과가 있을 때만)
            if results and results[0]['score'] >= 0.1:
                if query not in st.session_state['qa_history']:
                    st.session_state['qa_history'].append(query)
                    if len(st.session_state['qa_history']) > 20:
                        st.session_state['qa_history'].pop(0)
                    save_history(st.session_state['qa_history'])
            
            if not results or results[0]['score'] < 0.1:
                st.warning("😕 관련된 문서를 찾지 못했습니다. 다른 검색어로 시도해보세요.")
                # 검색 결과가 없으면 선택된 문서 초기화
                if 'selected_doc' in st.session_state:
                    del st.session_state['selected_doc']
                    del st.session_state['selected_chunk']
            else:
                # 새로운 검색어인 경우 가장 관련성 높은 문서 자동 선택
                # 이전 검색어와 다르거나, 아직 선택된 문서가 없는 경우
                if query != st.session_state.get('previous_query') or 'selected_doc' not in st.session_state:
                    st.session_state['previous_query'] = query
                    st.session_state['selected_doc'] = results[0]['doc_id']
                    st.session_state['selected_chunk'] = results[0]['chunk_id']
                    # 리런하지 않고 바로 반영됨 (Session State 업데이트)
                # 좌우 2단 레이아웃: 왼쪽 검색 결과, 오른쪽 문서 뷰어
                col_left, col_right = st.columns([1, 1])
                
                # ===== 왼쪽: 검색 결과 =====
                with col_left:
                    # 헤더와 다운로드 버튼
                    col_header, col_download = st.columns([3, 1])
                    with col_header:
                        st.markdown(f"### 검색 결과 ({len(results)}개)")
                    with col_download:
                        # Excel 다운로드 버튼
                        df_results = pd.DataFrame([{
                            '순위': i+1,
                            '문서명': res['doc_id'],
                            '관련도': res['relevance'],
                            '점수': f"{res['score']:.4f}",
                            '내용': res['text'][:200] + ('...' if len(res['text']) > 200 else ''),
                            '전체내용': res['text']
                        } for i, res in enumerate(results)])
                        
                        buffer = BytesIO()
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            df_results.to_excel(writer, index=False, sheet_name='검색결과')
                        
                        st.download_button(
                            label="📥",
                            data=buffer.getvalue(),
                            file_name=f"검색결과_{query[:20]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            help="검색 결과를 Excel로 다운로드",
                            use_container_width=True
                        )
                    
                    for i, res in enumerate(results):
                        # 관련도 표시
                        if res['relevance'] == 'high':
                            badge_class, badge_text, card_class = "badge-high", "⭐⭐⭐ 매우 관련 있음", "relevance-high"
                        elif res['relevance'] == 'medium':
                            badge_class, badge_text, card_class = "badge-medium", "⭐⭐ 관련 있음", "relevance-medium"
                        else:
                            badge_class, badge_text, card_class = "badge-low", "⭐ 참고", "relevance-low"
                        
                        # 하이라이트
                        display_text = highlight_text(res['text'], query)
                        
                        # 카드 렌더링
                        st.markdown(f"""
                            <div class="result-card {card_class}">
                                <div class="relevance-badge {badge_class}">{badge_text}</div>
                                <div class="doc-title">📄 {res['doc_id']}</div>
                                <div class="doc-content">{display_text}</div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # 전체 문서 보기 버튼
                        if st.button(f"📖 전체 문서 보기", key=f"view_{i}", use_container_width=True):
                            st.session_state['selected_doc'] = res['doc_id']
                            st.session_state['selected_chunk'] = res['chunk_id']
                            st.rerun()
                
                # ===== 오른쪽: 문서 뷰어 =====
                with col_right:
                    if 'selected_doc' in st.session_state:
                        doc_id = st.session_state['selected_doc']
                        
                        # 헤더와 닫기 버튼
                        col_title, col_close = st.columns([4, 1])
                        with col_title:
                            st.markdown(f"### 📄 {doc_id}")
                        with col_close:
                            if st.button("✖️", key="close_viewer", help="닫기"):
                                del st.session_state['selected_doc']
                                del st.session_state['selected_chunk']
                                st.rerun()
                        
                        # 문서 내용 렌더링
                        all_chunks = searcher.doc_map[doc_id]
                        is_markdown = doc_id.lower().endswith('.md')
                        selected_chunk_id = st.session_state.get('selected_chunk')
                        
                        doc_content_html = ""
                        for c in all_chunks:
                            is_hit = c['chunk_id'] == selected_chunk_id
                            # 청크 ID를 HTML id 속성으로 사용
                            chunk_idx = c['metadata']['index']
                            html_id = f"chunk_{chunk_idx}"
                            
                            if is_markdown:
                                rendered_content = render_markdown(c["text"])
                                style_class = "viewer-highlight" if is_hit else "padding: 10px; margin-bottom: 8px;"
                                doc_content_html += f'<div id="{html_id}" class="{style_class}" style="{style_class if not is_hit else ""}">{rendered_content}</div>'
                            else:
                                if is_hit:
                                    doc_content_html += f'<div id="{html_id}" class="viewer-highlight">📍 {c["text"]}</div>'
                                else:
                                    doc_content_html += f'<div id="{html_id}" style="padding: 10px; margin-bottom: 8px;">{c["text"]}</div>'
                        
                        # 뷰어 컨테이너에 ID 부여
                        st.markdown(f'<div id="doc_viewer_container" class="doc-viewer">{doc_content_html}</div>', unsafe_allow_html=True)
                        
                        # 스크롤 자동 이동 스크립트
                        # 선택된 청크의 인덱스를 찾아서 해당 ID로 스크롤
                        if selected_chunk_id:
                            target_index = next((c['metadata']['index'] for c in all_chunks if c['chunk_id'] == selected_chunk_id), None)
                            if target_index is not None:
                                scroll_script = f"""
                                    <script>
                                        // Streamlit components run in an iframe, so we need to access the parent document
                                        setTimeout(function() {{
                                            try {{
                                                const element = window.parent.document.getElementById("chunk_{target_index}");
                                                if (element) {{
                                                    element.scrollIntoView({{ behavior: "smooth", block: "center" }});
                                                    // 시각적 피드백을 위해 잠시 깜빡임 효과 (선택 사항)
                                                    element.style.transition = "background-color 0.5s";
                                                    const originalBg = element.style.backgroundColor;
                                                    element.style.backgroundColor = "#fff9c4"; // 노란색 하이라이트
                                                    setTimeout(() => {{
                                                        element.style.backgroundColor = originalBg;
                                                    }}, 1500);
                                                }} else {{
                                                    console.log("Chunk element not found: chunk_{target_index}");
                                                }}
                                            }} catch (e) {{
                                                console.error("Scroll script error:", e);
                                            }}
                                        }}, 500);
                                    </script>
                                """
                                st.components.v1.html(scroll_script, height=0, width=0)
                    else:
                        # 뷰어가 비어있을 때 안내 메시지
                        st.info("👈 왼쪽 검색 결과에서 '📖 전체 문서 보기'를 클릭하면 여기에 문서 전체가 표시됩니다.")
        else:
            st.markdown(WELCOME_HTML, unsafe_allow_html=True)
    
    # ===== TAB 2: AI 질문하기 =====
    with tab2:
        st.markdown("### 💬 AI에게 질문하기")
        
        # 검색 탭에서 검색어 가져오기
        if 'qa_question' in st.session_state and st.session_state.qa_question:
            initial_question = st.session_state.qa_question
        elif 'search_input' in st.session_state and st.session_state.search_input:
            initial_question = st.session_state.search_input
        else:
            initial_question = ""
        
        # 설정 영역 (접을 수 있음)
        with st.expander("⚙️ AI 설정", expanded=not st.session_state.get('qa_configured', False)):
            st.caption("AI 제공자와 API 키를 설정하세요")
            
            # AI 제공자 및 모델 선택
            col1, col2 = st.columns(2)
            
            with col1:
                provider = st.selectbox(
                    "AI 제공자",
                    ["OpenAI", "Gemini"],
                    help="사용할 AI 서비스를 선택하세요",
                    key="qa_provider"
                )
            
            with col2:
                if provider == "OpenAI":
                    model_options = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
                    default_model = "gpt-4o-mini"
                else:
                    model_options = ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"]
                    default_model = "gemini-2.0-flash-exp"
                
                model_name = st.selectbox(
                    "모델 선택",
                    model_options,
                    index=model_options.index(default_model),
                    help="사용할 AI 모델을 선택하세요",
                    key="qa_model"
                )
            
            # API 키 입력
            api_key = st.text_input(
                f"{provider} API 키",
                type="password",
                placeholder=f"{'sk-...' if provider == 'OpenAI' else 'AI...'} 형식의 API 키를 입력하세요",
                help=f"{'https://platform.openai.com/api-keys' if provider == 'OpenAI' else 'https://aistudio.google.com/app/apikey'}에서 발급받으세요",
                key="qa_api_key"
            )
            
            # 설정 완료 버튼
            if st.button("✅ 설정 완료", use_container_width=True):
                if api_key:
                    st.session_state['qa_configured'] = True
                    st.success("설정이 완료되었습니다!")
                    st.rerun()
                else:
                    st.error("API 키를 입력해주세요.")
        
        # 설정 상태 표시
        if st.session_state.get('qa_configured', False):
            st.success(f"✅ 설정 완료: {st.session_state.get('qa_provider', 'OpenAI')} - {st.session_state.get('qa_model', 'gpt-4o-mini')}")
        
        # 질문 입력 (더 큰 영역)
        question = st.text_area(
            "질문 입력",
            value=initial_question,
            placeholder="예: 돈까스 레시피에서 중요한 온도는?",
            height=120,
            help="검색 탭에서 검색한 내용이 자동으로 입력됩니다",
            key="qa_question"
        )
        
        # 답변 받기 버튼
        col_btn1, col_btn2 = st.columns([3, 1])
        with col_btn1:
            ask_button = st.button("🤖 답변 받기", use_container_width=True, type="primary")
        with col_btn2:
            if st.button("🔄 초기화", use_container_width=True):
                st.session_state['qa_question'] = ""
                st.rerun()
        
        if ask_button:
            # API 키 확인
            current_api_key = st.session_state.get('qa_api_key', '')
            current_provider = st.session_state.get('qa_provider', 'OpenAI')
            current_model = st.session_state.get('qa_model', 'gpt-4o-mini')
            
            if not current_api_key:
                st.error("⚙️ 위의 'AI 설정'에서 API 키를 입력해주세요.")
            elif not question:
                st.warning("질문을 입력해주세요.")
            else:
                # 질문 이력에 추가 (중복 제거)
                if question not in st.session_state['qa_history']:
                    st.session_state['qa_history'].append(question)
                    # 최대 20개까지만 저장
                    if len(st.session_state['qa_history']) > 20:
                        st.session_state['qa_history'].pop(0)
                    save_history(st.session_state['qa_history'])  # 파일에 저장
                
                with st.spinner("🤔 AI가 답변을 생성하는 중..."):
                    results = searcher.search(question, top_k=3)
                    
                    if not results or results[0]['score'] < 0.1:
                        st.warning("😕 관련된 문서를 찾지 못했습니다. 다른 질문으로 시도해보세요.")
                    else:
                        # 캐시 확인
                        cache_key = question.strip()
                        if cache_key in st.session_state['qa_cache']:
                            answer = st.session_state['qa_cache'][cache_key]
                            error = None
                            st.info("⚡ 이전에 답변한 내용입니다 (캐시됨)")
                        else:
                            answer, error = get_ai_answer(question, results, current_provider, current_api_key, current_model)
                            
                            # 새 답변 캐시에 저장
                            if answer and not error:
                                st.session_state['qa_cache'][cache_key] = answer
                                save_qa_cache(st.session_state['qa_cache'])
                        
                        if error:
                            st.error(error)
                        elif answer:
                            # 답변 표시
                            st.markdown(f"""
                            <div class="answer-box">
                                <h3>🤖 AI 답변 ({current_provider} - {current_model})</h3>
                                <div class="answer-content">{answer}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # 참고 문서 표시
                            with st.expander("📚 참고한 문서 보기"):
                                for i, doc in enumerate(results):
                                    st.markdown(f"**[문서 {i+1}] {doc['doc_id']}**")
                                    st.text(doc['text'][:200] + "...")
                                    st.markdown("---")

if __name__ == "__main__":
    main()
