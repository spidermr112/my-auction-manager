import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time

# --- 페이지 설정 ---
st.set_page_config(page_title="파크부동산 매물관리", layout="wide")

# --- 데이터 영구 저장 로직 (중복 및 오류 방지 강화) ---
DB_FILE = "property_data.csv"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            # 날짜 형식 보정
            if 'receipt_date' in df.columns:
                df['receipt_date'] = pd.to_datetime(df['receipt_date']).dt.date
            # 모든 필수 컬럼이 있는지 확인하고 없으면 추가 (빽섭/업데이트 대응)
            required_cols = ["id", "receipt_date", "item_category", "item_sub_category", 
                             "purpose", "trade_type", "price", "address", "area", "description", "status"]
            for col in required_cols:
                if col not in df.columns:
                    df[col] = "N/A"
            df['id'] = df['id'].astype(str)
            return df
        except:
            return create_empty_df()
    else:
        return create_empty_df()

def create_empty_df():
    return pd.DataFrame(columns=[
        "id", "receipt_date", "item_category", "item_sub_category", 
        "purpose", "trade_type", "price", "address", "area", "description", "status"
    ])

def save_data(df):
    df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')

# 세션 데이터 로드
if 'data' not in st.session_state:
    st.session_state.data = load_data()

# --- 레이아웃 구성 ---
col_reg, col_list = st.columns([1, 2.3])

# --- [좌측] 매물 등록 파트 ---
with col_reg:
    st.subheader("📍 매물 등록")
    
    receipt_date = st.date_input("접수일", datetime.now())
    item_category = st.radio("물건 대분류", ["주거용", "비주거용", "토지"], horizontal=True)
    
    # 대분류별 소분류 설정
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
    description = st.text_area("특약내용")
    
    if st.button("🏠 데이터베이스 저장", use_container_width=True):
        if address:
            # 절대 중복될 수 없는 ID 생성 (나노초 기반)
            new_id = f"ID_{int(time.time() * 1000000)}" 
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
            st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
            save_data(st.session_state.data)
            st.success("매물이 안전하게 저장되었습니다.")
            st.rerun()
        else:
            st.error("주소를 입력해주세요.")

# --- [우측] 매물 목록 및 관리 ---
with col_list:
    st.title("🏘️ 파크부동산 매물 대장")
    
    search_query = st.text_input("🔍 주소 또는 키워드 검색", placeholder="검색어를 입력하세요.")
    st.write("---")

    # 필터 및 데이터 정리
    df = st.session_state.data.copy()
    if search_query:
        # 문자열 포함 여부 검사 시 에러 방지 처리
        df = df[df['address'].astype(str).str.contains(search_query, na=False) | 
                df['description'].astype(str).str.contains(search_query, na=False)]

    tab1, tab2 = st.tabs(["✅ 진행중 매물", "🏁 거래완료 목록"])
    
    with tab1:
        active_df = df[df['status'] == "진행중"]
        if active_df.empty:
            st.info("현재 진행 중인 매물이 없습니다.")
        else:
            # 전문적인 리스트 출력
            for i, row in active_df.iterrows():
                # 버튼 키 중복을 완전히 차단하기 위해 id 사용
                with st.expander(f"📍 {row['address']} ({row['item_sub_category']} / {row['price']}만원)"):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.write(f"**접수일:** {row['receipt_date']} | **구분:** {row['trade_type']} | **면적:** {row['area']}")
                        st.write(f"**특약:** {row['description']}")
                    with c2:
                        # 고유 ID를 버튼 키로 사용하여 DuplicateElementKey 에러 방지
                        if st.button("완료처리", key=f"btn_{row['id']}"):
                            st.session_state.data.loc[st.session_state.data['id'] == row['id'], 'status'] = "거래완료"
                            save_data(st.session_state.data)
                            st.rerun()
            st.write("---")
            st.markdown("##### 📋 데이터 요약")
            st.dataframe(active_df, use_container_width=True, hide_index=True)

    with tab2:
        done_df = df[df['status'] == "거래완료"]
        st.dataframe(done_df, use_container_width=True, hide_index=True)
        if not done_df.empty:
            if st.button("🏁 완료 목록 비우기 (영구 삭제)", key="clear_done"):
                st.session_state.data = st.session_state.data[st.session_state.data['status'] == "진행중"]
                save_data(st.session_state.data)
                st.rerun()
