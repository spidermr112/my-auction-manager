import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import re

# 1. 페이지 설정 및 [세련된 캡슐형 내비게이션] CSS
st.set_page_config(page_title="페이지부동산", page_icon="📄", layout="wide")

st.markdown("""
    <style>
    /* 전체적인 디자인 톤앤매너 */
    .stApp { background-color: #fcfcfc; }
    
    /* 캡슐형 내비게이션 바 디자인 */
    div[data-testid="stHorizontalBlock"]:has(.nav-marker) {
        background: #ffffff !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 50px !important;
        padding: 5px 15px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
        width: fit-content !important;
        margin: 20px auto !important;
        display: flex !important;
        align-items: center !important;
        gap: 0px !important;
    }
    
    /* 컬럼 간격 제거 */
    div[data-testid="stHorizontalBlock"]:has(.nav-marker) > div[data-testid="column"] {
        flex: 0 0 auto !important;
        width: auto !important;
        min-width: 0 !important;
    }

    /* 내비게이션 버튼 스타일 */
    .stButton > button[key^="btn_nav_"] {
        border: none !important;
        background: transparent !important;
        color: #444 !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        padding: 8px 16px !important;
        transition: all 0.2s !important;
    }
    
    .stButton > button[key^="btn_nav_"]:hover {
        color: #007AFF !important;
        transform: scale(1.1);
    }

    /* 중앙 숫자 카운터 */
    .nav-counter {
        background: #f1f3f5;
        padding: 4px 14px;
        border-radius: 20px;
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        color: #1a1a1a;
        font-size: 16px;
        margin: 0 10px;
        min-width: 60px;
        text-align: center;
    }
    
    /* 메모 저장 버튼 전용 스타일 */
    .stButton > button[key^="save_slide_"] {
        background-color: #f8f9fa !important;
        border: 1px solid #dee2e6 !important;
        color: #495057 !important;
        border-radius: 8px !important;
    }

    .nav-marker { display: none; }
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

# 2. 검색 및 필터 (생략/기존 유지)
# ... [검색 필터 및 데이터 에디터 코드 영역] ...

# 필터링 로직 수행 (가정)
df_filtered = df_list.copy() # 실제로는 필터 조건이 적용된 데이터여야 함

# --- 3. [개선된 상세 브리핑 영역] ---
if not df_filtered.empty:
    st.markdown("---")
    st.subheader("📋 매물 상세 브리핑")

    if "current_idx" not in st.session_state:
        st.session_state.current_idx = 0

    filtered_indices = df_filtered.index.tolist()
    total_count = len(filtered_indices)
    
    if st.session_state.current_idx >= total_count:
        st.session_state.current_idx = 0

    item = df_filtered.loc[filtered_indices[st.session_state.current_idx]]
    
    # [A. 상세 정보 카드]
    with st.container(border=True):
        st.info(f"📍 **{item['소재지']}**")
        sc1, sc2 = st.columns(2)
        with sc1:
            st.write(f"🏠 **종류:** {item['소분류']} ({item['상태']})")
            st.write(f"💰 **가액:** {item['가액']} / {item['월세']}")
        with sc2:
            st.write(f"📏 **면적:** {item['면적']}")
            st.write(f"👤 **고객:** {item['고객명']}")
        
        st.write(f"📞 **연락처:** {item['연락처']}")
        st.markdown("**📜 상세 메모**")
        
        # [B. 메모장]
        new_memo = st.text_area("내용 수정", value=item['특약사항'], height=200, key=f"memo_slide_{item.name}", label_visibility="collapsed")
        
        # [C. 위치 변경: 내비게이션 바가 메모 저장 버튼 위로!]
        nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])
        with nav_col1:
            st.markdown('<div class="nav-marker"></div>', unsafe_allow_html=True)
            if st.button("이전", key="btn_nav_prev", use_container_width=True):
                st.session_state.current_idx = (st.session_state.current_idx - 1) % total_count
                st.rerun()
        with nav_col2:
            st.markdown(f"<div class='nav-counter'>{st.session_state.current_idx + 1} / {total_count}</div>", unsafe_allow_html=True)
        with nav_col3:
            if st.button("다음", key="btn_nav_next", use_container_width=True):
                st.session_state.current_idx = (st.session_state.current_idx + 1) % total_count
                st.rerun()

        # [D. 위치 변경: 메모 저장 버튼을 가장 하단으로]
        if st.button("💾 메모 내용 저장하기", key=f"save_slide_{item.name}", use_container_width=True):
            df_list.at[item.name, '특약사항'] = new_memo
            conn.update(data=df_list)
            st.success("메모가 저장되었습니다!")
            st.rerun()
