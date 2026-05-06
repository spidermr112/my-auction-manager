import streamlit as st
import pandas as pd
from datetime import datetime

# --- 페이지 설정 ---
st.set_page_config(page_title="파크부동산 매물관리", layout="wide")

# --- 데이터 로드 (예시 데이터를 사용하거나 실제 DB 연결) ---
# 실제 환경에서는 st.connection이나 gspread 등을 사용하시겠지만, 
# 코드 구현을 위해 샘플 데이터 구조를 생성합니다.
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=[
        "receipt_date", "item_category", "item_sub_category", 
        "purpose", "trade_type", "room_count", "bathroom_count", 
        "price", "address", "area", "description"
    ])

df = st.session_state.data

# --- 레이아웃 구성 ---
col_reg, col_list = st.columns([1, 2])

# --- 왼쪽: 매물 등록 섹션 (기존 기능 유지) ---
with col_reg:
    st.subheader("📍 매물 등록")
    with st.form("registration_form", clear_on_submit=True):
        receipt_date = st.date_input("접수일", datetime.now())
        item_category = st.radio("물건 대분류", ["주거용", "비주거용", "토지"], horizontal=True)
        item_sub_category = st.radio("물건 소분류", ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택"], horizontal=True)
        purpose = st.radio("의뢰목적", ["매도", "임대", "매수", "임차", "교환"], horizontal=True)
        trade_type = st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        room_count = st.radio("방 개수", ["방1", "방2", "방3", "방4 이상"], horizontal=True)
        bathroom_count = st.radio("화장실 개수", ["화장실1", "화장실2", "화장실3 이상"], horizontal=True)
        
        price = st.number_input("거래가액(만원)", min_value=0, step=100)
        address = st.text_input("소재지 상세")
        area = st.text_input("면적 (평 또는 ㎡ 입력)")
        description = st.text_area("특약 및 분석내용")
        
        submit_btn = st.form_submit_button("🏠 데이터베이스 저장")
        
        if submit_btn:
            new_data = {
                "receipt_date": receipt_date,
                "item_category": item_category,
                "item_sub_category": item_sub_category,
                "purpose": purpose,
                "trade_type": trade_type,
                "room_count": room_count,
                "bathroom_count": bathroom_count,
                "price": price,
                "address": address,
                "area": area,
                "description": description
            }
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_data])], ignore_index=True)
            st.success("매물이 등록되었습니다!")
            st.rerun()

# --- 오른쪽: 매물 목록 및 색인 섹션 ---
with col_list:
    st.title("🏘️ 파크부동산")
    
    # 1. 상단 키워드 검색
    search_query = st.text_input("🔍 무엇을 찾으실까요? (예: 아파트 매매 20평이상)", placeholder="키워드 검색...")

    # 2. 하단 상세 색인 필터 (요청하신 복수 선택 박스)
    st.write("---")
    st.markdown("#### 🔎 상세 필터링 (복수 선택 가능)")
    
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        sel_sub_cat = st.multiselect("물건 소분류", ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택"])
    with f_col2:
        sel_purpose = st.multiselect("의뢰목적", ["매도", "임대", "매수", "임차", "교환"])
    with f_col3:
        sel_trade = st.multiselect("거래구분", ["매매", "전세", "월세"])

    f_col4, f_col5 = st.columns(2)
    with f_col4:
        sel_rooms = st.multiselect("방 개수", ["방1", "방2", "방3", "방4 이상"])
    with f_col5:
        sel_baths = st.multiselect("화장실 개수", ["화장실1", "화장실2", "화장실3 이상"])

    # --- 필터링 로직 적용 ---
    filtered_df = st.session_state.data.copy()

    # 키워드 검색 필터
    if search_query:
        filtered_df = filtered_df[filtered_df.apply(lambda row: search_query in str(row.values), axis=1)]

    # 멀티셀렉트 박스 필터 (선택된 항목이 있을 때만 작동)
    if sel_sub_cat:
        filtered_df = filtered_df[filtered_df['item_sub_category'].isin(sel_sub_cat)]
    if sel_purpose:
        filtered_df = filtered_df[filtered_df['purpose'].isin(sel_purpose)]
    if sel_trade:
        filtered_df = filtered_df[filtered_df['trade_type'].isin(sel_trade)]
    if sel_rooms:
        filtered_df = filtered_df[filtered_df['room_count'].isin(sel_rooms)]
    if sel_baths:
        filtered_df = filtered_df[filtered_df['bathroom_count'].isin(sel_baths)]

    # 결과 출력
    st.write(f"**검색 결과:** {len(filtered_df)} 건")
    st.dataframe(filtered_df, use_container_width=True)
