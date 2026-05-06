import streamlit as st
import pandas as pd
from datetime import datetime
import os
import re

# --- 1. 페이지 설정 및 강제 너비 고정 (CSS 최우선 순위 적용) ---
st.set_page_config(page_title="파크부동산 매물관리", layout="wide")

st.markdown("""
    <style>
    /* 전체 배경 및 컨테이너 여백 */
    .block-container {
        padding: 1.5rem 2rem !important;
        max-width: 100% !important;
    }

    /* [원인 해결] 스트림릿의 컬럼 컨테이너 자체를 Grid로 강제 변환 */
    [data-testid="stHorizontalBlock"] {
        display: grid !important;
        grid-template-columns: 800px 1fr !important; /* 좌측 800px, 우측 나머지 */
        gap: 2rem !important;
        width: 100% !important;
    }

    /* [원인 해결] 개별 컬럼의 Flex 비율을 완전히 끄고 너비 박제 */
    [data-testid="column"]:nth-of-type(1) {
        width: 800px !important;
        min-width: 800px !important;
        max-width: 800px !important;
        flex: none !important;
    }

    [data-testid="column"]:nth-of-type(2) {
        width: 100% !important;
        flex: 1 !important;
    }

    /* 폼(Form) 테두리와 내부 내용물도 800px에 맞게 꽉 채우기 */
    [data-testid="stForm"] {
        width: 100% !important;
        padding: 2rem !important;
    }

    /* 라디오 버튼들이 800px 안에서 넉넉하게 가로로 배치되도록 설정 */
    div[role="radiogroup"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: wrap !important;
        gap: 15px !important;
        justify-content: flex-start !important;
    }
    
    div[role="radiogroup"] label {
        flex: 0 0 auto !important;
        margin-right: 10px !important;
        white-space: nowrap !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 데이터 관리 로직 (기능은 절대 수정하지 않았습니다) ---
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

# --- 3. 화면 배치 ---
col_reg, col_list = st.columns([1, 1]) # CSS Grid가 제어하므로 설정값은 무시됩니다.

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
            c_inner1, c_inner2 = st.columns(2)
            with c_inner1: reg_room = st.radio("방 개수", ["방1", "방2", "방3", "방4↑"], horizontal=True)
            with c_inner2: reg_bath = st.radio("화장실", ["화장실1", "화장실2", "화장실3↑"], horizontal=True)
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
