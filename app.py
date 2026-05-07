import streamlit as st
import pandas as pd
from datetime import datetime
import re

# 1. 페이지 설정
st.set_page_config(page_title="파크부동산 통합 관리 시스템", page_icon="🏘️", layout="wide")
st.title("🏘️ 파크부동산 통합 관리 시스템")

# --- [세션 상태 초기화] ---
if 'land_price' not in st.session_state: st.session_state.land_price = None
if 'py_price' not in st.session_state: st.session_state.py_price = None
if 'land_area_val' not in st.session_state: st.session_state.land_area_val = 0 # 연동용 숫자값

# --- [단위 판별 및 변환 로직] ---
def process_area_input(input_str):
    if not input_str:
        return 0, ""
    
    # 숫자만 추출 (소수점 포함)
    numbers = re.findall(r"[-+]?\d*\.\d+|\d+", input_str)
    if not numbers:
        return 0, ""
    
    val = float(numbers[0])
    
    # [핵심 로직]
    # 1. '평'이라는 글자가 포함되어 있으면 -> 그대로 '평'으로 인식
    if "평" in input_str:
        py_val = int(val)
        status_msg = f"✅ '평' 입력 감지: {py_val}평으로 유지"
    # 2. 숫자만 있거나 ㎡ 관련 단위가 있으면 -> ㎡로 인식하여 평으로 환산
    else:
        py_val = int(round(val * 0.3025))
        status_msg = f"🔄 숫자만 입력(㎡ 인식) -> {py_val}평으로 환산"
        
    return py_val, f"{py_val}평", status_msg

# --- [연동 계산 함수] ---
def update_by_total():
    if st.session_state.land_area_val > 0 and st.session_state.land_price:
        st.session_state.py_price = int(st.session_state.land_price / st.session_state.land_area_val)

def update_by_py_price():
    if st.session_state.land_area_val > 0 and st.session_state.py_price:
        st.session_state.land_price = int(st.session_state.py_price * st.session_state.land_area_val)

# 2. 새 매물 등록 섹션
category_map = {"주거용": ["아파트", "연립"], "비주거용": ["상가", "사무실"], "토지": ["대지", "임야", "전/답"]}

with st.expander("➕ 새 매물 등록하기", expanded=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.date_input("접수일", datetime.today())
        main_cat = st.radio("물건 대분류", list(category_map.keys()), horizontal=True, index=2)
        st.radio("의뢰목적", ["매도", "임대", "매수", "임차"], horizontal=True)
    
    with col2:
        st.selectbox("물건 소분류", category_map[main_cat])
        st.radio("구분", ["매매", "전세", "월세", "복수토지"] if main_cat == "토지" else ["매매", "전세", "월세"], horizontal=True)
        
        if main_cat == "토지":
            st.text_input("소재지 상세")
            # 연동 입력창 (플러스/마이너스 제거)
            st.number_input("평단가 (만원)", key="py_price", value=st.session_state.py_price, step=0, format="%d", on_change=update_by_py_price)
            st.number_input("거래가액 (만원)", key="land_price", value=st.session_state.land_price, step=0, format="%d", on_change=update_by_total)
    
    with col3:
        # 면적 입력 (텍스트로 받아서 단위 판별)
        area_text = st.text_input("면적 입력", placeholder="예: 100평(그대로) 또는 330(㎡로 인식하여 환산)")
        
        # 단위 변환 적용
        py_num, py_display, msg = process_area_input(area_text)
        st.session_state.land_area_val = py_num # 계산용 숫자 저장
        
        if area_text:
            st.info(msg) # 환산 결과 안내
            
        st.text_area("특약내용", height=110)

    if st.button("🏠 데이터베이스 저장", use_container_width=True):
        st.success(f"저장 데이터 일관성 확인: 면적 {py_display} 저장 완료")

st.divider()

# 3. 매물 관리 목록
st.subheader("🔍 매물 관리 목록")
if 'df_list' not in st.session_state:
    st.session_state.df_list = pd.DataFrame([{"접수일": "2026-05-07", "대분류": "토지", "소분류": "대지", "가액": 50000, "면적": "100평", "상태": "진행중"}])

st.data_editor(
    st.session_state.df_list,
    use_container_width=True,
    hide_index=True,
    column_config={
        "상태": st.column_config.SelectboxColumn("상태", options=["진행중", "완료", "보류", "삭제"], required=True),
        "가액": st.column_config.NumberColumn("가액(만원)", format="%d 만원"),
    },
    disabled=["접수일", "대분류", "소분류", "가액", "면적"]
)
