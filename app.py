import streamlit as st
import pandas as pd
from datetime import datetime
import os
import re
import time

# --- 1. 페이지 설정 및 디자인 고정 ---
st.set_page_config(page_title="파크부동산 매물관리", layout="wide")

# 사이드바 폭을 350px로 고정하는 CSS
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        min-width: 350px;
        max-width: 350px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 데이터 관리 로직 ---
DB_FILE = "property_data.csv"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            if 'receipt_date' in df.columns:
                df['receipt_date'] = pd.to_datetime(df['receipt_date']).dt.date
            return df
        except:
            return create_empty_df()
    else:
        return create_empty_df()

def create_empty_df():
    return pd.DataFrame(columns=[
        "id", "receipt_date", "item_category", "item_sub_category", 
        "purpose", "trade_type", "room_count", "bathroom_count", 
        "price", "address", "area", "description", "status"
    ])

def save_data(df):
    df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')

def parse_korean_price(price_str):
    """한글 금액 및 월세 환산보증금 계산"""
    if not price_str: return "0"
    if '/' in price_str:
        try:
            parts = price_str.split('/')
            deposit = int(re.sub(r'[^0-9]', '', parts[0]))
            monthly = int(re.sub(r'[^0-9]', '', parts[1]))
            hwan_san = deposit + (monthly * 100)
            return f"{price_str} (환산 {hwan_san})"
        except: return price_str
    try:
        if price_str.isdigit(): return price_str
        result = 0
        eok = re.search(r'([\d\.]+)\s*억', price_str)
        if eok: result += float(eok.group(1)) * 10000
        cheon = re.search(r'([\d\.]+)\s*천', price_str)
        if cheon: result += float(cheon.group(1)) * 100
        if not eok and not cheon:
            num = re.sub(r'[^0-9]', '', price_str)
            return num if num else "0"
        return str(int(result))
    except: return price_str

# 세션 초기화
if 'data' not in st.session_state:
    st.session_state.data = load_data()
if 'last_submit_time' not in st.session_state:
    st.session_state.last_submit_time = 0

# --- 3. 사이드바: 매물 등록 (위치 고정) ---
with st.sidebar:
    st.title("📍 매물 등록")
    with st.form("registration_form", clear_on_submit=True):
        reg_date = st.date_input("접수일", datetime.now())
        reg_cat = st.radio("물건 대분류", ["주거용", "비주거용", "토지"], horizontal=True)
        
        # --- 수정된 부분: 순서 변경 및 라디오 버튼 적용 ---
        if reg_cat == "주거용":
            subs = ["빌라/다세대", "단독/다가구", "전원주택", "아파트", "오피스텔(주거)"]
        elif reg_cat == "비주거용":
            subs = ["상가/사무실", "공장/창고", "빌딩/건물", "지식산업센터", "기타"]
        else:
            subs = ["대지", "임야", "농지", "기타"]
            
        reg_sub = st.radio("물건 소분류", subs) # selectbox에서 radio로 변경
        # ---------------------------------------------
        
        reg_purp = st.radio("의뢰목적", ["매도", "임대", "매수", "임차", "교환"], horizontal=True)
        reg_trade = st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        
        reg_price_raw = st.text_input("거래가액(*만, 보증금/월차임)", placeholder="예: 3억 5천 / 4000/35")
        reg_addr = st.text_input("소재지 상세")
        reg_area_raw = st.text_input("면적(평 or ㎡ 둘다 가능)", placeholder="예: 30평")
        reg_desc = st.text_area("특약내용")
        
        submit_btn = st.form_submit_button("🏠 데이터베이스 저장", use_container_width=True)

        if submit_btn:
            current_time = time.time()
            if current_time - st.session_state.last_submit_time > 2.0:
                st.session_state.last_submit_time = current_time
                
                final_price = parse_korean_price(reg_price_raw)
                final_area = reg_area_raw
                if reg_area_raw and '평' in reg_area_raw:
                    try:
                        num = float(re.sub(r'[^0-9.]', '', reg_area_raw))
                        final_area = f"{round(num * 3.3058, 2)}㎡({num}평)"
                    except: pass
                
                new_row = pd.DataFrame([{
                    "id": f"P_{int(current_time * 1000)}",
                    "receipt_date": reg_date, "item_category": reg_cat,
                    "item_sub_category": reg_sub, "purpose": reg_purp,
                    "trade_type": reg_trade, "price": final_price,
                    "address": reg_addr if reg_addr else "(미입력)",
                    "area": final_area if final_area else "(미입력)",
                    "description": reg_desc, "status": "진행중"
                }])
                st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
                save_data(st.session_state.data)
                st.success("저장되었습니다!")
                st.rerun()

# --- 4. 메인 화면: 매물 목록 및 색인 ---
st.title("🏘️ 파크부동산 통합 관리 시스템")

# 상단 검색창
s_query = st.text_input("🔍 키워드 검색 (주소, 특약 등)", placeholder="검색어를 입력하세요.")

# 필터 섹션 (체크박스)
with st.expander("✅ 필터 상세 선택", expanded=True):
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        all_subs = ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택", "상가/사무실", "공장/창고", "빌딩/건물", "지식산업센터", "대지", "임야", "농지"]
        st.write("**물건 소분류**")
        f_sub_cols = st.columns(4)
        selected_subs = []
        for i, opt in enumerate(all_subs):
            if f_sub_cols[i % 4].checkbox(opt, key=f"filter_{opt}"):
                selected_subs.append(opt)
    with f_col2:
        st.write("**의뢰 목적**")
        f_purp_cols = st.columns(3)
        selected_purps = []
        for i, opt in enumerate(["매도", "임대", "매수", "임차", "교환"]):
            if f_purp_cols[i % 3].checkbox(opt, key=f"filter_p_{opt}"):
                selected_purps.append(opt)

# 데이터 필터링
df_display = st.session_state.data.copy()
if s_query:
    df_display = df_display[df_display.apply(lambda r: s_query in str(r.values), axis=1)]
if selected_subs:
    df_display = df_display[df_display['item_sub_category'].isin(selected_subs)]
if selected_purps:
    df_display = df_display[df_display['purpose'].isin(selected_purps)]

# 결과 표 출력
st.subheader(f"📊 매물 목록 (총 {len(df_display)}건)")
st.dataframe(df_display.drop(columns=['id'], errors='ignore'), use_container_width=True, hide_index=True)

# 초기화 버튼
if st.button("🗑️ 전체 데이터 초기화"):
    if st.checkbox("정말 삭제하시겠습니까? (체크 후 버튼 다시 클릭)"):
        st.session_state.data = create_empty_df()
        save_data(st.session_state.data)
        st.rerun()
