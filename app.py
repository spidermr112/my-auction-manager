import streamlit as st
import pandas as pd
from datetime import datetime
import os
import re

# --- 1. 페이지 설정 및 반응형 레이아웃 ---
st.set_page_config(page_title="파크부동산 매물관리", layout="wide")

st.markdown("""
    <style>
    .block-container {
        padding: 1rem 2rem !important;
        max-width: 100% !important;
    }

    /* 반응형 Grid 설정: 화면이 작아지면 자동으로 비율 조정 */
    [data-testid="stHorizontalBlock"] {
        display: grid !important;
        /* 좌측은 최대 750px, 최소는 400px까지 유동적 / 우측은 나머지 전부 */
        grid-template-columns: minmax(400px, 750px) 1fr !important; 
        gap: 2rem !important;
        align-items: start !important;
    }

    /* 모바일이나 아주 작은 화면에서는 위아래로 배치되도록 설정 */
    @media (max-width: 1000px) {
        [data-testid="stHorizontalBlock"] {
            grid-template-columns: 1fr !important;
        }
    }

    [data-testid="column"]:nth-of-type(1) {
        width: 100% !important;
        max-width: 750px !important;
        flex: none !important;
    }

    /* 라디오 버튼 정렬 */
    div[role="radiogroup"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: wrap !important;
        gap: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 데이터 로직 (생략/유지) ---
DB_FILE = "property_data.csv"
def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            if 'receipt_date' in df.columns:
                df['receipt_date'] = pd.to_datetime(df['receipt_date']).dt.date
            return df.fillna("")
        except: return create_empty_df()
    return create_empty_df()

def create_empty_df():
    return pd.DataFrame(columns=["receipt_date", "item_category", "item_sub_category", "purpose", "trade_type", "room_count", "bathroom_count", "price", "address", "area", "description", "status"])

def save_data(df):
    df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')

if 'data' not in st.session_state:
    st.session_state.data = load_data()

# --- 3. 화면 배치 ---
col_reg, col_list = st.columns([1, 1])

with col_reg:
    st.subheader("🚩 매물 등록")
    
    # [핵심] 대분류를 폼(Form) 밖으로 빼야 소분류가 즉각 바뀝니다.
    reg_cat = st.radio("물건 대분류", ["주거용", "비주거용", "토지"], horizontal=True)
    
    subs = {
        "주거용": ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택"],
        "비주거용": ["상가/사무실", "공장/창고", "빌딩/건물", "지식산업센터", "기타"],
        "토지": ["대지", "임야", "농지", "기타"]
    }

    with st.form("reg_form", clear_on_submit=True):
        reg_date = st.date_input("접수일", datetime.now())
        # 여기서 reg_cat에 따라 리스트가 실시간 변경됨
        reg_sub = st.radio("물건 소분류", subs[reg_cat], horizontal=True)
        
        reg_purp = st.radio("의뢰목적", ["매도", "임대", "매수", "임차", "교환"], horizontal=True)
        reg_trade = st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        
        if reg_cat == "주거용":
            c1, c2 = st.columns(2)
            with c1: reg_room = st.radio("방 개수", ["방1", "방2", "방3", "방4↑"], horizontal=True)
            with c2: reg_bath = st.radio("화장실", ["화장실1", "화장실2", "화장실3↑"], horizontal=True)
        else:
            reg_room, reg_bath = "", ""

        reg_price = st.text_input("거래가액")
        reg_addr = st.text_input("소재지 상세")
        reg_area = st.text_input("면적(평 or ㎡)")
        reg_desc = st.text_area("특약내용")
        
        if st.form_submit_button("🏠 데이터베이스 저장", use_container_width=True):
            # (저장 로직은 기존과 동일)
            new_row = pd.DataFrame([{
                "receipt_date": reg_date, "item_category": reg_cat, "item_sub_category": reg_sub,
                "purpose": reg_purp, "trade_type": reg_trade, "room_count": reg_room,
                "bathroom_count": reg_bath, "price": reg_price,
                "address": reg_addr, "area": reg_area, "description": reg_desc, "status": "진행중"
            }])
            st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
            save_data(st.session_state.data)
            st.rerun()

with col_list:
    st.subheader("📋 매물 목록")
    st.dataframe(st.session_state.data.iloc[::-1], use_container_width=True, hide_index=True)
