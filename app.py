import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

# 1. 브라우저 설정 (탭 이름 및 아이콘)
st.set_page_config(
    page_title="파크부동산",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. 모바일 앱 설정 (홈 화면 추가 시 자동 이름/아이콘 지정 - 화면 노출 없음)
components.html(
    """
    <script>
        var meta1 = document.createElement('meta');
        meta1.name = "apple-mobile-web-app-title";
        meta1.content = "파크부동산";
        document.getElementsByTagName('head')[0].appendChild(meta1);
        
        var meta2 = document.createElement('meta');
        meta2.name = "apple-mobile-web-app-capable";
        meta2.content = "yes";
        document.getElementsByTagName('head')[0].appendChild(meta2);

        var meta3 = document.createElement('meta');
        meta3.name = "application-name";
        meta3.content = "파크부동산";
        document.getElementsByTagName('head')[0].appendChild(meta3);
    </script>
    """,
    height=0,
)

# UI 스타일 설정
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
        html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
        .stButton>button { width: 100%; border-radius: 10px; background-color: #FF4B4B; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 관리 (세션 상태 초기화)
if 'listings' not in st.session_state:
    # 초기 예시 데이터 (테스트용)
    st.session_state.listings = pd.DataFrame([
        {"상태": "진행중", "의뢰목적": "매매", "소분류": "주거용", "구분": "아파트", "상세 주소": "서울시 강남구", "면적": "84㎡", "가격(만)": 150000, "메모": "채광 좋음"},
        {"상태": "보류", "의뢰목적": "월세", "소분류": "비주거용", "구분": "상가", "상세 주소": "경기도 성남시", "면적": "33㎡", "가격(만)": 500, "메모": "역세권"}
    ])

# --- 헤더 ---
st.title("🏠 파크부동산")

# --- 매물 등록 섹션 ---
with st.expander("➕ 매물 등록하기", expanded=False):
    with st.form("listing_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("접수일", datetime.now())
            purpose = st.radio("의뢰목적", ["매도/의뢰", "구함"], horizontal=True)
            category = st.selectbox("물건대분류", ["주거용", "비주거용", "토지"])
        with col2:
            manage_num = st.text_input("면적/관리번호", placeholder="예: 84㎡ / 101호")
            trade_type = st.radio("거래 구분", ["매매", "전세", "월세"], horizontal=True)
            address = st.text_input("소재지 상세", placeholder="상세 주소 입력")
            
        price = st.number_input("가격/보증금 (만원)", min_value=0, step=100)
        memo = st.text_area("특약내용/메모")
        
        submitted = st.form_submit_button("💾 데이터베이스 저장")
        if submitted:
            new_data = {
                "상태": "진행중",
                "의뢰목적": trade_type,
                "소분류": category,
                "구분": purpose,
                "상세 주소": address,
                "면적": manage_num,
                "가격(만)": price,
                "메모": memo
            }
            st.session_state.listings = pd.concat([st.session_state.listings, pd.DataFrame([new_data])], ignore_index=True)
            st.success("매물이 저장되었습니다!")
            st.rerun()

st.divider()

# --- 검색 및 필터 섹션 (이 부분이 핵심!) ---
st.subheader("🔍 매물 필터링 / 검색")
f_col1, f_col2 = st.columns(2)

with f_col1:
    status_filter = st.multiselect("상태 선택", ["진행중", "보류", "계약완료"], default=["진행중", "보류"])
with f_col2:
    category_filter = st.multiselect("대분류 선택", ["주거용", "비주거용", "토지"], default=["주거용", "비주거용", "토지"])

search_query = st.text_input("🔍 검색어 입력", placeholder="주소 또는 메모 내용으로 검색")

# 필터링 로직 적용
df_display = st.session_state.listings.copy()

if status_filter:
    df_display = df_display[df_display["상태"].isin(status_filter)]
if category_filter:
    df_display = df_display[df_display["소분류"].isin(category_filter)]
if search_query:
    df_display = df_display[
        df_display["상세 주소"].str.contains(search_query, na=False) | 
        df_display["메모"].str.contains(search_query, na=False)
    ]

# --- 목록 관리 섹션 ---
st.subheader(f"📋 매물 목록 관리 ({len(df_display)}건)")
st.dataframe(df_display, use_container_width=True, hide_index=True)

if st.button("🔄 전체 목록 새로고침"):
    st.rerun()

st.caption("파크부동산 전용 매물관리 시스템 | v1.4 (필터 및 데이터 복구 완료)")
