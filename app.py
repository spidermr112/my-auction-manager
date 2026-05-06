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
            # 필수 컬럼 체크 및 보정
            required = ["id", "receipt_date", "item_category", "item_sub_category", "purpose", "trade_type", "price", "address", "area", "description", "status"]
            for col in required:
                if col not in df.columns:
                    df[col] = "진행중" if col == "status" else "N/A"
            return df
        except:
            return create_empty_df()
    else:
        return create_empty_df()

def create_empty_df():
    return pd.DataFrame(columns=["id", "receipt_date", "item_category", "item_sub_category", "purpose", "trade_type", "price", "address", "area", "description", "status"])

def save_data(df):
    df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')

# 세션 데이터 초기화
if 'data' not in st.session_state:
    st.session_state.data = load_data()

# --- 레이아웃 구성 ---
col_reg, col_list = st.columns([1, 2.5])

# --- [좌측] 매물 등록 파트 ---
with col_reg:
    st.subheader("📍 매물 등록")
    
    # 각 위젯에 고유한 key 부여 (중복 방지)
    r_date = st.date_input("접수일", datetime.now(), key="reg_date_input")
    i_cat = st.radio("물건 대분류", ["주거용", "비주거용", "토지"], horizontal=True, key="reg_cat_radio")
    
    if i_cat == "주거용":
        sub_opts = ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택"]
    elif i_cat == "비주거용":
        sub_opts = ["상가/사무실", "공장/창고", "빌딩/건물", "지식산업센터", "기타"]
    else:
        sub_opts = ["대지", "임야", "농지", "기타"]
    
    i_sub_cat = st.radio("물건 소분류", sub_opts, horizontal=True, key="reg_sub_radio")
    i_purpose = st.radio("의뢰목적", ["매도", "임대", "매수", "임차", "교환"], horizontal=True, key="reg_purp_radio")
    i_trade = st.radio("구분", ["매매", "전세", "월세"], horizontal=True, key="reg_trade_radio")
    
    i_price = st.number_input("거래가액(만원)", min_value=0, step=100, key="reg_price_input")
    i_addr = st.text_input("소재지 상세", key="reg_addr_input")
    i_area = st.text_input("면적", key="reg_area_input")
    i_desc = st.text_area("특약내용", key="reg_desc_input")
    
    if st.button("🏠 데이터베이스 저장", use_container_width=True, key="main_save_btn"):
        if i_addr:
            # 절대 중복되지 않는 ID 생성
            unique_id = f"P_{int(time.time() * 1000)}"
            new_data = pd.DataFrame([{
                "id": unique_id, "receipt_date": r_date, "item_category": i_cat,
                "item_sub_category": i_sub_cat, "purpose": i_purpose,
                "trade_type": i_trade, "price": i_price, "address": i_addr, 
                "area": i_area, "description": i_desc, "status": "진행중"
            }])
            st.session_state.data = pd.concat([st.session_state.data, new_data], ignore_index=True)
            save_data(st.session_state.data)
            st.success("매물이 저장되었습니다!")
            st.rerun()
        else:
            st.error("상세 주소를 입력해주세요.")

# --- [우측] 매물 목록 및 필터 파트 ---
with col_list:
    st.title("🏘️ 파크부동산 매물 대장")
    
    # 1. 검색 및 필터 (레이아웃 깨짐 방지를 위해 멀티셀렉트 권장)
    s_query = st.text_input("🔍 키워드 검색 (주소/특약)", placeholder="검색어를 입력하세요.", key="search_bar")
    
    st.markdown("### ✅ 필터링")
    f1, f2 = st.columns(2)
    with f1:
        # 체크박스 대신 멀티셀렉트를 사용하면 레이아웃이 절대 깨지지 않고 오류도 없습니다.
        all_subs = ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택", "상가/사무실", "공장/창고", "빌딩/건물", "지식산업센터", "대지", "임야", "농지"]
        sel_sub = st.multiselect("물건 소분류 선택", all_subs, key="filter_sub_ms")
    with f2:
        sel_trade = st.multiselect("거래 구분 선택", ["매매", "전세", "월세"], key="filter_trade_ms")

    # 데이터 필터링 로직
    df_view = st.session_state.data.copy()
    if s_query:
        df_view = df_view[df_view.apply(lambda r: s_query in str(r.values), axis=1)]
    if sel_sub:
        df_view = df_view[df_view['item_sub_category'].isin(sel_sub)]
    if sel_trade:
        df_view = df_view[df_view['trade_type'].isin(sel_trade)]

    # 2. 탭 구성
    t_active, t_done = st.tabs(["✅ 진행중 매물", "🏁 거래완료 목록"])
    
    with t_active:
        active_items = df_view[df_view['status'] == "진행중"]
        if active_items.empty:
            st.info("조건에 맞는 매물이 없습니다.")
        else:
            for idx, row in active_items.iterrows():
                # expander와 버튼에 고유한 key(id) 부여
                with st.expander(f"📍 {row['address']} ({row['item_sub_category']} / {row['price']}만원)", expanded=False):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.write(f"**구분:** {row['trade_type']} | **면적:** {row['area']} | **접수:** {row['receipt_date']}")
                        st.write(f"**특약:** {row['description']}")
                    with c2:
                        # row['id']를 활용해 버튼 키 중복 완전 차단
                        if st.button("완료처리", key=f"finish_btn_{row['id']}"):
                            st.session_state.data.loc[st.session_state.data['id'] == row['id'], 'status'] = "거래완료"
                            save_data(st.session_state.data)
                            st.rerun()
            st.write("---")
            st.dataframe(active_items, use_container_width=True, hide_index=True)

    with t_done:
        done_items = df_view[df_view['status'] == "거래완료"]
        st.dataframe(done_items, use_container_width=True, hide_index=True)
        if not done_items.empty:
            if st.button("완료 내역 전체 삭제", key="clear_db_btn"):
                st.session_state.data = st.session_state.data[st.session_state.data['status'] == "진행중"]
                save_data(st.session_state.data)
                st.rerun()
