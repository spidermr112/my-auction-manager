import streamlit as st
import pandas as pd
from datetime import datetime
import re

# 1. 페이지 설정
st.set_page_config(page_title="파크부동산 통합 관리 시스템", page_icon="🏘️", layout="wide")
st.title("🏘️ 파크부동산 통합 관리 시스템")

# --- [세션 상태 초기화] ---
if 'land_price' not in st.session_state: st.session_state.land_price = 0
if 'py_price' not in st.session_state: st.session_state.py_price = 0
if 'df_list' not in st.session_state:
    st.session_state.df_list = pd.DataFrame(columns=["접수일", "대분류", "소분류", "가액", "면적", "상태"])

# --- [단위 변환 및 연동 로직] ---
def process_area(input_str):
    if not input_str or input_str.strip() == "": return 0, "-" # 빈 값일 때 "-" 표시
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", input_str)
    if not nums: return 0, "-"
    val = float(nums[0])
    if "평" in input_str:
        return int(val), f"{int(val)}평"
    return int(round(val * 0.3025)), f"{int(round(val * 0.3025))}평"

# --- [연동 계산 함수] ---
def calc_values():
    area_text = st.session_state.get('area_input', '')
    py_num, _ = process_area(area_text)
    
    # 평단가와 면적이 있으면 가액 계산
    if py_num > 0 and st.session_state.py_price > 0:
        st.session_state.land_price = st.session_state.py_price * py_num
    # 가액과 면적이 있으면 평단가 계산
    elif py_num > 0 and st.session_state.land_price > 0 and st.session_state.py_price == 0:
        st.session_state.py_price = int(st.session_state.land_price / py_num)

# 2. 새 매물 등록 섹션
category_map = {"주거용": ["아파트", "연립"], "비주거용": ["상가", "공장"], "토지": ["대지", "임야", "전/답"]}

with st.expander("➕ 새 매물 등록하기", expanded=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        reg_date = st.date_input("접수일", datetime.today())
        main_cat = st.radio("물건 대분류", list(category_map.keys()), horizontal=True, index=2)
    
    with col2:
        sub_cat = st.selectbox("물건 소분류", category_map[main_cat])
        st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        
        if main_cat == "토지":
            st.text_input("소재지 상세", key="addr_input")
            st.number_input("평단가 (만원)", key="py_price", step=0, format="%d", on_change=calc_values)
            st.number_input("거래가액 (만원)", key="land_price", step=0, format="%d", on_change=calc_values)
        else:
            st.number_input("거래가액 (만원)", step=0, format="%d", key="land_price")
    
    with col3:
        area_text = st.text_input("면적 입력", placeholder="예: 100평 또는 330", key="area_input", on_change=calc_values)
        py_num, py_display = process_area(area_text)
        
        if area_text:
            st.info(f"💾 계산 기준 면적: {py_display}")
            
        st.text_area("특약내용", height=110, key="memo_input")

    # --- [수정된 저장 로직: 빈칸 허용] ---
    if st.button("🏠 데이터베이스 저장", use_container_width=True):
        new_data = {
            "접수일": reg_date.strftime("%Y-%m-%d"),
            "대분류": main_cat,
            "소분류": sub_cat,
            "가액": st.session_state.land_price if st.session_state.land_price > 0 else 0,
            "면적": py_display if py_display != "-" else "미입력",
            "상태": "진행중"
        }
        # 새 데이터를 목록에 추가
        st.session_state.df_list = pd.concat([st.session_state.df_list, pd.DataFrame([new_data])], ignore_index=True)
        st.success("데이터가 목록에 추가되었습니다!")

st.divider()

# 3. 매물 관리 목록
st.subheader("🔍 매물 관리 목록")
if not st.session_state.df_list.empty:
    edited_df = st.data_editor(
        st.session_state.df_list,
        use_container_width=True,
        hide_index=True,
        column_config={
            "상태": st.column_config.SelectboxColumn("상태", options=["진행중", "완료", "보류", "삭제"], required=True),
            "가액": st.column_config.NumberColumn("가액(만원)", format="%d 만원"),
        },
        # 가액과 면적도 수정 가능하게 disabled에서 제외함
        disabled=["접수일", "대분류", "소분류"] 
    )
    if st.button("💾 상태 변경 사항 저장"):
        st.session_state.df_list = edited_df
        st.toast("저장되었습니다!")
else:
    st.info("등록된 매물이 없습니다.")
