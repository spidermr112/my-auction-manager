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
    # 초기 샘플 데이터 (테스트용)
    st.session_state.df_list = pd.DataFrame([
        {"접수일": "2026-05-07", "대분류": "토지", "소분류": "대지", "가액": 50000, "면적": "100평", "상태": "진행중", "소재지": "경기도 남양주시"},
        {"접수일": "2026-05-08", "대분류": "주거용", "소분류": "아파트", "가액": 85000, "면적": "34평", "상태": "완료", "소재지": "서울시 강남구"}
    ])

# --- [공통 함수: 단위 변환] ---
def process_area(input_str):
    if not input_str or input_str.strip() == "": return 0, "-" 
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", input_str)
    if not nums: return 0, "-"
    val = float(nums[0])
    if "평" in input_str:
        return int(val), f"{int(val)}평"
    return int(round(val * 0.3025)), f"{int(round(val * 0.3025))}평"

# --- [공통 함수: 연동 계산] ---
def calc_values():
    area_text = st.session_state.get('area_input', '')
    py_num, _ = process_area(area_text)
    if py_num > 0 and st.session_state.py_price > 0:
        st.session_state.land_price = st.session_state.py_price * py_num
    elif py_num > 0 and st.session_state.land_price > 0 and st.session_state.py_price == 0:
        st.session_state.py_price = int(st.session_state.land_price / py_num)

# --- [카테고리 맵] ---
category_map = {
    "주거용": ["아파트", "연립/다세대", "단독/다가구", "전원주택", "오피스텔(주거)"],
    "비주거용": ["상가/사무실", "빌딩/건물", "공장/창고", "지식산업센터", "숙박시설"],
    "토지": ["대지", "전/답/과수원", "임야", "잡종지", "기타토지"]
}

# 2. 새 매물 등록 섹션 (접이식)
with st.expander("➕ 새 매물 등록하기", expanded=False): # 기본은 닫아둠
    col1, col2, col3 = st.columns(3)
    with col1:
        reg_date = st.date_input("접수일", datetime.today())
        main_cat = st.radio("물건 대분류", list(category_map.keys()), horizontal=True, index=2)
    with col2:
        sub_cat = st.selectbox("물건 소분류", category_map[main_cat])
        st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        addr = st.text_input("소재지 상세", key="addr_input")
        if main_cat == "토지":
            st.number_input("평단가 (만원)", key="py_price", step=0, format="%d", on_change=calc_values)
            st.number_input("거래가액 (만원)", key="land_price", step=0, format="%d", on_change=calc_values)
        else:
            st.number_input("거래가액 (만원)", key="land_price", step=0, format="%d")
    with col3:
        area_text = st.text_input("면적 입력", placeholder="예: 100평 또는 330", key="area_input", on_change=calc_values)
        py_num, py_display = process_area(area_text)
        if area_text: st.info(f"💾 계산 기준 면적: {py_display}")
        st.text_area("특약내용", height=110, key="memo_input")

    if st.button("🏠 데이터베이스 저장", use_container_width=True):
        new_data = {
            "접수일": reg_date.strftime("%Y-%m-%d"),
            "대분류": main_cat, "소분류": sub_cat,
            "가액": st.session_state.land_price, "면적": py_display,
            "상태": "진행중", "소재지": addr
        }
        st.session_state.df_list = pd.concat([st.session_state.df_list, pd.DataFrame([new_data])], ignore_index=True)
        st.success("데이터가 추가되었습니다!")

st.divider()

# 3. 매물 필터링 섹션 (새로 추가된 접이식 기능)
with st.expander("🔍 매물 필터링 / 검색", expanded=True):
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        filter_status = st.multiselect("상태 선택", ["진행중", "완료", "보류", "삭제"], default=["진행중", "보류"])
    with f_col2:
        filter_cat = st.multiselect("대분류 선택", list(category_map.keys()), default=list(category_map.keys()))
    with f_col3:
        search_addr = st.text_input("소재지 검색", placeholder="동네 이름이나 주소 입력")

# 데이터 필터링 로직
df = st.session_state.df_list
if filter_status:
    df = df[df['상태'].isin(filter_status)]
if filter_cat:
    df = df[df['대분류'].isin(filter_cat)]
if search_addr:
    df = df[df['소재지'].str.contains(search_addr, na=False)]

# 4. 매물 관리 목록
st.subheader(f"📋 매물 목록 (검색 결과: {len(df)}건)")
if not df.empty:
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "상태": st.column_config.SelectboxColumn("상태", options=["진행중", "완료", "보류", "삭제"], required=True),
            "가액": st.column_config.NumberColumn("가액(만원)", format="%d 만원"),
        },
        disabled=["접수일", "대분류", "소분류"] 
    )
    if st.button("💾 변경 사항 저장 (상태/내용)"):
        # 필터링된 데이터의 변경사항을 원본 데이터에 반영
        st.session_state.df_list.update(edited_df)
        st.toast("변경사항이 원본에 반영되었습니다!")
else:
    st.info("조건에 맞는 매물이 없습니다.")
