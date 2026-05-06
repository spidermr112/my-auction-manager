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
            # ID가 중복되었을 가능성이 크므로, 로드 시점에 ID를 문자열로 고정
            if 'id' in df.columns:
                df['id'] = df['id'].astype(str)
            
            # 필수 컬럼 보정 (상태값이 없으면 진행중으로 처리)
            if 'status' not in df.columns:
                df['status'] = "진행중"
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
    
    # 위젯마다 중복되지 않는 고유 key 할당
    reg_date = st.date_input("접수일", datetime.now(), key="k_reg_date")
    reg_cat = st.radio("물건 대분류", ["주거용", "비주거용", "토지"], horizontal=True, key="k_reg_cat")
    
    if reg_cat == "주거용":
        subs = ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택"]
    elif reg_cat == "비주거용":
        subs = ["상가/사무실", "공장/창고", "빌딩/건물", "지식산업센터", "기타"]
    else:
        subs = ["대지", "임야", "농지", "기타"]
    
    reg_sub = st.radio("물건 소분류", subs, horizontal=True, key="k_reg_sub")
    reg_purp = st.radio("의뢰목적", ["매도", "임대", "매수", "임차", "교환"], horizontal=True, key="k_reg_purp")
    reg_trade = st.radio("구분", ["매매", "전세", "월세"], horizontal=True, key="k_reg_trade")
    
    reg_price = st.number_input("거래가액(만원)", min_value=0, step=100, key="k_reg_price")
    reg_addr = st.text_input("소재지 상세", key="k_reg_addr")
    reg_area = st.text_input("면적", key="k_reg_area")
    reg_desc = st.text_area("특약내용", key="k_reg_desc")
    
    if st.button("🏠 데이터베이스 저장", use_container_width=True, key="k_reg_btn"):
        if reg_addr:
            # 절대 겹칠 수 없는 ID 생성 (타임스탬프 + 현재 데이터 길이)
            unique_id = f"{int(time.time() * 1000)}_{len(st.session_state.data)}"
            new_row = pd.DataFrame([{
                "id": unique_id, "receipt_date": reg_date, "item_category": reg_cat,
                "item_sub_category": reg_sub, "purpose": reg_purp,
                "trade_type": reg_trade, "price": reg_price, "address": reg_addr, 
                "area": reg_area, "description": reg_desc, "status": "진행중"
            }])
            st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
            save_data(st.session_state.data)
            st.success("매물 등록 완료!")
            st.rerun()
        else:
            st.error("주소를 입력해주세요.")

# --- [우측] 매물 목록 및 필터 파트 ---
with col_list:
    st.title("🏘️ 파크부동산 매물 대장")
    
    # 1. 검색 및 필터링 (가장 안전한 멀티셀렉트 방식)
    search_q = st.text_input("🔍 키워드 검색 (주소/특약)", placeholder="검색어를 입력하세요.", key="k_search")
    
    st.markdown("### ✅ 필터링")
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        all_list = ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택", "상가/사무실", "공장/창고", "빌딩/건물", "지식산업센터", "대지", "임야", "농지"]
        sel_sub = st.multiselect("소분류 필터", all_list, key="k_filter_sub")
    with f_col2:
        sel_trade = st.multiselect("거래 구분 필터", ["매매", "전세", "월세"], key="k_filter_trade")

    # 데이터 필터링 로직
    df = st.session_state.data.copy()
    if search_q:
        df = df[df.apply(lambda r: search_q in str(r.values), axis=1)]
    if sel_sub:
        df = df[df['item_sub_category'].isin(sel_sub)]
    if sel_trade:
        df = df[df['trade_type'].isin(sel_trade)]

    # 2. 탭 시스템
    tab_a, tab_b = st.tabs(["✅ 진행중 매물", "🏁 거래완료 목록"])
    
    with tab_a:
        active_list = df[df['status'] == "진행중"]
        if active_list.empty:
            st.info("현재 진행 중인 매물이 없습니다.")
        else:
            # 에러 방지를 위해 enumerate 사용 (혹시 ID가 겹쳐도 버튼 key 충돌 안 나게 이중 보안)
            for i, row in active_list.iterrows():
                with st.expander(f"📍 {row['address']} ({row['item_sub_category']} / {row['price']}만원)"):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.write(f"**구분:** {row['trade_type']} | **면적:** {row['area']} | **접수:** {row['receipt_date']}")
                        st.write(f"**특약:** {row['description']}")
                    with c2:
                        # 버튼 키에 ID뿐만 아니라 행 인덱스(i)를 붙여 중복을 원천 차단
                        if st.button("완료처리", key=f"done_btn_{row['id']}_{i}"):
                            st.session_state.data.loc[st.session_state.data['id'] == row['id'], 'status'] = "거래완료"
                            save_data(st.session_state.data)
                            st.rerun()
            st.write("---")
            st.dataframe(active_list, use_container_width=True, hide_index=True)

    with tab_b:
        done_list = df[df['status'] == "거래완료"]
        st.dataframe(done_list, use_container_width=True, hide_index=True)
        if not done_list.empty:
            if st.button("🏁 완료 목록 비우기", key="k_clear_done"):
                st.session_state.data = st.session_state.data[st.session_state.data['status'] == "진행중"]
                save_data(st.session_state.data)
                st.rerun()
