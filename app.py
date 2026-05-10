import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import re

# 1. 페이지 설정 및 [미니멀 콤팩트 UI] CSS
st.set_page_config(page_title="페이지부동산", page_icon="📄", layout="wide")

st.markdown("""
    <style>
    /* 1. 내비게이션 바: 가로/세로 폭 극소화 및 중앙 정렬 */
    div[data-testid="stHorizontalBlock"]:has(.nav-marker) {
        display: flex !important;
        flex-direction: row !important;
        justify-content: center !important;
        align-items: center !important;
        gap: 0px !important;
        width: fit-content !important; /* 가로폭 최소화 */
        margin: 5px auto !important;   /* 위아래 여백 최소화 */
        padding: 0 !important;
    }
    
    /* 2. 각 요소(버튼, 숫자) 사이의 간격 제거 */
    div[data-testid="stHorizontalBlock"]:has(.nav-marker) > div[data-testid="column"] {
        flex: 0 0 auto !important;
        width: auto !important;
        min-width: 0 !important;
        padding: 0 !important;
    }

    /* 3. 내비게이션 버튼: 작고 정교한 디자인 */
    .stButton > button[key^="btn_nav_"] {
        border: 1px solid #e0e0e0 !important;
        background: white !important;
        color: #444 !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        height: 32px !important; /* 높이 축소 */
        padding: 0 12px !important;
        border-radius: 6px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
        transition: all 0.2s !important;
    }
    
    .stButton > button[key^="btn_nav_"]:hover {
        border-color: #007AFF !important;
        color: #007AFF !important;
        background-color: #f8fbff !important;
    }

    /* 4. 중앙 숫자: 가독성을 높인 슬림 폰트 */
    .nav-counter {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        color: #1a1a1a;
        font-size: 14px;
        line-height: 32px;
        padding: 0 12px;
        text-align: center;
    }
    
    .nav-marker { display: none; }
    
    /* 5. 메모 저장 버튼: 하단에 차분하게 배치 */
    .stButton > button[key^="save_slide_"] {
        margin-top: 5px !important;
        height: 38px !important;
        border-radius: 8px !important;
        font-size: 14px !important;
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

# --- 3. [상세 브리핑 영역] ---
df_filtered = df_list.copy() # 예시용 (실제로는 필터 로직 반영)

if not df_filtered.empty:
    st.markdown("---")
    st.subheader("📋 매물 상세 브리핑")

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
            st.write(f"🏠 **분류:** {item['소분류']} ({item['상태']})")
            st.write(f"💰 **가액:** {item['가액']} / {item['월세']}")
        with sc2:
            st.write(f"📏 **면적:** {item['면적']}")
            st.write(f"👤 **고객:** {item['고객명']}")
        
        st.write(f"📞 **연락처:** {item['연락처']}")
        st.markdown("**📜 상세 메모**")
        
        # 1. 메모장
        new_memo = st.text_area("내용 수정", value=item['특약사항'], height=180, key=f"memo_slide_{item.name}", label_visibility="collapsed")
        
        # 2. [디자인 개선] 슬림 내비게이션 바 (메모장 바로 아래)
        nav_c1, nav_c2, nav_c3 = st.columns([1, 1, 1])
        with nav_c1:
            st.markdown('<div class="nav-marker"></div>', unsafe_allow_html=True)
            if st.button("◀ 이전", key="btn_nav_prev"):
                st.session_state.current_idx = (st.session_state.current_idx - 1) % total
                st.rerun()
        with nav_c2:
            st.markdown(f"<div class='nav-counter'>{st.session_state.current_idx + 1} / {total}</div>", unsafe_allow_html=True)
        with nav_c3:
            if st.button("다음 ▶", key="btn_nav_next"):
                st.session_state.current_idx = (st.session_state.current_idx + 1) % total
                st.rerun()

        # 3. [위치 변경] 메모 저장 버튼 (최하단)
        if st.button("💾 메모 내용 저장하기", key=f"save_slide_{item.name}", use_container_width=True):
            df_list.at[item.name, '특약사항'] = new_memo
            conn.update(data=df_list)
            st.toast("메모 저장 완료!")
            st.rerun()
