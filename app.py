import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 브라우저 설정 및 앱 아이콘/이름 설정
st.set_page_config(
    page_title="파크부동산",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. 모바일 앱 환경 설정 (홈 화면 추가 시 자동 이름/아이콘 지정)
st.markdown("""
    <head>
        <meta name="apple-mobile-web-app-title" content="파크부동산">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="default">
        <link rel="apple-touch-icon" href="https://img.icons8.com/fluency/144/home.png">
        
        <meta name="mobile-web-app-capable" content="yes">
        <meta name="application-name" content="파크부동산">
        <link rel="icon" sizes="192x192" href="https://img.icons8.com/fluency/192/home.png">
    </head>
    <style>
        /* 폰트 및 UI 깔끔하게 조정 */
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
        html, body, [class*="css"] {
            font-family: 'Noto Sans KR', sans-serif;
        }
        .main {
            background-color: #f8f9fa;
        }
        .stButton>button {
            width: 100%;
            border-radius: 10px;
            height: 3em;
            background-color: #FF4B4B;
            color: white;
            font-weight: bold;
            border: none;
        }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 관리 (세션 스테이트)
if 'listings' not in st.session_state:
    st.session_state.listings = pd.DataFrame(columns=[
        "상태", "의뢰목적", "소분류", "구분", "상세 주소", "면적", "가격(만)"
    ])

# --- 헤더 섹션 ---
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.write("# 🏠")
with col_title:
    st.title("파크부동산")

# --- 매물 등록 섹션 ---
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
        memo = st.text_area("특약내용/메모", placeholder="특징, 비빌번호, 채광 등 상세내용 입력")
        
        submitted = st.form_submit_button("💾 데이터베이스 저장")
        if submitted:
            # 임시 데이터 추가 로직
            new_data = {
                "상태": "진행중",
                "의뢰목적": trade_type,
                "소분류": category,
                "구분": "매매",
                "상세 주소": address,
                "면적": manage_num,
                "가격(만)": price
            }
            st.session_state.listings = pd.concat([st.session_state.listings, pd.DataFrame([new_data])], ignore_index=True)
            st.success("매물이 성공적으로 저장되었습니다!")

st.divider()

# --- 검색 및 필터 섹션 ---
st.subheader("🔍 매물 필터링 / 검색")
f_col1, f_col2 = st.columns(2)
with f_col1:
    status_filter = st.multiselect("상태 선택", ["진행중", "보류", "계약완료"], default=["진행중", "보류"])
with f_col2:
    type_filter = st.multiselect("대분류 선택", ["주거용", "비주거용", "토지"], default=["주거용", "비주거용"])

btn_col1, btn_col2 = st.columns([4, 1])
with btn_col1:
    search_query = st.text_input("검색어 입력", placeholder="주소 또는 메모 검색")
with btn_col2:
    st.write("##")
    if st.button("🔄 초기화"):
        st.rerun()

# --- 목록 관리 섹션 ---
st.subheader(f"📋 매물 목록 관리 ({len(st.session_state.listings)}건)")
st.dataframe(st.session_state.listings, use_container_width=True, hide_index=True)

# 하단 정보
st.caption("파크부동산 전용 매물관리 시스템 | v1.2 (모바일 앱 최적화)")
