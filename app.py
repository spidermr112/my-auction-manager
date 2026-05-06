import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time

# --- 페이지 설정 ---
st.set_page_config(page_title="파크부동산 프로 매물관리", layout="wide")

# --- 데이터 영구 저장 로직 ---
DB_FILE = "property_data.csv"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            if 'receipt_date' in df.columns:
                df['receipt_date'] = pd.to_datetime(df['receipt_date']).dt.date
            df['id'] = df['id'].astype(str)
            return df
        except:
            return create_empty_df()
    else:
        return create_empty_df()

def create_empty_df():
    return pd.DataFrame(columns=[
        "id", "receipt_date", "item_category", "item_sub_category", 
        "purpose", "trade_type", "price", "address", "area", "status", "description"
    ])

def save_data(df):
    df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')

# 데이터 로드
if 'data' not in st.session_state:
    st.session_state.data = load_data()

# --- 사이드바: 매물 등록 (공간 분리) ---
with st.sidebar:
    st.header("📍 신규 매물 등록")
    with st.container(border=True):
        receipt_date = st.date_input("접수일", datetime.now())
        item_category = st.selectbox("대분류", ["주거용", "비주거용", "토지"])
        
        if item_category == "주거용":
            sub_options = ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택"]
        elif item_category == "비주거용":
            sub_options = ["상가/사무실", "공장/창고", "빌딩/건물", "지식산업센터", "기타"]
        else:
            sub_options = ["대지", "임야", "농지", "기타"]
            
        item_sub_category = st.selectbox("소분류", sub_options)
        purpose = st.selectbox("의뢰목적", ["매도", "임대", "매수", "임차", "교환"])
        trade_type = st.selectbox("구분", ["매매", "전세", "월세"])
        price = st.number_input("거래가액(만원)", min_value=0, step=1000)
        address = st.text_input("소재지 상세")
        area = st.text_input("면적")
        description = st.text_area("특약내용")
        
        if st.button("🏠 매물 등록하기", use_container_width=True):
            if address:
                new_id = f"P{int(time.time())}"
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

# --- 메인 화면: 대시보드 ---
st.title("🏘️ 파크부동산 자산 관리 시스템")

# 1. 상단 요약 지표 (Metrics)
active_df = st.session_state.data[st.session_state.data['status'] == "진행중"]
done_df = st.session_state.data[st.session_state.data['status'] == "거래완료"]

m1, m2, m3, m4 = st.columns(4)
m1.metric("진행 중 매물", f"{len(active_df)}건")
m2.metric("누적 거래 완료", f"{len(done_df)}건")
m3.metric("총 매도 가액", f"{active_df[active_df['purpose']=='매도']['price'].sum():,}만원")
m4.metric("오늘 신규", f"{len(active_df[active_df['receipt_date'] == datetime.now().date()])}건")

st.divider()

# 2. 검색 및 필터 파트
col_s1, col_s2, col_s3 = st.columns([2, 1, 1])
with col_s1:
    search_q = st.text_input("🔍 주소 또는 특약 키워드 검색", placeholder="예: 한강로, 올수리, 급매")
with col_s2:
    f_cat = st.multiselect("소분류 필터", options=st.session_state.data['item_sub_category'].unique())
with col_s3:
    f_trade = st.multiselect("거래구분 필터", options=["매매", "전세", "월세"])

# 데이터 필터링 로직
df_to_show = st.session_state.data.copy()
if search_q:
    df_to_show = df_to_show[df_to_show['address'].str.contains(search_q) | df_to_show['description'].str.contains(search_q)]
if f_cat:
    df_to_show = df_to_show[df_to_show['item_sub_category'].isin(f_cat)]
if f_trade:
    df_to_show = df_to_show[df_to_show['trade_type'].isin(f_trade)]

# 3. 메인 데이터 테이블 (전문가용 뷰)
tab_main, tab_history = st.tabs(["📋 실시간 매물 대장", "📂 거래 완료 히스토리"])

with tab_main:
    current_list = df_to_show[df_to_show['status'] == "진행중"]
    if not current_list.empty:
        # 데이터프레임 스타일링
        st.dataframe(
            current_list[["receipt_date", "item_sub_category", "purpose", "trade_type", "price", "address", "area", "description", "id"]],
            column_config={
                "price": st.column_config.NumberColumn("거래가(만원)", format="%d"),
                "receipt_date": "접수일",
                "item_sub_category": "분류",
                "trade_type": "구분",
                "address": "상세 주소",
                "description": "특약사항"
            },
            hide_index=True,
            use_container_width=True
        )
        
        # 관리 작업 (거래 완료 처리 버튼들을 하단에 작게 배치)
        with st.expander("⚙️ 매물 상태 관리 (거래 완료 처리)"):
            cols = st.columns(3)
            for idx, row in current_list.iterrows():
                with cols[idx % 3]:
                    if st.button(f"✅ 완료: {row['address'][:10]}...", key=f"d_{row['id']}"):
                        st.session_state.data.loc[st.session_state.data['id'] == row['id'], 'status'] = "거래완료"
                        save_data(st.session_state.data)
                        st.rerun()
    else:
        st.info("현재 진행 중인 매물이 없습니다.")

with tab_history:
    done_list = df_to_show[df_to_show['status'] == "거래완료"]
    st.dataframe(done_list, use_container_width=True, hide_index=True)
    if st.button("🧹 완료 목록 전체 비우기"):
        st.session_state.data = st.session_state.data[st.session_state.data['status'] == "진행중"]
        save_data(st.session_state.data)
        st.rerun()
