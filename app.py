import streamlit as st
import pandas as pd
from datetime import datetime
import os
import re
import time

# --- 1. 페이지 설정 및 디자인 고정 ---
st.set_page_config(page_title="파크부동산 매물관리", layout="wide")

# 사이드바 폭 고정 및 줄바꿈 방지 CSS
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        min-width: 350px;
        max-width: 350px;
    }
    .stCheckbox label {
        white-space: nowrap !important;
        word-break: keep-all !important;
        min-width: max-content !important;
    }
    .filter-label {
        color: red;
        font-weight: bold;
        font-size: 15px;
        white-space: nowrap;
    }
    [data-testid="column"] {
        padding-right: 5px !important;
        padding-left: 5px !important;
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

# --- 3. 사이드바: 매물 등록 ---
with st.sidebar:
    st.title("📍 매물 등록")
    with st.form("registration_form", clear_on_submit=True):
        reg_date = st.date_input("접수일", datetime.now())
        reg_cat = st.radio("물건 대분류", ["주거용", "비주거용", "토지"], horizontal=True)
        
        if reg_cat == "주거용":
            subs = ["연립/다세대", "단독/다가구", "전원주택", "아파트", "오피스텔(주거)"]
        elif reg_cat == "비주거용":
            subs = ["상가/사무실", "공장/창고", "빌딩/건물", "지식산업센터", "기타"]
        else:
            subs = ["대지", "임야", "농지", "기타"]
            
        reg_sub = st.radio("물건 소분류", subs)
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

# --- 4. 메인 화면: 통합 필터 및 목록 ---
st.title("🏘️ 파크부동산 통합 관리 시스템")

s_query = st.text_input("🔍 키워드 검색 (주소, 특약 등)", placeholder="검색어를 입력하세요.")

# [필터 상세 선택 섹션]
with st.expander("✅ 필터 상세 선택", expanded=True):
    # 1. 주거용 라인 (연동 기능 추가)
    c = st.columns([1, 1.2, 1.2, 1, 1, 1.5])
    f_ju = c[0].checkbox("주거용", key="f_ju")
    # 대분류 체크 시 소분류의 value값을 f_ju와 동기화
    f_yeon = c[1].checkbox("연립/다세대", key="f_yeon", value=f_ju if f_ju else False)
    f_dan = c[2].checkbox("단독/다가구", key="f_dan", value=f_ju if f_ju else False)
    f_jeon = c[3].checkbox("전원주택", key="f_jeon", value=f_ju if f_ju else False)
    f_apt = c[4].checkbox("아파트", key="f_apt", value=f_ju if f_ju else False)
    f_op = c[5].checkbox("오피스텔(주거)", key="f_op", value=f_ju if f_ju else False)

    # 2. 비주거용 라인 (연동 기능 추가)
    b = st.columns([1, 1.2, 1, 1, 1.2, 1.5])
    f_bi = b[0].checkbox("비주거용", key="f_bi")
    f_sang = b[1].checkbox("상가/사무실", key="f_sang", value=f_bi if f_bi else False)
    f_gong = b[2].checkbox("공장/창고", key="f_gong", value=f_bi if f_bi else False)
    f_build = b[3].checkbox("빌딩/건물", key="f_build", value=f_bi if f_bi else False)
    f_jisik = b[4].checkbox("지식산업센터", key="f_jisik", value=f_bi if f_bi else False)
    f_etc_non = b[5].checkbox("기타", key="f_etc_non", value=f_bi if f_bi else False)

    # 3. 토지 라인 (연동 기능 추가)
    l = st.columns([1, 1, 1, 1, 1, 1.5])
    f_to = l[0].checkbox("토지", key="f_to")
    f_dae = l[1].checkbox("대지", key="f_dae", value=f_to if f_to else False)
    f_imya = l[2].checkbox("임야", key="f_imya", value=f_to if f_to else False)
    f_nong = l[3].checkbox("농지", key="f_nong", value=f_to if f_to else False)
    f_etc_land = l[4].checkbox("기타 ", key="f_etc_land", value=f_to if f_to else False)

    st.markdown("---")

    # 통합 의뢰목적 및 옵션 라인
    m = st.columns([1.5, 1.5, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7])
    f_sell_rent = m[0].checkbox("매도/임대", key="f_sell_rent")
    f_buy_lease = m[1].checkbox("매수/임차", key="f_buy_lease")
    
    f_r1 = m[2].checkbox("방1")
    f_r2 = m[3].checkbox("방2")
    f_r3 = m[4].checkbox("방3")
    f_r4 = m[5].checkbox("방4")
    f_b1 = m[6].checkbox("욕1")
    f_b2 = m[7].checkbox("욕2")
    f_b3 = m[8].checkbox("욕3")

# --- 데이터 필터링 로직 ---
df_display = st.session_state.data.copy()
selected_subs = []

# 소분류 체크박스 값들을 수집 (대분류와 연동됨)
if f_yeon: selected_subs.append("연립/다세대")
if f_dan: selected_subs.append("단독/다가구")
if f_jeon: selected_subs.append("전원주택")
if f_apt: selected_subs.append("아파트")
if f_op: selected_subs.append("오피스텔(주거)")
if f_sang: selected_subs.append("상가/사무실")
if f_gong: selected_subs.append("공장/창고")
if f_build: selected_subs.append("빌딩/건물")
if f_jisik: selected_subs.append("지식산업센터")
if f_etc_non: selected_subs.append("기타")
if f_dae: selected_subs.append("대지")
if f_imya: selected_subs.append("임야")
if f_nong: selected_subs.append("농지")
if f_etc_land: selected_subs.append("기타 ")

if selected_subs:
    selected_subs = list(set(selected_subs))
    df_display = df_display[df_display['item_sub_category'].isin(selected_subs)]

selected_purps = []
if f_sell_rent: selected_purps.extend(["매도", "임대"])
if f_buy_lease: selected_purps.extend(["매수", "임차"])

if selected_purps:
    df_display = df_display[df_display['purpose'].isin(selected_purps)]

if s_query:
    df_display = df_display[df_display.apply(lambda r: s_query in str(r.values), axis=1)]

st.subheader(f"📊 매물 목록 (총 {len(df_display)}건)")
st.dataframe(df_display.drop(columns=['id'], errors='ignore'), use_container_width=True, hide_index=True)

if st.button("🗑️ 전체 데이터 초기화"):
    if st.checkbox("정말 삭제하시겠습니까?"):
        st.session_state.data = create_empty_df()
        save_data(st.session_state.data)
        st.rerun()
