import streamlit as st
import pandas as pd
from datetime import datetime
import re

# 1. 페이지 설정
st.set_page_config(page_title="파크부동산", page_icon="🏘️", layout="wide")
st.title("🏘️ 파크부동산")

# --- [세션 상태 초기화] ---
if 'land_price' not in st.session_state: st.session_state.land_price = 0
if 'py_price' not in st.session_state: st.session_state.py_price = 0
if 'search_query' not in st.session_state: st.session_state.search_query = "" 
if 'df_list' not in st.session_state:
    st.session_state.df_list = pd.DataFrame(columns=["접수일", "대분류", "소분류", "가액", "면적", "상태", "소재지"])

# --- [유틸리티 함수] ---
def process_area(input_str):
    if not input_str or input_str.strip() == "": return 0, "-" 
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", input_str)
    if not nums: return 0, "-"
    val = float(nums[0])
    if "평" in input_str: return int(val), f"{int(val)}평"
    return int(round(val * 0.3025)), f"{int(round(val * 0.3025))}평"

def calc_values():
    area_text = st.session_state.get('area_input', '')
    py_num, _ = process_area(area_text)
    if py_num > 0 and st.session_state.py_price > 0:
        st.session_state.land_price = st.session_state.py_price * py_num
    elif py_num > 0 and st.session_state.land_price > 0 and st.session_state.py_price == 0:
        st.session_state.py_price = int(st.session_state.land_price / py_num)

category_map = {
    "주거용": ["아파트", "연립/다세대", "단독/다가구", "전원주택", "오피스텔(주거)"],
    "비주거용": ["상가/사무실", "빌딩/건물", "공장/창고", "지식산업센터", "숙박시설"],
    "토지": ["대지", "전/답/과수원", "임야", "잡종지", "기타토지"]
}

# 2. 매물 등록하기 (이전과 동일)
with st.expander("➕ 매물 등록하기", expanded=False):
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

st.write("")

# 3. 매물 필터링 (이전과 동일)
with st.expander("🔍 매물 필터링 / 검색", expanded=True):
    f_col1, f_col2, f_col3 = st.columns([1, 1, 1])
    with f_col1:
        filter_status = st.multiselect("상태 선택", ["진행중", "완료", "보류", "삭제"], default=["진행중", "보류"])
    with f_col2:
        filter_cat = st.multiselect("대분류 선택", list(category_map.keys()), default=list(category_map.keys()))
    with f_col3:
        s_col1, s_col2 = st.columns([3, 1])
        with s_col1:
            search_input = st.text_input("소재지 검색", placeholder="동네 이름이나 주소", label_visibility="collapsed")
        with s_col2:
            if st.button("🔍 검색", use_container_width=True):
                st.session_state.search_query = search_input

# 필터링 로직
df_filtered = st.session_state.df_list.copy()
if filter_status:
    df_filtered = df_filtered[df_filtered['상태'].isin(filter_status)]
if filter_cat:
    df_filtered = df_filtered[df_filtered['대분류'].isin(filter_cat)]
if st.session_state.search_query:
    df_filtered = df_filtered[df_filtered['소재지'].str.contains(st.session_state.search_query, na=False)]

# --- [여기부터 매물 목록 수정 부분] ---
st.subheader(f"📋 매물 목록 관리 (조회: {len(df_filtered)}건)")

# 데이터 편집기 설정
edited_df = st.data_editor(
    df_filtered,
    use_container_width=True,
    hide_index=True,
    num_rows="dynamic", # 행 추가/삭제 가능 모드
    column_config={
        "접수일": st.column_config.TextColumn("📅 접수일", width="small"),
        "대분류": st.column_config.TextColumn("📁 분류", width="small"),
        "소분류": st.column_config.TextColumn("📄 세부", width="small"),
        "소재지": st.column_config.TextColumn("📍 소재지 상세", width="large"),
        "가액": st.column_config.NumberColumn("💰 가액(만원)", format="%d", width="medium"),
        "면적": st.column_config.TextColumn("📏 면적", width="small"),
        "상태": st.column_config.SelectboxColumn(
            "⚙️ 상태", 
            options=["진행중", "완료", "보류", "삭제"],
            required=True,
            width="small"
        ),
    },
    # 접수일과 분류는 실수 방지를 위해 수정 불가 처리, 나머지는 수정 가능
    disabled=["접수일", "대분류", "소분류"] 
)

# 변경 사항 반영 버튼
c1, c2, _ = st.columns([1, 1, 2])
with c1:
    if st.button("💾 모든 변경 사항 저장", use_container_width=True):
        # 편집된 데이터를 원본 세션에 반영
        # 필터링된 상태에서 행이 삭제되거나 수정된 것을 원본에 동기화
        st.session_state.df_list = edited_df
        st.toast("목록이 성공적으로 업데이트되었습니다!")
with c2:
    # 엑셀 다운로드 기능 추가 (보너스)
    csv = df_filtered.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 목록 다운로드 (CSV)", data=csv, file_name="park_land_list.csv", use_container_width=True)

if df_filtered.empty:
    st.info("조건에 맞는 매물이 없습니다. 필터를 조정하거나 새 매물을 등록해 주세요.")
