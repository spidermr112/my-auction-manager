import streamlit as st
import pandas as pd
from datetime import datetime
import re
import os

# 1. 페이지 설정
st.set_page_config(page_title="파크부동산", page_icon="🏠", layout="wide")
st.title("🏠 파크부동산")

# --- [데이터 저장/불러오기 로직] ---
DB_FILE = "property_db.csv"
COLS = ["의뢰목적", "소분류", "구분", "소재지", "면적", "가액", "월세", "대분류", "접수일", "상태"]

def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            for col in COLS:
                if col not in df.columns:
                    df[col] = 0 if col in ["가액", "월세"] else "-"
            return df[COLS]
        except:
            pass
    return pd.DataFrame(columns=COLS)

def save_data(df):
    df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')

if 'df_list' not in st.session_state:
    st.session_state.df_list = load_data()
if 'search_query' not in st.session_state: 
    st.session_state.search_query = ""

def process_area(input_str):
    if not input_str or str(input_str).strip() == "": return 0, "-" 
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", str(input_str))
    if not nums: return 0, "-"
    val = float(nums[0])
    if "평" in str(input_str): return int(val), f"{int(val)}평"
    return int(round(val * 0.3025)), f"{int(round(val * 0.3025))}평"

category_map = {
    "주거용": ["연립/다세대", "아파트", "단독/다가구", "오피스텔(주거)"],
    "비주거용": ["상가/사무실", "빌딩/건물", "공장/창고", "지식산업센터", "숙박시설"],
    "토지": ["대지", "전/답/과수원", "임야", "잡종지", "기타토지"]
}

# 2. 매물 등록하기 (낱개 등록)
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
        price = st.number_input("가액/보증금 (만원)", step=0, format="%d")
        rent = st.number_input("월세 (만원)", step=0, format="%d") if gubun == "월세" else 0
    with col3:
        area_text = st.text_input("면적 입력(평 또는 ㎡)", placeholder="")
        _, py_display = process_area(area_text)
        guide_text = "특약, 비밀번호, 방, 욕실, 씽크대, 구조, 난방, 전기용량 등 상세 내용을 입력하세요."
        memo = st.text_area("특약내용", height=150, placeholder=guide_text)

    if st.button("🏠 데이터베이스 저장", use_container_width=True):
        new_row = pd.DataFrame([{
            "의뢰목적": req_purpose, "소분류": sub_cat, "구분": gubun, "소재지": addr, 
            "면적": py_display, "가액": price, "월세": rent, "대분류": main_cat,
            "접수일": reg_date.strftime("%Y-%m-%d"), "상태": "진행중"
        }])
        st.session_state.df_list = pd.concat([st.session_state.df_list, new_row], ignore_index=True)
        save_data(st.session_state.df_list)
        st.success("새 매물이 등록되었습니다.")

# --- [신규: 엑셀 대량 업로드 섹션] ---
with st.expander("📁 엑셀 파일로 대량 등록", expanded=False):
    st.info("엑셀 파일의 제목줄이 [의뢰목적, 소분류, 구분, 소재지, 면적, 가액, 월세, 대분류, 접수일, 상태]로 구성되어야 합니다.")
    uploaded_file = st.file_uploader("엑셀 파일(.xlsx) 선택", type=["xlsx"])
    
    if uploaded_file is not None:
        try:
            df_excel = pd.read_excel(uploaded_file)
            # 필수 컬럼 존재 여부 확인
            missing_cols = [c for c in COLS if c not in df_excel.columns]
            
            if not missing_cols:
                st.write("▲ 업로드할 데이터 미리보기 (상위 5건)")
                st.dataframe(df_excel.head(), use_container_width=True)
                
                if st.button("✅ 위 데이터를 데이터베이스에 추가합니다"):
                    st.session_state.df_list = pd.concat([st.session_state.df_list, df_excel[COLS]], ignore_index=True)
                    save_data(st.session_state.df_list)
                    st.success(f"총 {len(df_excel)}건의 매물이 추가되었습니다!")
                    st.rerun()
            else:
                st.error(f"엑셀 양식이 맞지 않습니다. 빠진 항목: {', '.join(missing_cols)}")
        except Exception as e:
            st.error(f"오류 발생: {e}")

st.write("") 

# 3. 매물 필터링 / 검색
with st.expander("🔍 매물 필터링 / 검색", expanded=True):
    f_col1, f_col2, f_col3 = st.columns([1, 1, 1])
    with f_col1:
        filter_status = st.multiselect("상태 선택", ["진행중", "완료", "보류", "삭제"], default=["진행중", "보류"])
    with f_col2:
        filter_cat = st.multiselect("대분류 선택", list(category_map.keys()), default=list(category_map.keys()))
    with f_col3:
        search_val = st.text_input("검색어 입력", value=st.session_state.search_query, label_visibility="collapsed")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔍 검색", use_container_width=True):
                st.session_state.search_query = search_val
                st.rerun()
        with c2:
            if st.button("🔄 초기화", use_container_width=True):
                st.session_state.search_query = ""
                st.rerun()

# --- [필터링 및 검색 로직] ---
df_display = st.session_state.df_list.copy()
if filter_status: df_display = df_display[df_display['상태'].isin(filter_status)]
if filter_cat: df_display = df_display[df_display['대분류'].isin(filter_cat)]

if st.session_state.search_query.strip():
    keywords = st.session_state.search_query.split()
    for word in keywords:
        clean_word = re.sub(r'[^가-힣a-zA-Z0-9]', '', word)
        search_target = df_display.apply(lambda x: re.sub(r'[^가-힣a-zA-Z0-9]', '', " ".join(x.astype(str))), axis=1)
        df_display = df_display[search_target.str.contains(clean_word, case=False, na=False)]

# 4. 매물 목록 관리
st.subheader(f"📋 매물 목록 관리 ({len(df_display)}건)")
edited_df = st.data_editor(
    df_display, 
    use_container_width=True, 
    hide_index=True, 
    num_rows="dynamic",
    column_config={
        "의뢰목적": st.column_config.SelectboxColumn("의뢰목적", options=["매도의뢰", "매수의뢰"], required=True),
        "구분": st.column_config.SelectboxColumn("구분", options=["매매", "전세", "월세"], required=True),
        "가액": st.column_config.NumberColumn("가액", format="%d"),
        "월세": st.column_config.NumberColumn("월세", format="%d"),
        "상태": st.column_config.SelectboxColumn("상태", options=["진행중", "완료", "보류", "삭제"], required=True),
    },
    disabled=["대분류", "소분류"]
)

if st.button("💾 모든 변경 사항 저장", use_container_width=True):
    # 수정된 데이터 반영
    st.session_state.df_list.update(edited_df)
    save_data(st.session_state.df_list)
    st.toast("저장되었습니다!")
