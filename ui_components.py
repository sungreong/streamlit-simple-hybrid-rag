"""
UI 스타일 및 컴포넌트 모듈
"""

# CSS 스타일
APP_STYLES = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%);
    }
    
    .result-card {
        background: white;
        padding: 20px 25px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 15px;
        border-left: 4px solid #6366f1;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    
    .result-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.12);
        transform: translateY(-2px);
    }
    
    .relevance-high { border-left-color: #10b981; }
    .relevance-medium { border-left-color: #f59e0b; }
    .relevance-low { border-left-color: #6b7280; }
    
    .relevance-badge {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 10px;
    }
    
    .badge-high { background-color: #d1fae5; color: #065f46; }
    .badge-medium { background-color: #fef3c7; color: #92400e; }
    .badge-low { background-color: #f3f4f6; color: #374151; }
    
    .doc-title {
        font-size: 0.75rem;
        color: #6b7280;
        margin-bottom: 8px;
    }
    
    .doc-content {
        font-size: 0.9rem;
        line-height: 1.6;
        color: #1f2937;
    }
    
    .highlight {
        background-color: #fef08a;
        color: #1e3a8a;
        padding: 2px 4px;
        border-radius: 3px;
        font-weight: 600;
    }
    
    .answer-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 25px;
        border-radius: 12px;
        margin: 20px 0;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .answer-box h3 {
        margin-top: 0;
        color: white;
    }
    
    .answer-content {
        background: rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 8px;
        margin-top: 10px;
        line-height: 1.8;
        font-size: 0.95rem;
    }
    
    .doc-viewer {
        background: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        max-height: 70vh;
        overflow-y: auto;
        line-height: 1.6;
        font-size: 0.9rem;
    }
    
    .doc-viewer h1 {
        color: #1e3a8a;
        font-size: 1.3rem;
        font-weight: 700;
        border-bottom: 2px solid #e5e7eb;
        padding-bottom: 8px;
        margin-top: 20px;
        margin-bottom: 12px;
    }
    
    .doc-viewer h2 {
        color: #1e40af;
        font-size: 1.15rem;
        font-weight: 600;
        margin-top: 16px;
        margin-bottom: 10px;
    }
    
    .doc-viewer h3 {
        color: #3b82f6;
        font-size: 1.0rem;
        font-weight: 600;
        margin-top: 12px;
        margin-bottom: 8px;
    }
    
    .doc-viewer code {
        background-color: #f3f4f6;
        padding: 2px 6px;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        font-size: 0.9em;
        color: #dc2626;
    }
    
    .doc-viewer pre {
        background-color: #1f2937;
        color: #f9fafb;
        padding: 15px;
        border-radius: 8px;
        overflow-x: auto;
        margin: 15px 0;
    }
    
    .doc-viewer pre code {
        background: none;
        color: #f9fafb;
        padding: 0;
    }
    
    .doc-viewer ul, .doc-viewer ol {
        margin: 8px 0;
        padding-left: 25px;
    }
    
    .doc-viewer li {
        margin: 3px 0;
        line-height: 1.5;
    }
    
    .doc-viewer p {
        margin: 8px 0;
        line-height: 1.6;
    }
    
    .doc-viewer table {
        border-collapse: collapse;
        width: 100%;
        margin: 15px 0;
    }
    
    .doc-viewer th, .doc-viewer td {
        border: 1px solid #e5e7eb;
        padding: 10px;
        text-align: left;
    }
    
    .doc-viewer th {
        background-color: #f3f4f6;
        font-weight: 600;
    }
    
    .doc-viewer blockquote {
        border-left: 4px solid #6366f1;
        padding-left: 15px;
        margin: 15px 0;
        color: #6b7280;
        font-style: italic;
    }
    
    .doc-viewer a {
        color: #3b82f6;
        text-decoration: none;
    }
    
    .doc-viewer a:hover {
        text-decoration: underline;
    }
    
    .viewer-highlight {
        background-color: #dbeafe;
        border-left: 3px solid #3b82f6;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 6px;
    }
    
    .search-input {
        font-size: 1.1rem !important;
    }

    /* Q&A 참조 문서용 - 전체 요소 강제 축소 */
    .small-doc-content {
        font-size: 0.85rem !important;
        line-height: 1.4 !important;
    }
    
    .small-doc-content * {
        font-size: inherit !important; 
        line-height: inherit !important;
    }

    /* 제목은 본문보다 아주 살짝만 크게 */
    .small-doc-content h1 { font-size: 1.1em !important; margin: 8px 0 4px 0 !important; font-weight: 700 !important; }
    .small-doc-content h2 { font-size: 1.05em !important; margin: 6px 0 3px 0 !important; font-weight: 600 !important; }
    .small-doc-content h3 { font-size: 1.0em !important; margin: 5px 0 2px 0 !important; font-weight: 600 !important; }
    
    /* 여백 및 패딩 축소 */
    .small-doc-content p { margin: 3px 0 !important; }
    .small-doc-content ul, .small-doc-content ol { padding-left: 18px !important; margin: 3px 0 !important; }
    .small-doc-content li { margin: 1px 0 !important; }
    .small-doc-content blockquote { margin: 5px 0 !important; padding-left: 10px !important; font-size: 0.9em !important; }
    .small-doc-content pre { padding: 8px !important; margin: 5px 0 !important; }
    .small-doc-content code { font-size: 0.9em !important; }
    .small-doc-content table { margin: 5px 0 !important; font-size: 0.9em !important; }
    .small-doc-content th, .small-doc-content td { padding: 4px 8px !important; }
    </style>
"""

# Welcome 화면 HTML
WELCOME_HTML = """
<div style="background: white; padding: 50px; border-radius: 16px; text-align: center; margin-top: 80px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
    <h2 style="color: #6366f1; margin-bottom: 20px;">👋 환영합니다!</h2>
    <p style="color: #6b7280; font-size: 1.15rem; line-height: 1.8;">
        위 검색창에 궁금한 내용을 입력하면<br>
        관련된 문서를 자동으로 찾아드립니다.
    </p>
    <div style="margin-top: 40px; padding: 20px; background: #f9fafb; border-radius: 10px;">
        <p style="color: #374151; font-size: 0.95rem; margin: 0;">
            💡 <b>팁:</b> 핵심 단어로 검색하면 더 정확한 결과를 얻을 수 있습니다.
        </p>
    </div>
</div>
"""
