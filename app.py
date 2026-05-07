import streamlit as st
import pandas as pd
from datetime import datetime
import os
import re
import time

# --- 1. 페이지 설정 및 디자인 고정 ---
st.set_page_config(page_title="파크부동산 통합 관리 시스템", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebar"] { min-width: 350px; max-width: 350px; }
    .stCheckbox label { white-space: nowrap !important; word-break: keep-all !important; min-width: max-content !important; }
    div[data-testid="stExpander"] { background-color: white; border-radius: 10px; border: 1px solid #e6e9ef; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 데이터 관리 로직 (기존 로직 유지) ---
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
        "purpose", "trade_type", "price", "address", "area", "description", "status"
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

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'last_submit_time' not in st.session_state: st.session_state.last_submit_time = 0

def toggle_group(group_key, sub_keys):
    for k in sub_keys:
        st.session_state[k] = st.session_state[group_key]

# --- 3. 메인 화면 상단: 매물 등록 (Expander 적용) ---
st.title("🏘️ 파크부동산 통합 관리 시스템")

# [변경사항] 사이드바에 있던 폼을 메인 상단 접이식으로 이동하여 목록 공간 확보
with st.expander("➕ 새 매물 등록하기 (클릭하여 입력창 열기)", expanded=False):
    with st.form("registration_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            reg_date = st.date_input("접수일", datetime.now())
            reg_cat = st.radio("물건 대분류", ["주거용", "비주거용", "토지"], horizontal=True)
            reg_purp = st.radio("의뢰목적", ["매도", "임대", "매수", "임차"], horizontal=True)
        with col2:
            subs = {
                "주거용": ["연립/다세대", "단독/다가구", "전원주택", "아파트", "오피스텔(주거)"],
                "비주거용": ["상가/사무실", "공장/창고", "빌딩/건물", "지식산업센터", "기타"],
                "토지": ["대지", "임야", "농지", "기타"]
            }[reg_cat]
            reg_sub = st.selectbox("물건 소분류", subs)
            reg_trade = st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
            reg_price_raw = st.text_input("거래가액", placeholder="예: 3억 5천 / 4000/35")
        with col3:
            reg_addr = st.text_input("소재지 상세")
            reg_area_raw = st.text_input("면적")
            reg_desc = st.text_area("특약내용", height=100)
            
        if st.form_submit_button("🏠 데이터베이스 저장", type="primary"):
            current_time = time.time()
            if current_time - st.session_state.last_submit_time > 1.5:
                st.session_state.last_submit_time = current_time
                new_row = pd.DataFrame([{
                    "id": f"P_{int(current_time * 1000)}", 
                    "receipt_date": reg_date, 
                    "item_category": reg_cat, 
                    "item_sub_category": reg_sub, 
                    "purpose": reg_purp, 
                    "trade_type": reg_trade, 
                    "price": parse_korean_price(reg_price_raw), 
                    "address": reg_addr or "(미입력)", 
                    "area": reg_area_raw or "(미입력)", 
                    "description": reg_desc, 
                    "status": "진행중"
                }])
                st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
                save_data(st.session_state.data)
                st.rerun()

st.divider()

# --- 4. 검색 및 필터 섹션 ---
s_query = st.text_input("🔍 키워드 검색 (주소, 특약 등)", placeholder="검색어를 입력하세요.")

with st.expander("✅ 상세 필터 선택", expanded=True):
    # 기존 필터 로직 유지
    c = st.columns([1, 1.2, 1.2, 1, 1, 1.5])
    f_ju = c[0].checkbox("주거용", key="f_ju", on_change=toggle_group, args=("f_ju", ["f_yeon", "f_dan", "f_jeon", "f_apt", "f_op"]))
    f_yeon, f_dan, f_jeon, f_apt, f_op = c[1].checkbox("연립/다세대", key="f_yeon"), c[2].checkbox("단독/다가구", key="f_dan"), c[3].checkbox("전원주택", key="f_jeon"), c[4].checkbox("아파트", key="f_apt"), c[5].checkbox("오피스텔(주거)", key="f_op")

    b = st.columns([1, 1.2, 1, 1, 1.2, 1.5])
    f_bi = b[0].checkbox("비주거용", key="f_bi", on_change=toggle_group, args=("f_bi", ["f_sang", "f_gong", "f_build", "f_jisik", "f_etc_non"]))
    f_sang, f_gong, f_build, f_jisik, f_etc_non = b[1].checkbox("상가/사무실", key="f_sang"), b[2].checkbox("공장/창고", key="f_gong"), b[3].checkbox("빌딩/건물", key="f_build"), b[4].checkbox("지식산업센터", key="f_jisik"), b[5].checkbox("기타", key="f_etc_non")

# 필터링 엔진
df_f = st.session_state.data.copy()
active_subs = []
sub_map = {f_yeon: "연립/다세대", f_dan: "단독/다가구", f_jeon: "전원주택", f_apt: "아파트", f_op: "오피스텔(주거)", f_sang: "상가/사무실", f_gong: "공장/창고", f_build: "빌딩/건물", f_jisik: "지식산업센터", f_etc_non: "기타"}
for check, val in sub_map.items():
    if check: active_subs.append(val)
if active_subs: df_f = df_f[df_f['item_sub_category'].isin(active_subs)]
if s_query: df_f = df_f[df_f.apply(lambda r: s_query.lower() in str(r.values).lower(), axis=1)]

# --- 5. [개선] 데이터프레임 스타일링 및 출력 ---
st.subheader(f"📊 매물 목록 (조회 결과: {len(df_f)}건)")

# 상태별 행 스타일 정의 함수
def apply_row_style(row):
    if row['status'] == '계약완료':
        return ['background-color: #f1f3f5; color: #adb5bd; text-decoration: line-through'] * len(row)
    elif row['status'] == '보류':
        return ['background-color: #fff9db; color: #856404'] * len(row)
    return [''] * len(row)

# 데이터프레임 시각화
st.dataframe(
    df_f.drop(columns=['id'], errors='ignore').style.apply(apply_row_style, axis=1),
    use_container_width=True,
    hide_index=True,
    column_config={
        "receipt_date": st.column_config.DateColumn("접수일"),
        "item_sub_category": "소분류",
        "purpose": "의뢰",
        "trade_type": "구분",
        "price": st.column_config.TextColumn("가액", width="medium"),
        "status": st.column_config.SelectboxColumn(
            "상태", options=["진행중", "계약완료", "보류"], required=True
        ),
        "address": st.column_config.TextColumn("주소", width="large"),
        "description": st.column_config.TextColumn("특약내용", width="large")
    }
)
