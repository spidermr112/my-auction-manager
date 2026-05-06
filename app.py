import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time

# --- 페이지 설정 ---
st.set_page_config(page_title="파크부동산 매물관리", layout="wide")

# --- 데이터 영구 저장 로직 ---
DB_FILE = "property_data.csv"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            if 'receipt_date' in df.columns:
                df['receipt_date'] = pd.to_datetime(df['receipt_date']).dt.date
            if 'id' in df.columns:
                df['id'] = df['id'].astype(str)
            # 필수 컬럼 누락 방지
            required = ["id", "receipt_date", "item_category", "item_sub_category", "purpose", "trade_type", "price", "address", "area", "description", "status"]
            for col in required:
                if col not in df.columns:
                    df[col] = "N/A"
            return df
        except:
            return create_empty_df()
    else:
        return create_empty_df()

def create_empty_df():
    return pd.DataFrame(columns=["id", "receipt_date", "item_category", "item_sub_category", "purpose", "trade_type", "price", "address", "area", "description", "status"])

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
    
    receipt_date = st.date_input("접수일", datetime.now(), key="reg_date")
    item_category = st.radio("물건 대분류", ["주거용", "비주거용", "토지"], horizontal=True, key="reg_cat")
    
    if item_category == "주거용":
        sub_options = ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택"]
    elif item_category == "비주거용":
        sub_options = ["상가/사무실", "공장/창고", "빌딩/건물", "지식산업센터", "기타"]
    else:
        sub_options = ["대지", "임야", "농지", "기타"]
    
    item_sub_category = st.radio("물건 소분류", sub_options, horizontal=True, key="reg_sub_cat")
    purpose = st.radio("의뢰목적", ["매도", "임대", "매수", "임차", "교환"], horizontal=True, key="reg_purpose")
    trade_type = st.radio("구분", ["매매", "전세", "월세"], horizontal=True, key="reg_trade")
    
    price = st.number_input("거래가액(만원)", min_value=0, step=100, key="reg_price")
    address = st.text_input("소재지 상세", key="reg_addr")
    area = st.text_input("면적", key="reg_area")
    description = st.text_area("특약내용", key="reg_desc")
    
    if st.button("🏠 데이터베이스 저장", use_container_width=True, key="reg_btn"):
        if address:
            new_id = f"ID_{int(time.time() * 1000)}" 
            new_row = pd.DataFrame([{
                "id": new_id, "receipt_date": receipt_date, "item_category": item_category,
                "item_sub_category": item_sub_category, "purpose": purpose,
                "trade_type": trade_type, "price": price, "address": address, 
                "area": area, "description": description, "status": "진행중"
            }])
            st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
            save_data(st.session_state.data)
            st.success("등록 완료!")
            st.rerun()

# --- [우측] 매물 목록 및 필터 ---
with col_list:
    st.title("🏘️ 파크부동산 매물 대장")
    
    search_query = st.text_input("🔍 키워드 검색", placeholder="검색어를 입력하세요.", key="main_search")
    st.write("---")

    # 필터 섹션 (Duplicate Key 에러 방지 처리)
    st.markdown("### ✅ 필터 선택")
    
    def create_safe_filter(label, options):
        st.markdown(f"**{label}**")
        cols = st.columns(len(options))
        selected = []
        for i, option in enumerate(options):
            # key값에 label을 포함시켜 중복을 완전히 방지
            if cols[i].checkbox(option, key=f"filter_{label}_{option}_{i}"):
                selected.append(option)
        return selected

    all_subs = ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택", "상가/사무실", "공장/창고", "빌딩/건물", "지식산업센터", "대지", "임야", "농지"]
    f_sub = create_safe_filter("소분류", all_subs)

    # 데이터 필터링
    df = st.session_state.data.copy()
    if search_query:
        df = df[df.apply(lambda r: search_query in str(r.values), axis=1)]
    if f_sub:
        df = df[df['item_sub_category'].isin(f_sub)]

    tab1, tab2 = st.tabs(["✅ 진행중 매물", "🏁 거래완료 목록"])
    
    with tab1:
        active_df = df[df['status'] == "진행중"]
        if active_df.empty:
            st.info("매물이 없습니다.")
        else:
            for i, row in active_df.iterrows():
                with st.expander(f"📍 {row['address']} ({row['item_sub_category']} / {row['price']}만원)"):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.write(f"**구분:** {row['trade_type']} | **면적:** {row['area']} | **특약:** {row['description']}")
                    with c2:
                        if st.button("완료처리", key=f"done_btn_{row['id']}"):
                            st.session_state.data.loc[st.session_state.data['id'] == row['id'], 'status'] = "거래완료"
                            save_data(st.session_state.data)
                            st.rerun()
            st.dataframe(active_df, use_container_width=True, hide_index=True)

    with tab2:
        done_df = df[df['status'] == "거래완료"]
        st.dataframe(done_df, use_container_width=True, hide_index=True)
