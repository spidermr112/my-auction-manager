import streamlit as st
import pandas as pd
from datetime import datetime
import re

# 1. 페이지 설정
st.set_page_config(page_title="파크부동산 통합 관리 시스템", page_icon="🏘️", layout="wide")
st.title("🏘️ 파크부동산 통합 관리 시스템")

# --- [데이터 및 로직 정의] ---
category_map = {
    "주거용": ["아파트", "연립/다세대", "단독/다가구", "전원주택", "오피스텔(주거)"],
    "비주거용": ["상가/사무실", "빌딩/건물", "공장/창고", "지식산업센터", "숙박시설"],
    "토지": ["대지", "전/답/과수원", "임야", "잡종지", "기타토지"]
}

# 세션 상태 초기화 (연동 계산용)
if 'land_price' not in st.session_state: st.session_state.land_price = 0 # 거래가액
if 'py_price' not in st.session_state: st.session_state.py_price = 0     # 평단가
if 'land_area' not in st.session_state: st.session_state.land_area = 0.0  # 면적(평)

# --- [연동 계산 함수] ---
def update_by_total(): # 거래가액 수정 시 평단가 재계산
    if st.session_state.land_area > 0:
        st.session_state.py_price = int(st.session_state.land_price / st.session_state.land_area)

def update_by_py_price(): # 평단가 수정 시 거래가액 재계산
    st.session_state.land_price = int(st.session_state.py_price * st.session_state.land_area)

def update_by_area(): # 면적 수정 시 거래가액 재계산
    st.session_state.land_price = int(st.session_state.py_price * st.session_state.land_area)

# 2. 새 매물 등록 섹션
with st.expander("➕ 새 매물 등록하기 (클릭하여 입력창 열기)", expanded=False):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.date_input("접수일", datetime.today())
        main_cat = st.radio("물건 대분류", list(category_map.keys()), horizontal=True)
        st.radio("의뢰목적", ["매도", "임대", "매수", "임차"], horizontal=True)
    
    with col2:
        st.selectbox("물건 소분류", category_map[main_cat])
        st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        
        if main_cat == "토지":
            # [토지 전용] 평단가 입력 (수정 시 거래가액 연동)
            st.number_input("평단가 (만원)", key="py_price", min_value=0, step=10, on_change=update_by_py_price)
            # [토지 전용] 거래가액 입력 (수정 시 평단가 연동)
            st.number_input("거래가액 (만원)", key="land_price", min_value=0, step=100, on_change=update_by_total)
        else:
            # [일반] 거래가액 입력
            st.number_input("거래가액 (만원 단위)", min_value=0, step=100, format="%d")
        
    with col3:
        st.text_input("소재지 상세")
        
        if main_cat == "토지":
            # [토지 전용] 면적 입력 (평 단위, 수정 시 거래가액 연동)
            st.number_input("면적 (평)", key="land_area", min_value=0.0, step=0.1, format="%.2f", on_change=update_by_area)
        else:
            st.text_input("면적")
            
        st.text_area("특약내용", height=68)
        
    if st.button("🏠 데이터베이스 저장", use_container_width=True):
        st.success(f"저장 완료: 거래가액 {st.session_state.land_price:,}만원 / 평단가 {st.session_state.py_price:,}만원")

st.divider()

# 3. 검색 및 매물 목록 (기존 로직 유지)
st.text_input("🔍 키워드 검색", placeholder="검색어를 입력하세요.")

# 임시 데이터 표시용
df_display = pd.DataFrame({
    "접수일": [datetime.today().strftime("%Y-%m-%d")],
    "대분류": [main_cat],
    "소분류": [category_map[main_cat][0]],
    "가액": [st.session_state.land_price if main_cat == "토지" else 0],
    "주소": ["샘플 주소"],
    "면적": [f"{st.session_state.land_area}평" if main_cat == "토지" else "미입력"]
})

st.subheader(f"📊 매물 목록 (조회 결과: {len(df_display)}건)")
st.dataframe(
    df_display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "가액": st.column_config.NumberColumn("가액(만원)", format="%d 만원")
    }
)

# 4. 다운로드 버튼
csv = df_display.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 목록 다운로드 (CSV)", csv, "real_estate.csv", "text/csv")
