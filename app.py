import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

# 1. 브라우저 기본 설정 (탭 이름과 아이콘)
st.set_page_config(
    page_title="파크부동산",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. 모바일 앱 설정 및 스타일 (화면에서 보이지 않게 처리)
components.html(
    """
    <script>
        // iOS 앱 제목 설정
        var meta = document.createElement('meta');
        meta.name = "apple-mobile-web-app-title";
        meta.content = "파크부동산";
        document.getElementsByTagName('head')[0].appendChild(meta);
        
        // 홈 화면 추가 시 전체화면 실행 설정
        var meta2 = document.createElement('meta');
        meta2.name = "apple-mobile-web-app-capable";
        meta2.content = "yes";
        document.getElementsByTagName('head')[0].appendChild(meta2);

        // 안드로이드 앱 이름 설정
        var meta3 = document.createElement('meta');
        meta3.name = "application-name";
        meta3.content = "파크부동산";
        document.getElementsByTagName('head')[0].appendChild(meta3);
    </script>
    """,
    height=0, # 높이를 0으로 해서 화면에서 안 보이게 합니다.
)

# CSS 스타일 (폰트 및 버튼 디자인)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
        html, body, [class*="css"] {
            font-family: 'Noto Sans KR', sans-serif;
        }
        .stButton>button {
            width: 100%;
            border-radius: 10px;
            background-color: #FF4B4B;
            color: white;
            font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)

# --- 이하 본문 내용은 동일 ---
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.write("# 🏠")
with col_title:
    st.title("파크부동산")

# 매물 등록 섹션
with st.expander("➕ 매물 등록하기", expanded=False):
    with st.form("listing_form"):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("접수일", datetime.now())
            purpose = st.radio("의뢰목적", ["매도/의뢰", "구함"], horizontal=True)
            category = st.selectbox("물건대분류", ["주거용", "비주거용"])
        with col2:
            manage_num = st.text_input("관리번호", placeholder="면적 입력(평 또는 ㎡)")
            trade_type = st.radio("거래 구분", ["매매", "전세", "월세"], horizontal=True)
            address = st.text_input("소재지 상세", placeholder="동/호수까지 입력")
        price = st.number_input("가격/보증금 (만원)", min_value=0, step=100)
        memo = st.text_area("특약내용/메모")
        submitted = st.form_submit_button("💾 데이터베이스 저장")

st.divider()

# 검색 및 목록 (예시용 데이터)
st.subheader("🔍 매물 필터링 / 검색")
st.text_input("검색어 입력", placeholder="주소 또는 메모 검색")

if 'listings' not in st.session_state:
    st.session_state.listings = pd.DataFrame(columns=["상태", "의뢰목적", "소분류", "상세 주소", "가격(만)"])

st.subheader(f"📋 매물 목록 관리 ({len(st.session_state.listings)}건)")
st.dataframe(st.session_state.listings, use_container_width=True, hide_index=True)

st.caption("파크부동산 전용 매물관리 시스템 | v1.3 (클린 업데이트)")
