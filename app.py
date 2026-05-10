import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import re

# 1. 페이지 설정
st.set_page_config(page_title="페이지부동산", page_icon="📄", layout="wide")

# --- [디자인 최적화] 버튼을 양옆으로 띄우는 커스텀 CSS ---
st.markdown("""
    <style>
    /* 전체 상세 브리핑 영역 컨테이너 */
    .stElementContainer:has(.nav-button) {
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    /* 버튼 스타일 (투명하고 양옆에 고정) */
    div[data-testid="stColumn"] > div:has(button[key^="nav_"]) {
        position: fixed;
        top: 50%;
        transform: translateY(-50%);
        z-index: 999;
        opacity: 0.2; /* 평소엔 투명하게 */
        transition: opacity 0.3s;
    }
    
    /* 마우스 올리면 진해짐 (데스크톱 롤오버 효과) */
    div[data-testid="stColumn"]:hover > div:has(button[key^="nav_"]) {
        opacity: 1;
    }

    /* 왼쪽 버튼 위치 */
    div[data-testid="stColumn"]:has(button[key="nav_prev"]) {
        left: 20px;
    }
    
    /* 오른쪽 버튼 위치 */
    div[data-testid="stColumn"]:has(button[key="nav_next"]) {
        right: 20px;
    }

    /* 모바일에서는 버튼이 항상 보이도록 설정 */
    @media (max-width: 768px) {
        div[data-testid="stColumn"] > div:has(button[key^="nav_"]) {
            opacity: 0.8;
            position: relative; /* 모바일은 화면을 가릴 수 있으므로 위치 조정 */
            top: 0;
            transform: none;
        }
        div[data-testid="stColumn"]:has(button[key="nav_prev"]) { left: 0; }
        div[data-testid="stColumn"]:has(button[key="nav_next"]) { right: 0; }
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

# --- 필터 로직 (중략 방지를 위해 유지) ---
category_map = {
    "주거용": ["아파트", "연립/다세대", "단독/다가구", "전원주택", "오피스텔(주거)"], 
    "비주거용": ["상가", "사무실", "공장", "창고", "빌딩/건물", "지식산업센터", "숙박시설"], 
    "토지": ["대지", "전/답/과수원", "임야", "잡종지", "기타토지"]
}

# 2. 통합 필터 (한 줄 배치)
st.subheader("🔍 통합 검색 필터")
with st.container(border=True):
    c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])
    with c1: search_q = st.text_input("📍 검색어", placeholder="주소, 고객명...", key="f_search")
    with c2: f_main_cat = st.multiselect("🏗️ 종류", options=list(category_map.keys()), default=list(category_map.keys()), key="f_main")
    with c3: f_deal_type = st.multiselect("💰 거래", options=["매매", "전세", "월세"], default=["매매", "전세", "월세"], key="f_deal")
    with c4: status_list = st.multiselect("🚦 상태", options=["진행중", "완료", "보류", "삭제"], default=["진행중", "보류"], key="f_status")

df_filtered = df_list.copy()
if not df_filtered.empty:
    df_filtered = df_filtered[df_filtered['상태'].isin(status_list)]
    if '대분류' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['대분류'].isin(f_main_cat)]
    if search_q:
        df_filtered = df_filtered[df_filtered['소재지'].str.contains(search_q, na=False) | df_filtered['고객명'].str.contains(search_q, na=False)]

# 3. 목록 표시
st.subheader(f"📋 매물 목록 ({len(df_filtered)}건)")
st.data_editor(df_filtered, use_container_width=True, hide_index=False)

# --- 4. [핵심] 매물 상세 브리핑 슬라이드 시스템 ---
if not df_filtered.empty:
    st.markdown("---")
    st.subheader("📋 매물 상세 브리핑")

    if "current_idx" not in st.session_state:
        st.session_state.current_idx = 0

    filtered_indices = df_filtered.index.tolist()
    total_count = len(filtered_indices)
    
    # 인덱스 범위 초과 방지
    if st.session_state.current_idx >= total_count:
        st.session_state.current_idx = 0

    # 브리핑 내비게이션 바 (모바일 좌우 배치 최적화)
    # [◀️] [1 / 8] [▶️] 형태
    nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
    
    with nav_col1:
        if st.button("◀️ 이전", use_container_width=True, key="nav_prev"):
            st.session_state.current_idx = (st.session_state.current_idx - 1) % total_count
            st.rerun()

    with nav_col2:
        st.markdown(f"<h3 style='text-align: center; margin: 0;'>{st.session_state.current_idx + 1} / {total_count}</h3>", unsafe_allow_html=True)

    with nav_col3:
        if st.button("다음 ▶️", use_container_width=True, key="nav_next"):
            st.session_state.current_idx = (st.session_state.current_idx + 1) % total_count
            st.rerun()

    # 실제 매물 정보 카드
    item = df_filtered.loc[filtered_indices[st.session_state.current_idx]]
    
    with st.container(border=True):
        st.info(f"📍 **{item['소재지']}**")
        sc1, sc2 = st.columns(2)
        with sc1:
            st.write(f"🏠 **분류:** {item['소분류']}")
            st.write(f"💰 **가액:** {item['가액']} / {item['월세']}")
        with sc2:
            st.write(f"📏 **면적:** {item['면적']}")
            st.write(f"👤 **고객:** {item['고객명']} ({item['연락처']})")
        
        st.markdown("**📜 상세 메모**")
        st.text_area("내용", value=item['특약사항'], height=200, key=f"memo_{item.name}")
