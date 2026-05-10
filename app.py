import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import re

# 1. 페이지 설정 및 [초슬림 가로형] CSS 최적화
st.set_page_config(page_title="페이지부동산", page_icon="📄", layout="wide")

st.markdown("""
    <style>
    /* 1. 내비게이션 바: 세로 여백을 0에 가깝게 조절 */
    div[data-testid="stHorizontalBlock"]:has(.nav-marker) {
        display: flex !important;
        flex-direction: row !important;
        justify-content: center !important;
        align-items: center !important;
        gap: 2px !important;
        width: 100% !important;
        margin: -10px auto 5px auto !important; /* 위쪽 메모장과 바짝 밀착 */
        padding: 0 !important;
    }
    
    /* 2. 모바일에서 컬럼이 아래로 떨어지지 않게 강제 한 줄 고정 */
    div[data-testid="stHorizontalBlock"]:has(.nav-marker) > div[data-testid="column"] {
        flex: 1 1 auto !important;
        width: auto !important;
        min-width: 0 !important;
        padding: 0 !important;
        text-align: center !important;
    }

    /* 3. 내비게이션 버튼: 세로폭을 줄인 슬림 디자인 */
    .stButton > button[key^="btn_nav_"] {
        border: 1px solid #e0e0e0 !important;
        background: white !important;
        color: #333 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        height: 34px !important; /* 높이 축소 */
        padding: 0 10px !important;
        border-radius: 6px !important;
        width: 100% !important;
    }
    
    /* 4. 중앙 숫자: 버튼 높이와 일치시켜 밸런스 조정 */
    .nav-counter {
        font-weight: 700;
        color: #1a1a1a;
        font-size: 15px;
        line-height: 34px; /* 버튼 높이와 동일하게 */
        display: block;
    }
    
    .nav-marker { display: none; }
    
    /* 5. 메모 저장 버튼: 디자인 완성도 향상 */
    .stButton > button[key^="save_slide_"] {
        margin-top: 0px !important;
        height: 40px !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📄 페이지부동산 매물 관리 시스템")

# --- [데이터 연결] ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        data = conn.read(ttl=0)
        data = data.dropna(how='all').fillna("")
        num_cols = ["가액", "월세"]
        for col in num_cols:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0).astype(int)
        return data
    except Exception:
        return pd.DataFrame(columns=["접수일", "고객명", "연락처", "대분류", "소분류", "면적", "가액", "월세", "상태", "소재지", "특약사항"])

df_list = load_data()

# --- 초기화 기능 ---
def reset_all():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

category_map = {
    "주거용": ["아파트", "연립/다세대", "단독/다가구", "전원주택", "오피스텔(주거)"], 
    "비주거용": ["상가", "사무실", "공장", "창고", "빌딩/건물", "지식산업센터", "숙박시설"], 
    "토지": ["대지", "전/답/과수원", "임야", "잡종지", "기타토지"]
}

# --- 상단 필터 및 목록 생략 (기존 로직 유지) ---
df_filtered = df_list.copy() # 실제로는 상단 필터링 코드가 들어감

# --- 3. [상세 브리핑 영역] 최적화 배치 ---
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
        sc1, sc2 = st.columns(2)
        with sc1:
            st.write(f"🏠 {item['소분류']} ({item['상태']})")
            st.write(f"💰 {item['가액']} / {item['월세']}")
        with sc2:
            st.write(f"📏 {item['면적']}")
            st.write(f"👤 {item['고객명']}")
        
        # 1. 메모장
        new_memo = st.text_area("상세 메모", value=item['특약사항'], height=180, key=f"memo_{item.name}", label_visibility="collapsed")
        
        # 2. [슬림 가로 한 줄 내비게이션] - 메모장 바로 아래 배치
        nav_c1, nav_c2, nav_c3 = st.columns([1, 0.8, 1])
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

        # 3. [메모 저장 버튼] - 가장 하단 배치
        if st.button("💾 메모 내용 저장하기", key=f"save_slide_{item.name}", use_container_width=True):
            df_list.at[item.name, '특약사항'] = new_memo
            conn.update(data=df_list)
            st.toast("저장되었습니다!")
            st.rerun()
