import streamlit as st
import pandas as pd
from datetime import datetime

# --- 페이지 설정 ---
st.set_page_config(page_title="파크부동산 매물관리", layout="wide")

# --- 데이터 로드 (세션 상태 활용) ---
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=[
        "id", "receipt_date", "item_category", "item_sub_category", 
        "purpose", "trade_type", "price", "address", "area", "status"
    ])

# --- [좌측] 매물 등록 파트 ---
col_reg, col_list = st.columns([1, 2.5])

with col_reg:
    st.subheader("📍 신규 매물 등록")
    
    # 실시간 반영을 위해 form을 사용하지 않음
    receipt_date = st.date_input("접수일", datetime.now())
    item_category = st.radio("물건 대분류", ["주거용", "비주거용", "토지"], horizontal=True)
    
    # 대분류에 따른 소분류 동적 변경 로직
    if item_category == "주거용":
        sub_options = ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택"]
    elif item_category == "비주거용":
        sub_options = ["상가/사무실", "공장/창고", "빌딩/건물", "지식산업센터", "기타"]
    else:
        sub_options = ["대지", "임야", "농지", "기타"]
        
    item_sub_category = st.radio("물건 소분류", sub_options, horizontal=True)
    purpose = st.radio("의뢰목적", ["매도", "임대", "매수", "임차", "교환"], horizontal=True)
    trade_type = st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
    
    price = st.number_input("거래가액(만원)", min_value=0, step=1000)
    address = st.text_input("소재지 상세")
    area = st.text_input("면적")
    
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
                "status": "진행중"  # 기본값은 진행중
            }])
            st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
            st.success("새 매물이 등록되었습니다!")
            st.rerun()
        else:
            st.error("주소를 입력해주세요.")

# --- [우측] 매물 목록 및 거래 관리 ---
with col_list:
    st.title("🏘️ 파크부동산 매물 대장")
    
    # 검색 및 필터 파트
    search_query = st.text_input("🔍 키워드 검색 (주소 등)", placeholder="검색어를 입력하세요.")
    
    st.write("---")
    
    # 데이터가 있을 때만 표시
    if not st.session_state.data.empty:
        # 필터링 로직
        display_df = st.session_state.data.copy()
        if search_query:
            display_df = display_df[display_df['address'].str.contains(search_query)]
        
        # 거래 완료 여부에 따른 탭 구분 (깔끔한 정리를 위해)
        tab1, tab2 = st.tabs(["✅ 진행중 매물", "🏁 거래완료 목록"])
        
        with tab1:
            active_items = display_df[display_df['status'] == "진행중"]
            if active_items.empty:
                st.info("현재 진행 중인 매물이 없습니다.")
            else:
                # 리스트 형태로 출력하며 '거래 완료' 버튼 추가
                for i, row in active_items.iterrows():
                    with st.expander(f"📍 {row['address']} ({row['item_sub_category']} / {row['price']}만원)"):
                        c1, c2, c3 = st.columns([3, 1, 1])
                        c1.write(f"**접수일:** {row['receipt_date']} | **종류:** {row['trade_type']} | **면적:** {row['area']}")
                        
                        # 거래 완료 처리 버튼
                        if c3.button("거래완료 처리", key=f"done_{row['id']}"):
                            st.session_state.data.loc[st.session_state.data['id'] == row['id'], 'status'] = "거래완료"
                            st.rerun()
                
                st.markdown("#### 📊 전체 진행중 리스트")
                st.dataframe(active_items, use_container_width=True)

        with tab2:
            completed_items = display_df[display_df['status'] == "거래완료"]
            if completed_items.empty:
                st.write("아직 거래 완료된 내역이 없습니다.")
            else:
                # 거래완료 데이터는 회색조로 표시되는 데이터프레임으로 제공
                st.dataframe(completed_items, use_container_width=True)
                if st.button("완료 목록 비우기"):
                    st.session_state.data = st.session_state.data[st.session_state.data['status'] == "진행중"]
                    st.rerun()
    else:
        st.info("등록된 매물이 없습니다. 왼쪽에서 첫 매물을 등록해보세요!")
