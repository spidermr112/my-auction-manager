import streamlit as st
import pandas as pd
from datetime import datetime
import os
import re
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
            # 고유 ID 부여 (에러 방지용)
            if 'id' not in df.columns:
                df['id'] = [f"P_{int(time.time())}_{i}" for i in range(len(df))]
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
col_reg, col_list = st.columns([1, 2.2])

# --- [좌측] 매물 등록 파트 ---
with col_reg:
    st.subheader("📍 매물 등록")
    
    with st.container(border=True):
        reg_date = st.date_input("접수일", datetime.now(), key="k_date")
        reg_cat = st.radio("물건 대분류", ["주거용", "비주거용", "토지"], horizontal=True, key="k_cat")
        
        if reg_cat == "주거용":
            subs = ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택"]
        elif reg_cat == "비주거용":
            subs = ["상가/사무실", "공장/창고", "빌딩/건물", "지식산업센터", "기타"]
        else:
            subs = ["대지", "임야", "농지", "기타"]
        
        reg_sub = st.radio("물건 소분류", subs, horizontal=True, key="k_sub")
        reg_purp = st.radio("의뢰목적", ["매도", "임대", "매수", "임차", "교환"], horizontal=True, key="k_purp")
        reg_trade = st.radio("구분", ["매매", "전세", "월세"], horizontal=True, key="k_trade")
        
        if reg_cat == "주거용":
            r_col, b_col = st.columns(2)
            with r_col:
                reg_room = st.radio("방 개수", ["방1", "방2", "방3", "방4 이상"], horizontal=True, key="k_room")
            with b_col:
                reg_bath = st.radio("화장실 개수", ["화장실1", "화장실2", "화장실3 이상"], horizontal=True, key="k_bath")
        else:
            reg_room, reg_bath = "N/A", "N/A"
        
        reg_price = st.number_input("거래가액(만원)", min_value=0, step=100, key="k_price")
        reg_addr = st.text_input("소재지 상세", key="k_addr")
        
        # [핵심] 면적 입력창 (평 단위 자동변환)
        reg_area_raw = st.text_input("면적 (예: 30평)", key="k_area_raw", help="'평'을 넣어 입력하면 제곱미터로 자동 계산됩니다.")
        reg_desc = st.text_area("특약내용", key="k_desc")
        
        if st.button("🏠 데이터베이스 저장", use_container_width=True, key="k_save_btn"):
            # --- 평 수 변환 로직 복구 ---
            final_area = reg_area_raw
            if reg_area_raw and '평' in reg_area_raw:
                try:
                    num_only = re.sub(r'[^0-9.]', '', reg_area_raw)
                    if num_only:
                        pyung = float(num_only)
                        m2 = round(pyung * 3.3058, 2)
                        final_area = f"{m2}㎡({pyung}평)"
                except:
                    pass
            
            # 새 데이터 생성 (주소/면적 빈칸 허용)
            new_id = f"P_{int(time.time() * 1000)}"
            new_row = pd.DataFrame([{
                "id": new_id, "receipt_date": reg_date, "item_category": reg_cat,
                "item_sub_category": reg_sub, "purpose": reg_purp,
                "trade_type": reg_trade, "room_count": reg_room,
                "bathroom_count": reg_bath, "price": reg_price,
                "address": reg_addr if reg_addr else "(미입력)", 
                "area": final_area if final_area else "(미입력)", 
                "description": reg_desc, "status": "진행중"
            }])
            
            st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
            save_data(st.session_state.data)
            st.success(f"[{final_area}] 저장 완료!")
            st.rerun()

# --- [우측] 매물 목록 및 색인 ---
with col_list:
    st.title("🏘️ 파크부동산")
    s_query = st.text_input("🔍 키워드 검색", key="k_s_query")

    st.write("---")
    st.markdown("### ✅ 필터 선택")

    def create_filter(label, options):
        st.markdown(f"**{label}**")
        cols = st.columns(5) # 한 줄에 5개씩 배치
        sel = []
        for i, opt in enumerate(options):
            if cols[i % 5].checkbox(opt, key=f"f_{label}_{opt}"):
                sel.append(opt)
        return sel

    all_subs = ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택", "상가/사무실", "공장/창고", "빌딩/건물", "지식산업센터", "대지", "임야", "농지"]
    f_sub = create_filter("물건 소분류", all_subs)
    f_purp = create_filter("의뢰목적", ["매도", "임대", "매수", "임차", "교환"])
    
    # 필터링 적용
    df_f = st.session_state.data.copy()
    if s_query:
        df_f = df_f[df_f.apply(lambda r: s_query in str(r.values), axis=1)]
    if f_sub:
        df_f = df_f[df_f['item_sub_category'].isin(f_sub)]
    if f_purp:
        df_f = df_f[df_f['purpose'].isin(f_purp)]

    st.write(f"**조회 결과:** {len(df_f)} 건")
    st.dataframe(df_f, use_container_width=True, hide_index=True)

    if not df_f.empty:
        if st.button("🗑️ 전체 데이터 초기화", key="k_clear"):
            st.session_state.data = create_empty_df()
            save_data(st.session_state.data)
            st.rerun()
