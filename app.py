import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import re

# 1. 페이지 설정 및 [초슬림 한 줄] CSS
st.set_page_config(page_title="페이지부동산", page_icon="📄", layout="wide")

st.markdown("""
    <style>
    /* 1. 내비게이션 바 컨테이너: 배경 박스 제거 및 높이 최소화 */
    div[data-testid="stHorizontalBlock"]:has(.nav-marker) {
        display: flex !important;
        flex-direction: row !important;
        justify-content: center !important;
        align-items: center !important;
        gap: 5px !important;
        width: fit-content !important;
        margin: 5px auto !important; /* 위아래 간격 최소화 */
        padding: 0 !important;
    }
    
    /* 2. 각 요소 간격 제거 */
    div[data-testid="stHorizontalBlock"]:has(.nav-marker) > div[data-testid="column"] {
        flex: 0 0 auto !important;
        width: auto !important;
        min-width: 0 !important;
        padding: 0 !important;
    }

    /* 3. 버튼 디자인: 크기는 유지하되 외곽 여백 제거 */
    .stButton > button[key^="btn_nav_"] {
        border: 1px solid #e0e0e0 !important;
        background: white !important;
        color: #333 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        height: 36px !important;
        padding: 0 15px !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    }
    
    .stButton > button[key^="btn_nav_"]:hover {
        border-color: #007AFF !important;
        color: #007AFF !important;
    }

    /* 4. 중앙 숫자: 세로 폭에 맞춰 슬림하게 */
    .nav-counter {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        color: #1a1a1a;
        font-size: 15px;
        margin: 0 10px;
        line-height: 36px; /* 버튼 높이와 일치 */
    }
    
    /* 5. 불필요한 마커 숨김 */
    .nav-marker { display: none; }
    
    /* 6. 메모 저장 버튼 슬림화 */
    .stButton > button[key^="save_slide_"] {
        margin-top: 5px !important;
        height: 38px !important;
        border-radius: 8px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- [데이터 연결 및 로직 생략 - 기존 코드 유지] ---
conn = st.connection("gsheets", type=GSheetsConnection)
df_list = conn.read(ttl=0).dropna(how='all').fillna("")
df_filtered = df_list.copy() # 예시

# --- 3. [상세 브리핑 영역] ---
if not df_filtered.empty:
    st.markdown("---")
    if "current_idx" not in st.session_state:
        st.session_state.current_idx = 0

    indices = df_filtered.index.tolist()
    total = len(indices)
    st.session_state.current_idx %= total
    item = df_filtered.loc[indices[st.session_state.current_idx]]
    
    with st.container(border=True):
        st.info(f"📍 **{item['소재지']}**")
        # [정보 표시부 생략]
        
        # [메모장]
        new_memo = st.text_area("상세 메모", value=item['특약사항'], height=180, key=f"memo_{item.name}", label_visibility="collapsed")
        
        # [공간 절약형 가로 한 줄 내비게이션]
        nav_c1, nav_c2, nav_c3 = st.columns([1, 1, 1])
        with nav_c1:
            st.markdown('<div class="nav-marker"></div>', unsafe_allow_html=True)
            if st.button("이전", key="btn_nav_prev"):
                st.session_state.current_idx = (st.session_state.current_idx - 1) % total
                st.rerun()
        with nav_c2:
            st.markdown(f"<div class='nav-counter'>{st.session_state.current_idx + 1} / {total}</div>", unsafe_allow_html=True)
        with nav_c3:
            if st.button("다음", key="btn_nav_next"):
                st.session_state.current_idx = (st.session_state.current_idx + 1) % total
                st.rerun()

        # [메모 저장 버튼]
        if st.button("💾 메모 내용 저장하기", key=f"save_slide_{item.name}", use_container_width=True):
            # 저장 로직
            st.toast("저장되었습니다!")
