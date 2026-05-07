import streamlit as st
import pandas as pd
from datetime import datetime
import re
import os

# 1. 페이지 설정
st.set_page_config(page_title="파크부동산", page_icon="🏘️", layout="wide")
st.title("🏘️ 파크부동산")

# --- [데이터 저장/불러오기 로직] ---
DB_FILE = "property_db.csv"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            # '월세' 열이 없으면 새로 생성 (기존 데이터 호환용)
            if "월세" not in df.columns:
                df["월세"] = 0
            return df
        except:
            pass
    return pd.DataFrame(columns=["접수일", "대분류", "소분류", "구분", "가액", "월세", "면적", "상태", "소재지"])

def save_data(df):
    df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')

# --- [세션 상태 초기화] ---
if 'df_list' not in st.session_state:
    st.session_state.df_list = load_data()
if 'land_price' not in st.session_state: st.session_state.land_price = 0
if 'monthly_rent' not in st.session_state: st.session_state.monthly_rent = 0 # 월세 세션 추가
if 'py_price' not in st.session_state: st.session_state.py_price = 0
if 'search_query' not in st.session_state: st.session_state.search_query = ""

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
    curr_py = st.session_state.get('py_price', 0)
    curr_land = st.session_state.get('land_price', 0)
    if py_num > 0 and curr_py > 0:
        st.session_state.land_price = int(curr_py * py_num)
    elif py_num > 0 and curr_land > 0 and curr_py == 0:
        st.session_state.py_price = int(curr_land / py_num)

# --- [카테고리 설정] ---
category_map = {
    "주거용": ["연립/다세대", "아파트", "단독/다가구", "전원주택", "오피스텔(주거)"],
    "비주거용": ["상가/사무실", "빌딩/건물", "공장/창고", "지식산업센터", "숙박시설"],
    "토지": ["대지", "전/답/과수원", "임야", "잡종지", "기타토지"]
}

# 2. 매물 등록하기
with st.expander("➕ 매물 등록하기", expanded=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        reg_date = st.date_input("접수일", datetime.today())
        main_cat = st.radio("물건 대분류", list(category_map.keys()), horizontal=True, index=0)
    with col2:
        sub_cat = st.selectbox("물건 소분류", category_map[main_cat])
        gubun = st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        addr = st.text_input("소재지 상세", key="addr_input")
        
        # --- [월세 분리 로직] ---
        if gubun == "매매":
            st.number_input("평단가 (만원)", key="py_price", step=0, format="%d", on_change=calc_values)
            st.number_input("거래가액 (만원)", key="land_price", step=0, format="%d", on_change=calc_values)
        elif gubun == "월세":
            st.number_input("보증금 (만원)", key="land_price", step=0, format="%d")
            st.number_input("월세 (만원)", key="monthly_rent", step=0, format="%d")
        else: # 전세
            st.number_input("거래가액 (만원)", key="land_price", step=0, format="%d")
            
    with col3:
        area_text = st.text_input("면적 입력", placeholder="예: 100평 또는 330", key="area_input", on_change=calc_values)
        py_num, py_display = process_area(area_text)
        if area_text: st.info(f"💾 계산 기준 면적: {py_display}")
        st.text_area("특약내용", height=110, key="memo_input")

    if st.button("🏠 데이터베이스 저장", use_container_width=True):
        new_data = {
            "접수일": reg_date.strftime("%Y-%m-%d"),
            "대분류": main_cat, "소분류": sub_cat, "구분": gubun,
            "가액": st.session_state.get('land_price', 0), 
            "월세": st.session_state.get('monthly_rent', 0) if gubun == "월세" else 0, # 월세 저장
            "면적": py_display, "상태": "진행중", "소재지": addr
        }
        st.session_state.df_list = pd.concat([st.session_state.df_list, pd.DataFrame([new_data])], ignore_index=True)
        save_data(st.session_state.df_list)
        st.success("매물이 저장되었습니다!")

st.write("") 

# 3. 매물 필터링 / 검색
with st.expander("🔍 매물 필터링 / 검색", expanded=True):
    f_col1, f_col2, f_col3 = st.columns([1, 1, 1])
    with f_col1:
        filter_status = st.multiselect("상태 선택", ["진행중", "완료", "보류", "삭제"], default=["진행중", "보류"])
    with f_col2:
        filter_cat = st.multiselect("대분류 선택", list(category_map.keys()), default=list(category_map.keys()))
    with f_col3:
        s_col1, s_col2 = st.columns([3, 1])
        with s_col1:
            search_input = st.text_input("소재지 검색", placeholder="주소 입력", label_visibility="collapsed")
        with s_col2:
            if st.button("🔍 검색", use_container_width=True):
                st.session_state.search_query = search_input

# 필터링 적용
df_filtered = st.session_state.df_list.copy()
if filter_status: df_filtered = df_filtered[df_filtered['상태'].isin(filter_status)]
if filter_cat: df_filtered = df_filtered[df_filtered['대분류'].isin(filter_cat)]
if st.session_state.search_query:
    df_filtered = df_filtered[df_filtered['소재지'].str.contains(st.session_state.search_query, na=False)]

# 4. 매물 목록 관리
st.subheader(f"📋 매물 목록 관리 ({len(df_filtered)}건)")
edited_df = st.data_editor(
    df_filtered, 
    use_container_width=True, 
    hide_index=True, 
    num_rows="dynamic",
    column_config={
        "상태": st.column_config.SelectboxColumn("상태", options=["진행중", "완료", "보류", "삭제"], required=True),
        "가액": st.column_config.NumberColumn("가액/보증금", format="%d"),
        "월세": st.column_config.NumberColumn("월세", format="%d"),
    },
    disabled=["접수일", "대분류", "소분류"]
)

if st.button("💾 모든 변경 사항 저장", use_container_width=True):
    st.session_state.df_list = edited_df
    save_data(st.session_state.df_list)
    st.toast("변경사항이 영구 저장되었습니다!")
