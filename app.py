import streamlit as st
import pandas as pd
from datetime import datetime

# --- 페이지 설정 ---
st.set_page_config(page_title="파크부동산 매물관리", layout="wide")

# --- 데이터 로드 (세션 상태 활용) ---
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=[
        "receipt_date", "item_category", "item_sub_category", 
        "purpose", "trade_type", "room_count", "bathroom_count", 
        "price", "address", "area", "description"
    ])

df = st.session_state.data

# --- 레이아웃 구성 ---
col_reg, col_list = st.columns([1, 2])

# --- 왼쪽: 매물 등록 (기존 라디오 버튼 유지) ---
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
        
        price = st.number_input("거래가액(만원)", min_value=0)
        address = st.text_input("소재지 상세")
        area = st.text_input("면적")
        description = st.text_area("특약내용")
        
        if st.form_submit_button("🏠 데이터베이스 저장"):
            new_row = pd.DataFrame([{
                "receipt_date": receipt_date, "item_category": item_category,
                "item_sub_category": item_sub_category, "purpose": purpose,
                "trade_type": trade_type, "room_count": room_count,
                "bathroom_count": bathroom_count, "price": price,
                "address": address, "area": area, "description": description
            }])
            st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
            st.rerun()

# --- 오른쪽: 매물 목록 및 체크박스 필터 ---
with col_list:
    st.title("🏘️ 파크부동산")
    
    # 상단 텍스트 검색
    search_query = st.text_input("🔍 키워드 검색", placeholder="소재지나 특약 내용을 입력하세요.")

    # --- 체크박스 필터 섹션 ---
    st.write("---")
    st.markdown("### ✅ 필터 선택 (복수 선택 가능)")

    def create_checkbox_filter(label, options):
        st.markdown(f"**{label}**")
        cols = st.columns(len(options))
        selected = []
        for i, option in enumerate(options):
            if cols[i].checkbox(option, key=f"{label}_{option}"):
                selected.append(option)
        return selected

    # 각 카테고리별 체크박스 생성
    filter_sub_cat = create_checkbox_filter("물건 소분류", ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택"])
    filter_purpose = create_checkbox_filter("의뢰목적", ["매도", "임대", "매수", "임차", "교환"])
    filter_trade = create_checkbox_filter("거래구분", ["매매", "전세", "월세"])
    
    st.write("") # 간격 조절
    
    col_r, col_b = st.columns(2)
    with col_r:
        filter_rooms = create_checkbox_filter("방 개수", ["방1", "방2", "방3", "방4 이상"])
    with col_b:
        filter_baths = create_checkbox_filter("화장실 개수", ["화장실1", "화장실2", "화장실3 이상"])

    # --- 데이터 필터링 로직 ---
    filtered_df = st.session_state.data.copy()

    if search_query:
        filtered_df = filtered_df[filtered_df.apply(lambda r: search_query in str(r.values), axis=1)]
    
    if filter_sub_cat:
        filtered_df = filtered_df[filtered_df['item_sub_category'].isin(filter_sub_cat)]
    if filter_purpose:
        filtered_df = filtered_df[filtered_df['purpose'].isin(filter_purpose)]
    if filter_trade:
        filtered_df = filtered_df[filtered_df['trade_type'].isin(filter_trade)]
    if filter_rooms:
        filtered_df = filtered_df[filtered_df['room_count'].isin(filter_rooms)]
    if filter_baths:
        filtered_df = filtered_df[filtered_df['bathroom_count'].isin(filter_baths)]

    # --- 결과 출력 ---
    st.write(f"**검색 결과:** {len(filtered_df)} 건")
    st.dataframe(filtered_df, use_container_width=True)
