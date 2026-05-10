import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import re

# 1. 페이지 설정 및 [슬림 가로 캡슐] CSS
st.set_page_config(page_title="페이지부동산", page_icon="📄", layout="wide")

st.markdown("""
    <style>
    /* 1. 슬림 가로 내비게이션 바 */
    div[data-testid="stHorizontalBlock"]:has(.nav-marker) {
        background: #f8f9fa !important;
        border-radius: 12px !important;
        padding: 2px 10px !important; /* 세로 패딩 극소화 */
        margin: 5px auto !important;   /* 위아래 간격 축소 */
        display: flex !important;
        flex-direction: row !important;
        justify-content: center !important;
        align-items: center !important;
        width: fit-content !important;
        border: 1px solid #e0e0e0 !important;
    }
    
    /* 2. 각 요소(버튼, 숫자)를 한 줄로 강제 고정 */
    div[data-testid="stHorizontalBlock"]:has(.nav-marker) > div[data-testid="column"] {
        flex: 0 0 auto !important;
        width: auto !important;
        min-width: 0 !important;
        padding: 0 !important;
    }

    /* 3. 내비게이션 버튼 슬림화 */
    .stButton > button[key^="btn_nav_"] {
        border: none !important;
        background: transparent !important;
        color: #007AFF !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        height: 32px !important; /* 높이 고정 */
        padding: 0 15px !important;
        margin: 0 !important;
    }
    
    /* 4. 중앙 숫자 디자인 */
    .nav-counter {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: #333;
        font-size: 14px;
        padding: 0 10px;
        min-width: 50px;
        text-align: center;
        line-height: 32px; /* 버튼 높이와 맞춤 */
    }

    /* 5. 하단 메모 저장 버튼도 슬림하게 */
    .stButton > button[key^="save_slide_"] {
        margin-top: -10px !important;
        font-size: 13px !important;
        height: 35px !important;
    }

    .nav-marker { display: none; }
    </style>
""", unsafe_allow_html=True)

st.title("📄 페이지부동산 매물 관리 시스템")

# --- [데이터 연결 로직 기존 유지] ---
conn = st.connection("gsheets", type=GSheetsConnection)
def load_data():
    try:
        data = conn.read(ttl=0)
        data = data.dropna(how='all').fillna("")
        return data
    except Exception:
        return pd.DataFrame(columns=["접수일", "고객명", "연락처", "대분류", "소분류", "면적", "가액", "월세", "상태", "소재지", "특약사항"])

df_list = load_data()
df_filtered = df_list.copy() # 실제로는 필터링 결과 적용

# --- 3. [상세 브리핑 영역] ---
if not df_filtered.empty:
    st.markdown("---")
    st.subheader("📋 매물 상세 브리핑")

    if "current_idx" not in st.session_state:
        st.session_state.current_idx = 0

    indices = df_filtered.index.tolist()
    total = len(indices)
    st.session_state.current_idx %= total
    item = df_filtered.loc[indices[st.session_state.current_idx]]
    
    # [상세 정보 카드]
    with st.container(border=True):
        st.info(f"📍 **{item['소재지']}**")
        sc1, sc2 = st.columns(2)
        with sc1:
            st.write(f"🏠 {item['소분류']} ({item['상태']})")
            st.write(f"💰 {item['가액']} / {item['월세']}")
        with sc2:
            st.write(f"📏 {item['면적']}")
            st.write(f"👤 {item['고객명']}")
        
        # [메모장]
        new_memo = st.text_area("상세 메모", value=item['특약사항'], height=180, key=f"memo_{item.name}", label_visibility="collapsed")
        
        # [가로형 슬림 내비게이션 바]
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
            df_list.at[item.name, '특약사항'] = new_memo
            conn.update(data=df_list)
            st.toast("메모 저장 완료!")
            st.rerun()
