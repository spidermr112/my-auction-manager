import streamlit as st
import pandas as pd
from datetime import datetime
import os
import re
import time

# --- 1. 페이지 설정 및 디자인 고정 ---
st.set_page_config(page_title="파크부동산 매물관리", layout="wide")

# 사이드바 폭 고정 및 UI 가독성을 위한 CSS
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        min-width: 350px;
        max-width: 350px;
    }
    .filter-label {
        color: red;
        font-weight: bold;
        font-size: 16px;
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

# [필터 상세 선택 섹션 재구성]
with st.expander("✅ 필터 상세 선택", expanded=True):
    # 주거용 라인
    c1, c2, c3, c4, c5, c6 = st.columns([1, 1, 1.2, 1, 1, 4])
    with c1: st.markdown('<p class="filter-label">☑️ 주거용</p>', unsafe_allow_html=True)
    f_yeon = c2.checkbox("연립/다세대", key="f_yeon")
    f_dan = c3.checkbox("단독/다가구", key="f_dan")
    f_jeon = c4.checkbox("전원주택", key="f_jeon")
    f_apt = c5.checkbox("아파트", key="f_apt")
    f_op = c6.checkbox("오피스텔(주거)", key="f_op")

    # 비주거용 라인
    b1, b2, b3, b4, b5, b6 = st.columns([1, 1, 1, 1, 1, 4])
    with b1: st.markdown('<p class="filter-label">☑️ 비주거용</p>', unsafe_allow_html=True)
    f_sang = b2.checkbox("상가/사무실", key="f_sang")
    f_gong = b3.checkbox("공장/창고", key="f_gong")
    f_build = b4.checkbox("빌딩/건물", key="f_build")
    f_jisik = b5.checkbox("지식산업센터", key="f_jisik")
    f_etc_non = b6.checkbox("기타", key="f_etc_non")

    # 토지 라인
    l1, l2, l3, l4, l5, l6 = st.columns([1, 1, 1, 1, 1, 4])
    with l1: st.markdown('<p class="filter-label">☑️ 토지</p>', unsafe_allow_html=True)
    f_dae = l2.checkbox("대지", key="f_dae")
    f_imya = l3.checkbox("임야", key="f_imya")
    f_nong = l4.checkbox("농지", key="f_nong")
    f_etc_land = l5.checkbox("기타 ", key="f_etc_land")

    st.markdown("---")

    # 기능 통합 및 방/욕실 라인
    m1, m2, m3, m4, m5, m6, m7, m8, m9 = st.columns([1.5, 1.5, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7])
    f_sell_rent = m1.checkbox("매도/임대", key="f_sell_rent")
    f_buy_lease = m2.checkbox("매수/임차", key="f_buy_lease")
    
    # 방/욕실 선택 (기존 데이터 필터용)
    f_r1 = m3.checkbox("방1")
    f_r2 = m4.checkbox("방2")
    f_r3 = m5.checkbox("방3")
    f_r4 = m6.checkbox("방4")
    f_b1 = m7.checkbox("욕1")
    f_b2 = m8.checkbox("욕2")
    f_b3 = m9.checkbox("욕3")

# 필터링 로직 적용
df_display = st.session_state.data.copy()

# 1. 소분류 필터 수집
selected_subs = []
if f_apt: selected_subs.append("아파트")
if f_op: selected_subs.append("오피스텔(주거)")
if f_yeon: selected_subs.append("연립/다세대")
if f_dan: selected_subs.append("단독/다가구")
if f_jeon: selected_subs.append("전원주택")
if f_sang: selected_subs.append("상가/사무실")
if f_gong: selected_subs.append("공장/창고")
if f_build: selected_subs.append("빌딩/건물")
if f_jisik: selected_subs.append("지식산업센터")
if f_dae: selected_subs.append("대지")
if f_imya: selected_subs.append("임야")
if f_nong: selected_subs.append("농지")

if selected_subs:
    df_display = df_display[df_display['item_sub_category'].isin(selected_subs)]

# 2. 통합 의뢰목적 필터 수집
selected_purps = []
if f_sell_rent: selected_purps.extend(["매도", "임대"])
if f_buy_lease: selected_purps.extend(["매수", "임차"])

if selected_purps:
    df_display = df_display[df_display['purpose'].isin(selected_purps)]

# 3. 검색어 필터
if s_query:
    df_display = df_display[df_display.apply(lambda r: s_query in str(r.values), axis=1)]

# 결과 출력
st.subheader(f"📊 매물 목록 (총 {len(df_display)}건)")
st.dataframe(df_display.drop(columns=['id'], errors='ignore'), use_container_width=True, hide_index=True)

if st.button("🗑️ 전체 데이터 초기화"):
    if st.checkbox("정말 삭제하시겠습니까?"):
        st.session_state.data = create_empty_df()
        save_data(st.session_state.data)
        st.rerun()
