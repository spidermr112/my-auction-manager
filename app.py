import streamlit as st
import pandas as pd
from datetime import datetime
import os
import re
import time

# --- 1. 페이지 설정 및 디자인 고정 ---
st.set_page_config(page_title="파크부동산 매물관리", layout="wide")

# --- 고급 디자인 CSS ---
st.markdown("""
    <style>
    /* 전체 배경색 및 폰트 */
    .main {
        background-color: #f8f9fa;
    }
    
    /* 사이드바 스타일링 */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #eee;
        min-width: 380px !important;
    }

    /* 카드형 매물 목록 스타일 */
    .property-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #007bff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    
    /* 강조 텍스트 */
    .price-text {
        color: #d63384;
        font-weight: bold;
        font-size: 1.2rem;
    }
    
    /* 뱃지 스타일 */
    .badge {
        padding: 4px 8px;
        border-radius: 5px;
        font-size: 0.8rem;
        font-weight: bold;
        margin-right: 5px;
    }
    .badge-blue { background-color: #e7f1ff; color: #007bff; }
    .badge-green { background-color: #e6ffed; color: #28a745; }
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
    return pd.DataFrame(columns=["id", "receipt_date", "item_category", "item_sub_category", "purpose", "trade_type", "price", "address", "area", "description", "status"])

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
        res = 0
        eok = re.search(r'([\d\.]+)\s*억', price_str)
        if eok: res += float(eok.group(1)) * 10000
        cheon = re.search(r'([\d\.]+)\s*천', price_str)
        if cheon: res += float(cheon.group(1)) * 100
        if not eok and not cheon:
            num = re.sub(r'[^0-9]', '', price_str)
            return num if num else "0"
        return str(int(res))
    except: return price_str

if 'data' not in st.session_state:
    st.session_state.data = load_data()

# --- 3. 사이드바: 매물 등록 (세련된 폼) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/602/602273.png", width=50)
    st.title("매물 등록")
    
    with st.form("reg_form", clear_on_submit=True):
        st.caption("새로운 매물 정보를 입력하세요")
        reg_date = st.date_input("📅 접수일", datetime.now())
        reg_cat = st.segmented_control("대분류", ["주거용", "비주거용", "토지"], default="주거용")
        
        subs = {
            "주거용": ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택"],
            "비주거용": ["상가/사무실", "공장/창고", "빌딩/건물", "지식산업센터", "기타"],
            "토지": ["대지", "임야", "농지", "기타"]
        }
        reg_sub = st.selectbox("물건 소분류", subs[reg_cat])
        
        c1, c2 = st.columns(2)
        with c1: reg_purp = st.selectbox("의뢰목적", ["매도", "임대", "매수", "임차"])
        with c2: reg_trade = st.selectbox("거래구분", ["매매", "전세", "월세"])
        
        reg_price = st.text_input("💰 거래가액", placeholder="예: 3억 5천 / 4000/35")
        reg_addr = st.text_input("📍 소재지 상세")
        reg_area = st.text_input("📐 면적 (평/㎡)", placeholder="예: 30평")
        reg_desc = st.text_area("📝 특약 및 상세내용")
        
        if st.form_submit_button("✨ 데이터베이스 저장", use_container_width=True):
            f_price = parse_korean_price(reg_price)
            f_area = reg_area
            if reg_area and '평' in reg_area:
                try:
                    num = float(re.sub(r'[^0-9.]', '', reg_area))
                    f_area = f"{round(num * 3.3058, 1)}㎡({num}평)"
                except: pass
                
            new_row = pd.DataFrame([{
                "id": str(time.time()), "receipt_date": reg_date, "item_category": reg_cat,
                "item_sub_category": reg_sub, "purpose": reg_purp, "trade_type": reg_trade,
                "price": f_price, "address": reg_addr if reg_addr else "주소 미입력",
                "area": f_area if f_area else "면적 미입력", "description": reg_desc, "status": "진행중"
            }])
            st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
            save_data(st.session_state.data)
            st.toast("매물이 성공적으로 등록되었습니다! 🎉")
            st.rerun()

# --- 4. 메인 화면: 매물 목록 (카드형 디자인) ---
st.title("🏘️ 파크부동산 매물 대장")

# 필터 및 검색
c1, c2 = st.columns([2, 1])
with c1:
    s_query = st.text_input("", placeholder="🔍 검색어를 입력하세요 (주소, 소분류, 특약 등)")
with c2:
    f_cat = st.multiselect("분류 필터", ["주거용", "비주거용", "토지"])

# 데이터 필터링
df = st.session_state.data.copy()
if s_query:
    df = df[df.apply(lambda r: s_query in str(r.values), axis=1)]
if f_cat:
    df = df[df['item_category'].isin(f_cat)]

# 목록 표시
if df.empty:
    st.info("등록된 매물이 없습니다. 왼쪽 사이드바에서 새 매물을 등록해 주세요.")
else:
    for _, row in df.iloc[::-1].iterrows(): # 최신순
        with st.container():
            st.markdown(f"""
                <div class="property-card">
                    <span class="badge badge-blue">{row['item_category']}</span>
                    <span class="badge badge-green">{row['item_sub_category']}</span>
                    <span style="float:right; color:#666; font-size:0.9rem;">📅 {row['receipt_date']}</span>
                    <h3 style="margin:10px 0;">{row['address']}</h3>
                    <p><b>구분:</b> {row['purpose']} / {row['trade_type']} | <b>면적:</b> {row['area']}</p>
                    <p class="price-text">가격: {row['price']}</p>
                    <div style="background:#f1f3f5; padding:10px; border-radius:5px; font-size:0.9rem; color:#444;">
                        💬 {row['description'] if row['description'] else "특약 내용 없음"}
                    </div>
                </div>
            """, unsafe_allow_html=True)

# 초기화 (관리자용)
with st.expander("⚙️ 시스템 관리"):
    if st.button("데이터 초기화"):
        st.session_state.data = create_empty_df()
        save_data(st.session_state.data)
        st.rerun()
