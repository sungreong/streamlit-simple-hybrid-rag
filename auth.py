import streamlit as st
import hashlib

def hash_password(password: str) -> str:
    """해시 함수를 사용하여 비밀번호를 암호화합니다."""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password() -> bool:
    """
    비밀번호 인증을 처리합니다.
    Returns:
        bool: 인증 성공 여부
    """
    
    # 세션 상태 초기화
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    # 이미 인증된 경우
    if st.session_state.authenticated:
        return True
    
    # 로그인 UI
    st.markdown("""
        <div style="text-align: center; padding: 50px 0;">
            <h1 style="color: #6366f1;">🔐 AI Hybrid Search System</h1>
            <p style="color: #6b7280; font-size: 1.1rem;">접근하려면 비밀번호를 입력하세요</p>
        </div>
    """, unsafe_allow_html=True)
    
    # 중앙 정렬을 위한 컬럼
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            password = st.text_input(
                "비밀번호",
                type="password",
                placeholder="비밀번호를 입력하세요",
                help="관리자로부터 받은 비밀번호를 입력하세요"
            )
            submit = st.form_submit_button("로그인", use_container_width=True)
            
            if submit:
                # secrets.toml에서 비밀번호 가져오기
                try:
                    correct_password = st.secrets["password"]
                    
                    # 비밀번호 검증 (해시 비교)
                    if hash_password(password) == correct_password:
                        st.session_state.authenticated = True
                        st.success("✅ 로그인 성공!")
                        st.rerun()
                    else:
                        st.error("❌ 비밀번호가 올바르지 않습니다.")
                except KeyError:
                    st.error("⚠️ 시스템 설정 오류: secrets.toml 파일을 확인하세요.")
                except Exception as e:
                    st.error(f"⚠️ 오류 발생: {str(e)}")
    
    return False

def logout():
    """로그아웃 처리"""
    st.session_state.authenticated = False
    st.rerun()

def show_logout_button():
    """사이드바에 로그아웃 버튼 표시"""
    with st.sidebar:
        st.markdown("---")
        if st.button("🚪 로그아웃", use_container_width=True):
            logout()
