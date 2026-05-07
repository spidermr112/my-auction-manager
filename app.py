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
            cols = ["접수일", "의뢰목적", "대분류", "소분류", "구분", "가액", "월세", "면적", "상태", "소재지"]
            for col in cols:
                if col not in df.columns:
                    df[col] = 0 if col in ["가액", "월세"] else "-"
            return df[cols]
        except:
            pass
    return pd.DataFrame(columns=["접수일", "의뢰목적", "대분류", "소분류", "구분", "가액", "월세", "면적", "상태", "소재지"])

def save_data(df):
    df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')

# --- [세션 상태 초기화] ---
if 'df_list' not in st.session_state:
    st.session_state.df_list = load_data()
if 'search_query' not in st.session_state: st.session_state.search_query = ""

# --- [유틸리티 함수] ---
def process_area(input_str):
    if not input_str or input_str.strip() == "": return 0, "-" 
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", input_str)
    if not nums: return 0, "-"
    val = float(nums[0])
    if "평" in input_str: return int(val), f"{int(val)}평"
    return int(round(val * 0.3025)), f"{int(round(val * 0.3025))}평"

category_map = {
    "주거용": ["연립/다세대", "아파트", "단독/다가구", "전원주택", "오피스텔(주거)"],
    "비주거용": ["상가/사무실", "빌딩/건물", "공장/창고", "지식산업센터", "숙박시설"],
    "토지": ["대지", "전/답/과수원", "임야", "잡종지", "기타토지"]
}

# 2. 매물 등록하기
with st.expander("➕ 매물 등록하기", expanded=False):
    col1, col2, col3 = st.columns(3)
    with col1:
        reg_date = st.date_input("접수일", datetime.today())
        req_purpose = st.radio("의뢰목적", ["매도의뢰", "매수의뢰"], horizontal=True)
        main_cat = st.radio("물건 대분류", list(category_map.keys()), horizontal=True)
    with col2:
        sub_cat = st.selectbox("물건 소분류", category_map[main_cat])
        gubun = st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        addr = st.text_input("소재지 상세")
        
        # 금액 입력 세션 직접 관리 대신 일반 변수 사용
        price = st.number_input("가액/보증금 (만원)", step=0, format="%d")
        rent = st.number_input("월세 (만원)", step=0, format="%d") if gubun == "월세" else 0
    with col3:
        area_text = st.text_input("면적 입력", placeholder="")
        _, py_display = process_area(area_text)
        st.text_area("특약내용", height=150, key="memo_input")

    if st.button("🏠 데이터베이스 저장", use_container_width=True):
        new_data = {
            "접수일": reg_date.strftime("%Y-%m-%d"),
            "의뢰목적": req_purpose, "대분류": main_cat, "소분류": sub_cat, "구분": gubun,
            "가액": price, "월세": rent, "면적": py_display, "상태": "진행중", "소재지": addr
        }
        st.session_state.df_list = pd.concat([st.session_state.df_list, pd.DataFrame([new_data])], ignore_index=True)
        save_data(st.session_state.df_list)
        st.success("저장 완료!")

st.write("") 

# 3. 매물 필터링 / 검색
with st.expander("🔍 매물 필터링 / 검색", expanded=True):
    f_col1, f_col2, f_col3 = st.columns([1, 1, 1])
    with f_col1:
        filter_status = st.multiselect("상태 선택", ["진행중", "완료", "보류", "삭제"], default=["진행중", "보류"])
    with f_col2:
        filter_cat = st.multiselect("대분류 선택", list(category_map.keys()), default=list(category_map.keys()))
    with f_col3:
        # 검색어 처리를 위한 텍스트 입력창
        search_val = st.text_input("검색어 입력", value=st.session_state.search_query, placeholder="", label_visibility="collapsed")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔍 검색", use_container_width=True):
                st.session_state.search_query = search_val
                st.rerun() # 즉시 화면 갱신
        with c2:
            if st.button("🔄 초기화", use_container_width=True):
                st.session_state.search_query = ""
                st.rerun()

# --- [검색 알고리즘 강화] ---
df_final = st.session_state.df_list.copy()

# 1. 상태/카테고리 필터
if filter_status: df_final = df_final[df_final['상태'].isin(filter_status)]
if filter_cat: df_final = df_final[df_final['대분류'].isin(filter_cat)]

# 2. 키워드 검색 (공백 기준 다중 AND 조건 + 특수문자 제거)
if st.session_state.search_query.strip():
    keywords = st.session_state.search_query.split()
    for word in keywords:
        clean_word = re.sub(r'[^가-힣a-zA-Z0-9]', '', word)
        # 모든 텍스트 열에서 특수문자를 제거하고 통합 검색
        search_target = df_final.apply(lambda x: re.sub(r'[^가-힣a-zA-Z0-9]', '', " ".join(x.astype(str))), axis=1)
        df_final = df_final[search_target.str.contains(clean_word, case=False, na=False)]

# 4. 매물 목록 관리
st.subheader(f"📋 매물 목록 관리 ({len(df_final)}건)")

# 데이터 에디터에서 인덱스 유지를 위해 별도 처리
edited_df = st.data_editor(
    df_final, 
    use_container_width=True, 
    hide_index=True, 
    num_rows="dynamic",
    column_config={
        "상태": st.column_config.SelectboxColumn("상태", options=["진행중", "완료", "보류", "삭제"], required=True),
        "의뢰목적": st.column_config.SelectboxColumn("의뢰목적", options=["매도의뢰", "매수의뢰"], required=True),
    },
    disabled=["접수일", "대분류", "소분류"]
)

if st.button("💾 모든 변경 사항 저장", use_container_width=True):
    # 검색된 결과에서 수정한 내용을 원본 리스트에 정확히 반영 (인덱스 매칭)
    # 1. 원본 데이터프레임 복사
    new_master_df = st.session_state.df_list.copy()
    # 2. 현재 화면에 보이는 데이터(수정본)의 인덱스를 기준으로 원본 업데이트
    # (data_editor는 인덱스를 유지하므로 유효함)
    new_master_df.update(edited_df)
    
    st.session_state.df_list = new_master_df
    save_data(st.session_state.df_list)
    st.toast("전체 데이터베이스에 안전하게 저장되었습니다!")
