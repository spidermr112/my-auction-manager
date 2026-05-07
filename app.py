import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="파크부동산 통합 관리 시스템", page_icon="🏘️", layout="wide")
st.title("🏘️ 파크부동산 통합 관리 시스템")

# --- [데이터 및 로직 정의] ---
category_map = {
    "주거용": ["아파트", "연립/다세대", "단독/다가구", "전원주택", "오피스텔(주거)"],
    "비주거용": ["상가/사무실", "빌딩/건물", "공장/창고", "지식산업센터", "숙박시설"],
    "토지": ["대지", "전/답/과수원", "임야", "잡종지", "기타토지"]
}

# 세션 상태 초기화
if 'land_price' not in st.session_state: st.session_state.land_price = None
if 'py_price' not in st.session_state: st.session_state.py_price = None
if 'land_area' not in st.session_state: st.session_state.land_area = None

# --- [연동 계산 함수] ---
def update_by_total():
    if st.session_state.land_area and st.session_state.land_area > 0 and st.session_state.land_price:
        st.session_state.py_price = int(st.session_state.land_price / st.session_state.land_area)

def update_by_py_price():
    if st.session_state.land_area and st.session_state.py_price:
        st.session_state.land_price = int(st.session_state.py_price * st.session_state.land_area)

def update_by_area():
    if st.session_state.land_area and st.session_state.land_area > 0:
        if st.session_state.py_price:
            st.session_state.land_price = int(st.session_state.py_price * st.session_state.land_area)
        elif st.session_state.land_price:
            st.session_state.py_price = int(st.session_state.land_price / st.session_state.land_area)

# 2. 새 매물 등록 섹션
with st.expander("➕ 새 매물 등록하기 (클릭하여 입력창 열기)", expanded=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.date_input("접수일", datetime.today())
        main_cat = st.radio("물건 대분류", list(category_map.keys()), horizontal=True, index=2)
        st.radio("의뢰목적", ["매도", "임대", "매수", "임차"], horizontal=True)
    
    with col2:
        st.selectbox("물건 소분류", category_map[main_cat])
        st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        
        if main_cat == "토지":
            st.text_input("소재지 상세", placeholder="예: 경기도 남양주시 화도읍...")
            # [수정] step=0을 설정하여 + / - 버튼 제거 (직접 입력 전용)
            st.number_input("평단가 (만원)", key="py_price", value=st.session_state.py_price, step=0, format="%d", on_change=update_by_py_price)
            st.number_input("거래가액 (만원)", key="land_price", value=st.session_state.land_price, step=0, format="%d", on_change=update_by_total)
        else:
            st.number_input("거래가액 (만원)", step=0, format="%d", value=None)
        
    with col3:
        if main_cat == "토지":
            # [수정] 면적 입력창에서도 버튼 제거
            st.number_input("면적 (평)", key="land_area", value=st.session_state.land_area, step=0, format="%d", on_change=update_by_area, placeholder="면적을 입력하세요")
        else:
            st.text_input("소재지 상세")
            st.text_input("면적")
            
        st.text_area("특약내용", height=110, placeholder="특이사항을 입력하세요.")
        
    st.write("")
    if st.button("🏠 데이터베이스 저장", use_container_width=True):
        st.success("데이터가 성공적으로 입력되었습니다.")

st.divider()

# 3. 매물 목록 현황
st.subheader("🔍 매물 관리 목록")
example_df = pd.DataFrame({
    "접수일": [datetime.today().strftime("%Y-%m-%d")],
    "대분류": [main_cat],
    "소분류": [category_map[main_cat][0]],
    "가액": [f"{st.session_state.land_price:,} 만원" if st.session_state.land_price else "-"],
    "면적": [f"{st.session_state.land_area}평" if st.session_state.land_area else "-"],
    "상태": ["진행중"]
})
st.dataframe(example_df, use_container_width=True, hide_index=True)
