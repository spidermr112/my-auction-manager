import streamlit as st
import pandas as pd
from datetime import datetime
import os
import re
import time

# --- 1. 페이지 설정 및 디자인 고정 ---
st.set_page_config(page_title="파크부동산 매물관리", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebar"] { min-width: 350px; max-width: 350px; }
    .stCheckbox label { white-space: nowrap !important; word-break: keep-all !important; min-width: max-content !important; }
    [data-testid="column"] { padding-right: 5px !important; padding-left: 5px !important; }
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
        except: return create_empty_df()
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
            return f"{price_str} (환산 {deposit + (monthly * 100)})"
        except: return price_str
    try:
        if price_str.isdigit(): return price_str
        result = 0
        eok = re.search(r'([\d\.]+)\s*억', price_str)
        if eok: result += float(eok.group(1)) * 10000
        cheon = re.search(r'([\d\.]+)\s*천', price_str)
        if cheon: result += float(cheon.group(1)) * 100
        return str(int(result)) if (eok or cheon) else re.sub(r'[^0-9]', '', price_str)
    except: return price_str

# 세션 초기화 및 연동 함수
if 'data' not in st.session_state: st.session_state.data = load_data()
if 'last_submit_time' not in st.session_state: st.session_state.last_submit_time = 0

# [중요] 대분류-소분류 연동 함수
def toggle_group(group_key, sub_keys):
    for k in sub_keys:
        st.session_state[k] = st.session_state[group_key]

# --- 3. 사이드바: 매물 등록 ---
with st.sidebar:
    st.title("📍 매물 등록")
    with st.form("registration_form", clear_on_submit=True):
        reg_date = st.date_input("접수일", datetime.now())
        reg_cat = st.radio("물건 대분류", ["주거용", "비주거용", "토지"], horizontal=True)
        subs = {
            "주거용": ["연립/다세대", "단독/다가구", "전원주택", "아파트", "오피스텔(주거)"],
            "비주거용": ["상가/사무실", "공장/창고", "빌딩/건물", "지식산업센터", "기타"],
            "토지": ["대지", "임야", "농지", "기타"]
        }[reg_cat]
        reg_sub = st.radio("물건 소분류", subs)
        reg_purp = st.radio("의뢰목적", ["매도", "임대", "매수", "임차", "교환"], horizontal=True)
        reg_trade = st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        reg_price_raw = st.text_input("거래가액", placeholder="예: 3억 5천 / 4000/35")
        reg_addr = st.text_input("소재지 상세")
        reg_area_raw = st.text_input("면적")
        reg_desc = st.text_area("특약내용")
        if st.form_submit_button("🏠 데이터베이스 저장"):
            current_time = time.time()
            if current_time - st.session_state.last_submit_time > 2.0:
                st.session_state.last_submit_time = current_time
                new_row = pd.DataFrame([{"id": f"P_{int(current_time * 1000)}", "receipt_date": reg_date, "item_category": reg_cat, "item_sub_category": reg_sub, "purpose": reg_purp, "trade_type": reg_trade, "price": parse_korean_price(reg_price_raw), "address": reg_addr or "(미입력)", "area": reg_area_raw or "(미입력)", "description": reg_desc, "status": "진행중"}])
                st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
                save_data(st.session_state.data)
                st.rerun()

# --- 4. 메인 화면: 통합 필터 및 목록 ---
st.title("🏘️ 파크부동산 통합 관리 시스템")
s_query = st.text_input("🔍 키워드 검색 (주소, 특약 등)", placeholder="검색어를 입력하세요.")

with st.expander("✅ 필터 상세 선택", expanded=True):
    # 1. 주거용 필터
    c = st.columns([1, 1.2, 1.2, 1, 1, 1.5])
    ju_subs = ["f_yeon", "f_dan", "f_jeon", "f_apt", "f_op"]
    f_ju = c[0].checkbox("주거용", key="f_ju", on_change=toggle_group, args=("f_ju", ju_subs))
    f_yeon = c[1].checkbox("연립/다세대", key="f_yeon")
    f_dan = c[2].checkbox("단독/다가구", key="f_dan")
    f_jeon = c[3].checkbox("전원주택", key="f_jeon")
    f_apt = c[4].checkbox("아파트", key="f_apt")
    f_op = c[5].checkbox("오피스텔(주거)", key="f_op")

    # 2. 비주거용 필터
    b = st.columns([1, 1.2, 1, 1, 1.2, 1.5])
    bi_subs = ["f_sang", "f_gong", "f_build", "f_jisik", "f_etc_non"]
    f_bi = b[0].checkbox("비주거용", key="f_bi", on_change=toggle_group, args=("f_bi", bi_subs))
    f_sang = b[1].checkbox("상가/사무실", key="f_sang")
    f_gong = b[2].checkbox("공장/창고", key="f_gong")
    f_build = b[3].checkbox("빌딩/건물", key="f_build")
    f_jisik = b[4].checkbox("지식산업센터", key="f_jisik")
    f_etc_non = b[5].checkbox("기타", key="f_etc_non")

    # 3. 토지 필터
    l = st.columns([1, 1, 1, 1, 1, 1.5])
    to_subs = ["f_dae", "f_imya", "f_nong", "f_etc_land"]
    f_to = l[0].checkbox("토지", key="f_to", on_change=toggle_group, args=("f_to", to_subs))
    f_dae = l[1].checkbox("대지", key="f_dae")
    f_imya = l[2].checkbox("임야", key="f_imya")
    f_nong = l[3].checkbox("농지", key="f_nong")
    f_etc_land = l[4].checkbox("기타", key="f_etc_land")

    st.divider()
    m = st.columns([1.5, 1.5, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7])
    f_sell_rent = m[0].checkbox("매도/임대", key="f_sell_rent")
    f_buy_lease = m[1].checkbox("매수/임차", key="f_buy_lease")
    f_r1, f_r2, f_r3, f_r4 = m[2].checkbox("방1"), m[3].checkbox("방2"), m[4].checkbox("방3"), m[5].checkbox("방4")
    f_b1, f_b2, f_b3 = m[6].checkbox("화1"), m[7].checkbox("화2"), m[8].checkbox("화3")

# 필터링 엔진
df_f = st.session_state.data.copy()

# 소분류 필터 수집
active_subs = []
sub_map = {
    f_yeon: "연립/다세대", f_dan: "단독/다가구", f_jeon: "전원주택", f_apt: "아파트", f_op: "오피스텔(주거)",
    f_sang: "상가/사무실", f_gong: "공장/창고", f_build: "빌딩/건물", f_jisik: "지식산업센터", f_etc_non: "기타",
    f_dae: "대지", f_imya: "임야", f_nong: "농지", f_etc_land: "기타"
}
for check, val in sub_map.items():
    if check: active_subs.append(val)

if active_subs:
    df_f = df_f[df_f['item_sub_category'].isin(active_subs)]

# 의뢰목적 필터 (매도/임대 등)
active_purps = []
if f_sell_rent: active_purps.extend(["매도", "임대"])
if f_buy_lease: active_purps.extend(["매수", "임차"])
if active_purps:
    df_f = df_f[df_f['purpose'].isin(active_purps)]

# 검색어 필터
if s_query:
    df_f = df_f[df_f.apply(lambda r: s_query.lower() in str(r.values).lower(), axis=1)]

st.subheader(f"📊 매물 목록 (총 {len(df_f)}건)")
st.dataframe(df_f.drop(columns=['id'], errors='ignore'), use_container_width=True, hide_index=True)
