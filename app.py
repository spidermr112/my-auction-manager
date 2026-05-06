import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="파크부동산 매물관리", layout="wide")

# --- 데이터 로드 및 영구 저장 로직 ---
DB_FILE = "property_data.csv"

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        # 날짜 데이터 형식 변환
        df['receipt_date'] = pd.to_datetime(df['receipt_date']).dt.date
        return df
    else:
        return pd.DataFrame(columns=[
            "id", "receipt_date", "item_category", "item_sub_category", 
            "purpose", "trade_type", "price", "address", "area", "description", "status"
        ])

def save_data(df):
    df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')

# 세션 상태에 데이터 로드 (최초 1회)
if 'data' not in st.session_state:
    st.session_state.data = load_data()

# --- 레이아웃 구성 ---
col_reg, col_list = st.columns([1, 2.5])

# --- [좌측] 매물 등록 파트 ---
with col_reg:
    st.subheader("📍 신규 매물 등록")
    
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
    
    price = st.number_input("거래가액(만원)", min_value=0, step=100)
    address = st.text_input("소재지 상세")
    area = st.text_input("면적")
    description = st.text_area("특약 및 분석내용")
    
    if st.button("🏠 데이터베이스 저장"):
        if address:
            # ID 생성을 위한 로직
            new_id = int(datetime.now().timestamp()) 
            new_row = pd.DataFrame([{
                "id": new_id,
                "receipt_date": receipt_date, 
                "item_category": item_category,
                "item_sub_category": item_sub_category, 
                "purpose": purpose,
                "trade_type": trade_type, 
                "price": price,
                "address": address, 
                "area": area, 
                "description": description,
                "status": "진행중"
            }])
            # 데이터 합치기 및 파일 저장
            st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
            save_data(st.session_state.data)
            st.success("데이터가 안전하게 파일로 저장되었습니다!")
            st.rerun()
        else:
            st.error("주소를 입력해주세요.")

# --- [우측] 매물 목록 및 색인 파트 ---
with col_list:
    st.title("🏘️ 파크부동산 매물 대장")
    search_query = st.text_input("🔍 키워드 검색", placeholder="검색어를 입력하세요.")
    st.write("---")
    
    if not st.session_state.data.empty:
        display_df = st.session_state.data.copy()
        
        if search_query:
            display_df = display_df[display_df['address'].str.contains(search_query, na=False)]

        tab1, tab2 = st.tabs(["✅ 진행중 매물", "🏁 거래완료 목록"])
        
        with tab1:
            active_items = display_df[display_df['status'] == "진행중"]
            if active_items.empty:
                st.info("현재 진행 중인 매물이 없습니다.")
            else:
                for i, row in active_items.iterrows():
                    with st.expander(f"📍 {row['address']} [{row['item_sub_category']}] - {row['price']}만원"):
                        c1, c2 = st.columns([4, 1])
                        with c1:
                            st.write(f"**종류:** {row['trade_type']} | **면적:** {row['area']}")
                        with c2:
                            if st.button("거래완료", key=f"done_{row['id']}"):
                                st.session_state.data.loc[st.session_state.data['id'] == row['id'], 'status'] = "거래완료"
                                save_data(st.session_state.data) # 변경사항 저장
                                st.rerun()
                st.dataframe(active_items, use_container_width=True)

        with tab2:
            completed_items = display_df[display_df['status'] == "거래완료"]
            st.dataframe(completed_items, use_container_width=True)
    else:
        st.info("등록된 매물이 없습니다.")
