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
            # id 컬럼이 문자열인 경우를 대비해 처리
            if 'id' in df.columns:
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
            # 중복 방지를 위해 아주 정교한 ID 생성 (시간 + 랜덤)
            new_id = f"{int(time.time() * 1000)}" 
            new_row = pd.DataFrame([{
                "id": new_id,
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
                "description": description,
                "status": "진행중"
            }])
            st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
            save_data(st.session_state.data)
            st.success("등록 완료!")
            st.rerun()
        else:
            st.error("주소를 입력해주세요.")

# --- [우측] 매물 목록 및 색인 파트 ---
with col_list:
    st.title("🏘️ 파크부동산 매물 대장")
    search_query = st.text_input("🔍 키워드 검색", placeholder="소재지나 특약 내용을 입력하세요.")

    st.write("---")
    st.markdown("### ✅ 필터 선택 (복수 선택 가능)")

    def create_checkbox_filter(label, options):
        st.markdown(f"**{label}**")
        cols = st.columns(len(options))
        selected = []
        for i, option in enumerate(options):
            if cols[i].checkbox(option, key=f"filter_{label}_{option}"):
                selected.append(option)
        return selected

    all_sub_options = ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택", 
                       "상가/사무실", "공장/창고", "빌딩/건물", "지식산업센터", "대지", "임야", "농지"]
    
    f_sub = create_checkbox_filter("물건 소분류", all_sub_options)
    f_pur = create_checkbox_filter("의뢰목적", ["매도", "임대", "매수", "임차", "교환"])
    f_tra = create_checkbox_filter("거래구분", ["매매", "전세", "월세"])
    
    df = st.session_state.data.copy()

    if search_query:
        df = df[df.apply(lambda r: search_query in str(r.values), axis=1)]
    if f_sub:
        df = df[df['item_sub_category'].isin(f_sub)]
    if f_pur:
        df = df[df['purpose'].isin(f_pur)]
    if f_tra:
        df = df[df['trade_type'].isin(f_tra)]

    tab_active, tab_done = st.tabs(["✅ 진행중 매물", "🏁 거래완료 목록"])
    
    with tab_active:
        active_df = df[df['status'] == "진행중"]
        if active_df.empty:
            st.info("조건에 맞는 매물이 없습니다.")
        else:
            for i, row in active_df.iterrows():
                # 버튼 키 중복 방지를 위해 row 인덱스(i)와 id를 조합
                with st.expander(f"📍 {row['address']} ({row['item_sub_category']} / {row['price']}만원)"):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.write(f"**접수일:** {row['receipt_date']} | **종류:** {row['trade_type']} | **면적:** {row['area']}")
                        st.write(f"**특약:** {row['description']}")
                    with c2:
                        # 중복 키 에러 방지를 위해 key값에 인덱스 i를 추가
                        if st.button("거래완료 처리", key=f"done_{row['id']}_{i}"):
                            st.session_state.data.loc[st.session_state.data['id'] == row['id'], 'status'] = "거래완료"
                            save_data(st.session_state.data)
                            st.rerun()
            st.dataframe(active_df, use_container_width=True)

    with tab_done:
        done_df = df[df['status'] == "거래완료"]
        st.dataframe(done_df, use_container_width=True)
        if not done_df.empty:
            if st.button("완료 목록 영구 삭제", key="clear_done_list"):
                st.session_state.data = st.session_state.data[st.session_state.data['status'] == "진행중"]
                save_data(st.session_state.data)
                st.rerun()
