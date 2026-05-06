import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="파크부동산 매물관리", layout="wide")

# --- [추가] 데이터 영구 저장 로직 ---
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
        "receipt_date", "item_category", "item_sub_category", 
        "purpose", "trade_type", "room_count", "bathroom_count", 
        "price", "address", "area", "description"
    ])

# 데이터 로드
if 'data' not in st.session_state:
    st.session_state.data = load_data()

# --- 레이아웃 구성 ---
col_reg, col_list = st.columns([1, 2])

# --- 왼쪽: 매물 등록 파트 (대표님 원본 코드 유지) ---
with col_reg:
    st.subheader("📍 매물 등록")
    
    receipt_date = st.date_input("접수일", datetime.now())
    item_category = st.radio("물건 대분류", ["주거용", "비주거용", "토지"], horizontal=True)
    
    if item_category == "주거용":
        sub_options = ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택"]
    elif item_category == "비주거용":
        sub_options = ["상가/사무실", "공장/창고", "빌딩/건물", "지식산업센터", "기타"]
    else:
        sub_options = ["대지", "임야", "농지", "기타"]
    
    item_sub_category = st.radio("물건 소분류", sub_options, horizontal=True)
    purpose = st.radio("의뢰목적", ["매도", "임대", "매수", "임차", "교환"], horizontal=True)
    trade_type = st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
    
    if item_category == "주거용":
        r_col, b_col = st.columns(2)
        with r_col:
            room_count = st.radio("방 개수", ["방1", "방2", "방3", "방4 이상"], horizontal=True)
        with b_col:
            bathroom_count = st.radio("화장실 개수", ["화장실1", "화장실2", "화장실3 이상"], horizontal=True)
    else:
        room_count = "N/A"
        bathroom_count = "N/A"
    
    price = st.number_input("거래가액(만원)", min_value=0, step=100)
    address = st.text_input("소재지 상세")
    area = st.text_input("면적")
    description = st.text_area("특약내용")
    
    if st.button("🏠 데이터베이스 저장"):
        if address:
            new_row = pd.DataFrame([{
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
            }])
            st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
            # 파일로 즉시 저장
            st.session_state.data.to_csv(DB_FILE, index=False, encoding='utf-8-sig')
            st.success(f"{item_sub_category} 등록 및 파일 저장 완료!")
            st.rerun()
        else:
            st.error("소재지 상세 주소를 입력해주세요.")

# --- 오른쪽: 매물 목록 및 색인 파트 (필터 기능 복구) ---
with col_list:
    st.title("🏘️ 파크부동산")
    
    search_query = st.text_input("🔍 키워드 검색", placeholder="소재지나 특약 내용을 입력하세요.")

    st.write("---")
    st.markdown("### ✅ 필터 선택 (복수 선택 가능)")

    def create_checkbox_filter(label, options):
        st.markdown(f"**{label}**")
        cols = st.columns(len(options))
        selected = []
        for i, option in enumerate(options):
            # 오류 방지를 위해 label과 option을 조합한 고유 key 부여
            if cols[i].checkbox(option, key=f"filter_{label}_{option}"):
                selected.append(option)
        return selected

    all_sub_options = ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택", 
                       "상가/사무실", "공장/창고", "빌딩/건물", "지식산업센터", "대지", "임야", "농지"]
    
    filter_sub_cat = create_checkbox_filter("물건 소분류", all_sub_options)
    filter_purpose = create_checkbox_filter("의뢰목적", ["매도", "임대", "매수", "임차", "교환"])
    filter_trade = create_checkbox_filter("거래구분", ["매매", "전세", "월세"])
    
    filtered_df = st.session_state.data.copy()

    if search_query:
        filtered_df = filtered_df[filtered_df.apply(lambda r: search_query in str(r.values), axis=1)]
    
    if filter_sub_cat:
        filtered_df = filtered_df[filtered_df['item_sub_category'].isin(filter_sub_cat)]
    if filter_purpose:
        filtered_df = filtered_df[filtered_df['purpose'].isin(filter_purpose)]
    if filter_trade:
        filtered_df = filtered_df[filtered_df['trade_type'].isin(filter_trade)]

    st.write(f"**검색 결과:** {len(filtered_df)} 건")
    
    # [수정] 오류가 났던 개별 버튼 방식을 빼고, 깔끔하게 데이터만 먼저 보여줍니다.
    st.dataframe(filtered_df, use_container_width=True)
    
    # 만약 꼭 삭제 기능이 필요하시면 아래 버튼 하나로 관리하는 게 안전합니다.
    if not filtered_df.empty:
        if st.button("🗑️ 현재 리스트 초기화 (전체 삭제)"):
            st.session_state.data = create_empty_df()
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)
            st.rerun()
