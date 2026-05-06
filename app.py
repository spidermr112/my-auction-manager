import streamlit as st
import pandas as pd
from datetime import datetime

# --- 페이지 설정 ---
st.set_page_config(page_title="파크부동산 매물관리", layout="wide")

# --- 데이터 로드 및 초기화 (세션 상태 활용) ---
if 'data' not in st.session_state:
    # 'status' 컬럼을 추가하여 진행중/거래완료 상태 관리
    st.session_state.data = pd.DataFrame(columns=[
        "id", "receipt_date", "item_category", "item_sub_category", 
        "purpose", "trade_type", "price", "address", "area", "description", "status"
    ])

# --- 레이아웃 구성 ---
col_reg, col_list = st.columns([1, 2.5])

# --- [좌측] 매물 등록 파트 (실시간 소분류 변경 포함) ---
with col_reg:
    st.subheader("📍 신규 매물 등록")
    
    # 폼(form)을 사용하지 않아야 대분류 클릭 시 소분류가 즉시 바뀝니다.
    receipt_date = st.date_input("접수일", datetime.now())
    
    # 1. 대분류 선택
    item_category = st.radio("물건 대분류", ["주거용", "비주거용", "토지"], horizontal=True)
    
    # 2. 대분류에 따른 소분류 옵션 동적 할당
    if item_category == "주거용":
        sub_options = ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택"]
    elif item_category == "비주거용":
        sub_options = ["상가/사무실", "공장/창고", "빌딩/건물", "지식산업센터", "기타"]
    else:  # 토지
        sub_options = ["대지", "임야", "농지", "기타"]
    
    # 3. 소분류 라디오 버튼 (위에 설정한 sub_options가 즉시 적용됨)
    item_sub_category = st.radio("물건 소분류", sub_options, horizontal=True)
    
    purpose = st.radio("의뢰목적", ["매도", "임대", "매수", "임차", "교환"], horizontal=True)
    trade_type = st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
    
    price = st.number_input("거래가액(만원)", min_value=0, step=100)
    address = st.text_input("소재지 상세")
    area = st.text_input("면적")
    description = st.text_area("특약 및 분석내용")
    
    # 저장 버튼
    if st.button("🏠 데이터베이스 저장"):
        if address:
            new_id = len(st.session_state.data) + 1
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
                "status": "진행중"  # 등록 시 기본 상태
            }])
            st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
            st.success(f"[{item_sub_category}] 등록 완료!")
            st.rerun()
        else:
            st.error("소재지 상세 주소를 입력해주세요.")

# --- [우측] 매물 목록 및 색인 파트 (거래완료 관리 포함) ---
with col_list:
    st.title("🏘️ 파크부동산 매물 대장")
    
    # 상단 검색 필터
    search_query = st.text_input("🔍 키워드 검색 (주소 등)", placeholder="검색어를 입력하세요.")

    st.write("---")
    
    if not st.session_state.data.empty:
        # 데이터 복사 및 필터링
        display_df = st.session_state.data.copy()
        if search_query:
            display_df = display_df[display_df['address'].str.contains(search_query) | 
                                    display_df['description'].str.contains(search_query)]

        # 탭 구분: 진행중 매물 vs 거래완료 목록
        tab1, tab2 = st.tabs(["✅ 진행중 매물", "🏁 거래완료 목록"])
        
        with tab1:
            active_items = display_df[display_df['status'] == "진행중"]
            if active_items.empty:
                st.info("현재 진행 중인 매물이 없습니다.")
            else:
                # 각 매물을 개별 카드로 표시 (거래완료 버튼 포함)
                for i, row in active_items.iterrows():
                    with st.expander(f"📍 {row['address']} [{row['item_sub_category']} / {row['trade_type']}] - {row['price']}만원"):
                        c1, c2 = st.columns([4, 1])
                        with c1:
                            st.write(f"**접수일:** {row['receipt_date']} | **면적:** {row['area']}")
                            st.write(f"**특약:** {row['description']}")
                        with c2:
                            # 거래 완료 버튼 클릭 시 상태 업데이트
                            if st.button("거래완료", key=f"btn_{row['id']}"):
                                st.session_state.data.loc[st.session_state.data['id'] == row['id'], 'status'] = "거래완료"
                                st.success("거래 완료 처리되었습니다.")
                                st.rerun()
                
                st.write("")
                st.markdown("##### 📋 전체 데이터 시트")
                st.dataframe(active_items, use_container_width=True)

        with tab2:
            completed_items = display_df[display_df['status'] == "거래완료"]
            if completed_items.empty:
                st.write("거래 완료된 매물이 없습니다.")
            else:
                st.dataframe(completed_items, use_container_width=True)
                if st.button("완료 내역 초기화(삭제)"):
                    st.session_state.data = st.session_state.data[st.session_state.data['status'] == "진행중"]
                    st.rerun()
    else:
        st.info("등록된 매물이 없습니다. 좌측에서 매물을 먼저 등록해 주세요.")
