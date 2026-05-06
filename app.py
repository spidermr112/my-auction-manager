import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time

# --- 페이지 설정 ---
st.set_page_config(page_title="파크부동산 매물관리", layout="wide")

# --- [핵심] 데이터 영구 저장 로직 ---
DB_FILE = "property_data.csv"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            if 'receipt_date' in df.columns:
                df['receipt_date'] = pd.to_datetime(df['receipt_date']).dt.date
            if 'id' not in df.columns: # ID가 없으면 생성 (버튼 에러 방지용)
                df['id'] = [f"ID_{int(time.time())}_{i}" for i in range(len(df))]
            df['id'] = df['id'].astype(str)
            return df
        except:
            return create_empty_df()
    else:
        return create_empty_df()

def create_empty_df():
    return pd.DataFrame(columns=[
        "id", "receipt_date", "item_category", "item_sub_category", 
        "purpose", "trade_type", "room_count", "bathroom_count", 
        "price", "address", "area", "description", "status"
    ])

def save_data(df):
    df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')

# 세션 상태 초기화
if 'data' not in st.session_state:
    st.session_state.data = load_data()

# --- 레이아웃 구성 ---
col_reg, col_list = st.columns([1, 2])

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
    
    item_sub_category = st.radio("물건 소분류", sub_options, horizontal=True, key="reg_sub")
    purpose = st.radio("의뢰목적", ["매도", "임대", "매수", "임차", "교환"], horizontal=True, key="reg_purp")
    trade_type = st.radio("구분", ["매매", "전세", "월세"], horizontal=True, key="reg_trade")
    
    if item_category == "주거용":
        r_col, b_col = st.columns(2)
        with r_col:
            room_count = st.radio("방 개수", ["방1", "방2", "방3", "방4 이상"], horizontal=True, key="reg_room")
        with b_col:
            bathroom_count = st.radio("화장실 개수", ["화장실1", "화장실2", "화장실3 이상"], horizontal=True, key="reg_bath")
    else:
        room_count, bathroom_count = "N/A", "N/A"
    
    price = st.number_input("거래가액(만원)", min_value=0, step=100, key="reg_price")
    address = st.text_input("소재지 상세", key="reg_addr")
    area = st.text_input("면적", key="reg_area")
    description = st.text_area("특약내용", key="reg_desc")
    
    if st.button("🏠 데이터베이스 저장", use_container_width=True):
        if address:
            new_id = f"ID_{int(time.time() * 1000)}"
            new_row = pd.DataFrame([{
                "id": new_id, "receipt_date": receipt_date, "item_category": item_category,
                "item_sub_category": item_sub_category, "purpose": purpose,
                "trade_type": trade_type, "room_count": room_count,
                "bathroom_count": bathroom_count, "price": price,
                "address": address, "area": area, "description": description, "status": "진행중"
            }])
            st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
            save_data(st.session_state.data) # 파일 저장
            st.success("매물 등록 및 파일 저장 완료!")
            st.rerun()
        else:
            st.error("소재지 주소를 입력해주세요.")

# --- [우측] 매물 목록 및 색인 파트 (체크박스 필터 완벽 복구) ---
with col_list:
    st.title("🏘️ 파크부동산")
    search_query = st.text_input("🔍 키워드 검색", placeholder="소재지나 특약 내용을 입력하세요.", key="main_search")

    st.write("---")
    st.markdown("### ✅ 필터 선택 (복수 선택 가능)")

    def create_checkbox_filter(label, options):
        st.markdown(f"**{label}**")
        cols = st.columns(len(options))
        selected = []
        for i, option in enumerate(options):
            if cols[i].checkbox(option, key=f"f_{label}_{option}"):
                selected.append(option)
        return selected

    all_subs = ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택", "상가/사무실", "공장/창고", "빌딩/건물", "지식산업센터", "대지", "임야", "농지"]
    f_sub_cat = create_checkbox_filter("물건 소분류", all_subs)
    f_purpose = create_checkbox_filter("의뢰목적", ["매도", "임대", "매수", "임차", "교환"])
    f_trade = create_checkbox_filter("거래구분", ["매매", "전세", "월세"])
    
    # 필터링 로직
    df_filtered = st.session_state.data.copy()
    if search_query:
        df_filtered = df_filtered[df_filtered.apply(lambda r: search_query in str(r.values), axis=1)]
    if f_sub_cat:
        df_filtered = df_filtered[df_filtered['item_sub_category'].isin(f_sub_cat)]
    if f_purpose:
        df_filtered = df_filtered[df_filtered['purpose'].isin(f_purpose)]
    if f_trade:
        df_filtered = df_filtered[df_filtered['trade_type'].isin(f_trade)]

    # 리스트 출력 (가독성 좋게 탭으로 구분)
    t1, t2 = st.tabs(["📋 진행중 매물", "✅ 거래완료 목록"])
    
    with t1:
        active_df = df_filtered[df_filtered['status'] == "진행중"]
        st.write(f"**검색 결과:** {len(active_df)} 건")
        
        # 목록이 너무 길지 않게 개별 매물 관리
        for i, row in active_df.iterrows():
            with st.expander(f"📍 {row['address']} ({row['item_sub_category']} / {row['price']}만원)"):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.write(f"**종류:** {row['trade_type']} | **면적:** {row['area']} | **접수:** {row['receipt_date']}")
                    st.write(f"**특약:** {row['description']}")
                with c2:
                    if st.button("완료", key=f"btn_done_{row['id']}"):
                        st.session_state.data.loc[st.session_state.data['id'] == row['id'], 'status'] = "거래완료"
                        save_data(st.session_state.data)
                        st.rerun()
        st.dataframe(active_df, use_container_width=True, hide_index=True)

    with t2:
        done_df = df_filtered[df_filtered['status'] == "거래완료"]
        st.dataframe(done_df, use_container_width=True, hide_index=True)
        if st.button("🏁 완료 목록 비우기", key="clear_done"):
            st.session_state.data = st.session_state.data[st.session_state.data['status'] == "진행중"]
            save_data(st.session_state.data)
            st.rerun()
