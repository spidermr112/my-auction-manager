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
            # 필수 컬럼 보완
            for col in ["id", "receipt_date", "item_category", "item_sub_category", "purpose", "trade_type", "price", "address", "area", "description", "status"]:
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

# --- 레이아웃 구성 (좌: 입력 / 우: 목록) ---
col_reg, col_list = st.columns([1, 2.8])

# --- [좌측] 매물 등록 (빠른 입력을 위해 깔끔하게 정리) ---
with col_reg:
    st.subheader("📍 신규 매물 등록")
    with st.container(border=True):
        reg_date = st.date_input("접수일", datetime.now(), key="k_date")
        reg_cat = st.radio("대분류", ["주거용", "비주거용", "토지"], horizontal=True, key="k_cat")
        
        if reg_cat == "주거용":
            subs = ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택"]
        elif reg_cat == "비주거용":
            subs = ["상가/사무실", "공장/창고", "빌딩/건물", "지식산업센터", "기타"]
        else:
            subs = ["대지", "임야", "농지", "기타"]
        
        reg_sub = st.selectbox("소분류", subs, key="k_sub")
        reg_trade = st.radio("거래구분", ["매매", "전세", "월세"], horizontal=True, key="k_trade")
        reg_price = st.number_input("거래금액(만원)", min_value=0, step=1000, key="k_price")
        reg_addr = st.text_input("상세주소", key="k_addr")
        reg_area = st.text_input("면적(평/㎡)", key="k_area")
        reg_desc = st.text_area("특약사항", key="k_desc")
        
        if st.button("💾 매물 저장", use_container_width=True, key="k_save_btn"):
            if reg_addr:
                new_id = f"P{int(time.time())}"
                new_row = pd.DataFrame([{
                    "id": new_id, "receipt_date": reg_date, "item_category": reg_cat,
                    "item_sub_category": reg_sub, "purpose": "매도", # 기본값
                    "trade_type": reg_trade, "price": reg_price, "address": reg_addr, 
                    "area": reg_area, "description": reg_desc, "status": "진행중"
                }])
                st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
                save_data(st.session_state.data)
                st.success("저장 완료!")
                st.rerun()

# --- [우측] 매물 목록 (전문가용 표 형식) ---
with col_list:
    st.title("🏘️ 파크부동산 통합 관리 대장")
    
    # 1. 통합 검색 및 필터 (체크박스 대신 멀티셀렉트로 깔끔하게)
    with st.container(border=True):
        f1, f2 = st.columns([2, 1])
        with f1:
            search_q = st.text_input("🔍 주소/특약 키워드 검색", placeholder="검색어를 입력하세요.", key="k_search")
        with f2:
            all_list = ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택", "상가/사무실", "공장/창고", "빌딩/건물", "지식산업센터", "대지", "임야", "농지"]
            sel_sub = st.multiselect("소분류 필터", all_list, key="k_filter_sub")

    # 데이터 필터링 로직
    df = st.session_state.data.copy()
    if search_q:
        df = df[df.apply(lambda r: search_q in str(r.values), axis=1)]
    if sel_sub:
        df = df[df['item_sub_category'].isin(sel_sub)]

    # 2. 탭 시스템 (진행중 / 완료)
    tab_active, tab_done = st.tabs(["📊 진행중 매물 관리", "📂 거래완료 히스토리"])
    
    with tab_active:
        active_list = df[df['status'] == "진행중"]
        if active_list.empty:
            st.info("현재 진행 중인 매물이 없습니다.")
        else:
            # 엑셀처럼 깔끔한 표로 출력
            st.dataframe(
                active_list[["receipt_date", "item_sub_category", "trade_type", "price", "address", "area", "description", "id"]],
                column_config={
                    "receipt_date": "접수일", "item_sub_category": "분류", "trade_type": "구분",
                    "price": st.column_config.NumberColumn("금액(만원)", format="%d"),
                    "address": "주소", "area": "면적", "description": "특약", "id": "관리번호"
                },
                hide_index=True, use_container_width=True
            )
            
            # 거래 완료 처리 섹션 (줄줄이 나오지 않게 하나로 묶음)
            with st.expander("✅ 선택한 매물 거래 완료 처리"):
                finish_id = st.selectbox("완료 처리할 매물 주소 선택", 
                                       options=active_list['id'].tolist(),
                                       format_func=lambda x: active_list[active_list['id'] == x]['address'].values[0],
                                       key="k_finish_select")
                if st.button("해당 매물 완료 처리", use_container_width=True):
                    st.session_state.data.loc[st.session_state.data['id'] == finish_id, 'status'] = "거래완료"
                    save_data(st.session_state.data)
                    st.success("거래 완료 처리되었습니다!")
                    st.rerun()

    with tab_done:
        done_list = df[df['status'] == "거래완료"]
        st.dataframe(done_list, use_container_width=True, hide_index=True)
        if not done_list.empty:
            if st.button("🚩 완료 목록 전체 삭제", key="k_del_all"):
                st.session_state.data = st.session_state.data[st.session_state.data['status'] == "진행중"]
                save_data(st.session_state.data)
                st.rerun()
