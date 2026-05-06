import streamlit as st
import pandas as pd
from datetime import datetime
import os
import re

# --- 1. 페이지 설정 및 레이아웃 박제 (CSS) ---
st.set_page_config(page_title="파크부동산 매물관리", layout="wide")

st.markdown("""
    <style>
    /* 1. 전체 여백 최적화 */
    .block-container {
        padding: 1.5rem 2rem !important;
        max-width: 100% !important;
    }

    /* 2. 좌측(400px 고정) / 우측(가변 확장) 레이아웃 강제 고정 */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 2rem !important;
    }

    /* 좌측 컬럼: 400px 절대값 박제 */
    [data-testid="column"]:nth-of-type(1) {
        flex: 0 0 400px !important;
        width: 400px !important;
        min-width: 400px !important;
        max-width: 400px !important;
    }

    /* 우측 컬럼: 나머지 무한 확장 */
    [data-testid="column"]:nth-of-type(2) {
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }

    /* 3. 라디오 버튼 벌어짐 방지 (대표님이 지적하신 핵심 부분) */
    div[role="radiogroup"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: wrap !important;
        justify-content: flex-start !important; /* 왼쪽으로 딱 붙임 */
        gap: 15px !important; /* 항목 간 간격을 일정하게 유지 */
    }

    /* 라디오 버튼 각각의 항목이 넓게 퍼지지 않도록 설정 */
    div[role="radiogroup"] > label {
        flex: 0 0 auto !important; 
        width: auto !important;
        margin-right: 5px !important;
    }

    /* 4. 입력창 및 버튼 너비가 박스(400px)를 넘지 않게 조정 */
    .stTextInput, .stTextArea, .stDateInput, .stButton {
        width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 데이터 관리 로직 (기능 일절 수정 없음) ---
DB_FILE = "property_data.csv"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            if 'receipt_date' in df.columns:
                df['receipt_date'] = pd.to_datetime(df['receipt_date']).dt.date
            df = df.fillna("")
            return df
        except: return create_empty_df()
    return create_empty_df()

def create_empty_df():
    return pd.DataFrame(columns=[
        "receipt_date", "item_category", "item_sub_category", "purpose", 
        "trade_type", "room_count", "bathroom_count", "price", 
        "address", "area", "description", "status"
    ])

def save_data(df):
    df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')

def parse_flexible_price(price_str):
    if not price_str: return ""
    processed = re.sub(r'[\.\-\s]+', '/', price_str.strip())
    if '/' in processed:
        try:
            parts = [p for p in processed.split('/') if p]
            if len(parts) >= 2:
                dep = int(re.sub(r'[^0-9]', '', parts[0]))
                mon = int(re.sub(r'[^0-9]', '', parts[1]))
                return f"{dep}/{mon}(환산 {dep + (mon * 100)})"
        except: return processed
    try:
        if processed.isdigit(): return processed
        res = 0
        eok = re.search(r'([\d\.]+)\s*억', processed)
        if eok: res += float(eok.group(1)) * 10000
        cheon = re.search(r'([\d\.]+)\s*천', processed)
        if cheon: res += float(cheon.group(1)) * 100
        return str(int(res)) if res > 0 else processed
    except: return processed

if 'data' not in st.session_state:
    st.session_state.data = load_data()

# --- 3. 화면 구성 ---
col_reg, col_list = st.columns([1, 4]) # CSS에서 강제 조정하므로 비율 의미 없음

with col_reg:
    st.markdown("### 📍 매물 등록")
    with st.form("reg_form", clear_on_submit=True):
        reg_date = st.date_input("접수일", datetime.now())
        reg_cat = st.radio("물건 대분류", ["주거용", "비주거용", "토지"], horizontal=True)
        
        subs = {
            "주거용": ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택"],
            "비주거용": ["상가/사무실", "공장/창고", "빌딩/건물", "지식산업센터", "기타"],
            "토지": ["대지", "임야", "농지", "기타"]
        }
        reg_sub = st.radio("물건 소분류", subs[reg_cat], horizontal=True)
        reg_purp = st.radio("의뢰목적", ["매도", "임대", "매수", "임차", "교환"], horizontal=True)
        reg_trade = st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        
        if reg_cat == "주거용":
            c1, c2 = st.columns(2)
            with c1: reg_room = st.radio("방 개수", ["방1", "방2", "방3", "방4 이상"], horizontal=True)
            with c2: reg_bath = st.radio("화장실", ["화장실1", "화장실2", "화장실3↑"], horizontal=True)
        else:
            reg_room, reg_bath = "", ""

        reg_price = st.text_input("거래가액")
        reg_addr = st.text_input("소재지 상세")
        reg_area = st.text_input("면적(평 or ㎡)")
        reg_desc = st.text_area("특약내용")
        
        if st.form_submit_button("🏠 데이터베이스 저장", use_container_width=True):
            f_area = reg_area
            if reg_area and '평' in reg_area:
                try:
                    num = float(re.sub(r'[^0-9.]', '', reg_area))
                    f_area = f"{round(num * 3.3058, 2)}㎡({num}평)"
                except: pass
            
            new_row = pd.DataFrame([{
                "receipt_date": reg_date, "item_category": reg_cat, "item_sub_category": reg_sub,
                "purpose": reg_purp, "trade_type": reg_trade, "room_count": reg_room,
                "bathroom_count": reg_bath, "price": parse_flexible_price(reg_price),
                "address": reg_addr, "area": f_area, "description": reg_desc, "status": "진행중"
            }])
            st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
            save_data(st.session_state.data)
            st.success("저장 완료!")
            st.rerun()

with col_list:
    with st.container(border=True):
        st.markdown("🔍 **필터 및 검색**")
        s_query = st.text_input("키워드 통합 검색")
        
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            all_list = ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택", "상가/사무실", "공장/창고", "빌딩/건물", "지식산업센터", "대지", "임야", "농지"]
            sel_subs = st.multiselect("소분류 필터", all_list)
        with f_col2:
            sel_purps = st.multiselect("목적 필터", ["매도", "임대", "매수", "임차", "교환"])

    st.markdown(f"### 📋 매물 목록 (총 {len(st.session_state.data)}건)")
    
    df_f = st.session_state.data.copy()
    if s_query:
        df_f = df_f[df_f.apply(lambda r: s_query in str(r.values), axis=1)]
    if sel_subs:
        df_f = df_f[df_f['item_sub_category'].isin(sel_subs)]
    if sel_purps:
        df_f = df_f[df_f['purpose'].isin(sel_purps)]
    
    st.dataframe(df_f.iloc[::-1], use_container_width=True, hide_index=True)

    if st.button("🗑️ 전체 데이터 초기화"):
        if st.checkbox("정말 삭제하시겠습니까?"):
            st.session_state.data = create_empty_df()
            save_data(st.session_state.data)
            st.rerun()
