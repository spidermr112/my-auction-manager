import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="부동산 경매 매물 관리자", layout="wide")
st.title("🏠 부동산 경매 매물 등록 시스템")

# 파일 경로 설정
EXCEL_FILE = "RealEstate_Data.xlsx"

# 2. 입력 폼 섹션 (기존 디자인 유지)
with st.form("my_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        case_no = st.text_input("사건번호", value="2025타경")
        p_type = st.selectbox("물건종류", ["빌라", "아파트", "단독", "오피스텔", "상가", "토지"])
        address = st.text_input("소재지", value="남양주시 ")
        trade_type = st.radio("구분", ["매매", "전세", "월세"], horizontal=True)

    with col2:
        price = st.text_input("거래가액 (만원)")
        rooms = st.selectbox("방 개수", ["방1", "방2", "방3", "방4", "방5"])
        area = st.text_input("공급/전용 면적")
        memo = st.text_area("특약사항 및 분석내용")

    submitted = st.form_submit_button("엑셀에 저장하기")

    if submitted:
        # 데이터 생성
        new_data = {
            "접수일자": datetime.now().strftime("%Y-%m-%d"),
            "사건번호": case_no,
            "물건종류": p_type,
            "주소": address,
            "구분": trade_type,
            "거래가액": price,
            "방개수": rooms,
            "면적": area,
            "비고": memo
        }
        
        # 엑셀 저장 로직
        df_new = pd.DataFrame([new_data])
        
        if not os.path.exists(EXCEL_FILE):
            df_new.to_excel(EXCEL_FILE, index=False)
        else:
            with pd.ExcelWriter(EXCEL_FILE, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                try:
                    existing_df = pd.read_excel(EXCEL_FILE)
                    updated_df = pd.concat([existing_df, df_new], ignore_index=True)
                    updated_df.to_excel(writer, index=False)
                except:
                    df_new.to_excel(writer, index=False)
        
        st.success(f"✅ {case_no} 물건 정보가 성공적으로 저장되었습니다!")
        st.rerun() # 저장 후 화면 갱신

# 3. 분석 및 검색 섹션 (데이터가 있을 때만 표시)
if os.path.exists(EXCEL_FILE):
    df = pd.read_excel(EXCEL_FILE)
    
    st.markdown("---")
    st.subheader("🔍 스마트 매물 분석기")
    
    # [기능 1] 통합 검색 (어떤 항목이든 검색 가능)
    search_query = st.text_input("검색어 입력 (주소, 사건번호, 비고 등 아무거나 입력하세요)")
    if search_query:
        mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
        df = df[mask]

    # [기능 2] 유연한 피벗 분석 (항목이 바뀌어도 자동 대응)
    col_sort, col_view = st.columns([1, 2])
    
    with col_sort:
        target_column = st.selectbox("📊 분석 기준 선택 (피벗)", df.columns)
        
    with col_view:
        summary = df[target_column].value_counts().reset_index()
        summary.columns = [target_column, '매물 수']
        st.dataframe(summary, use_container_width=True)

    # 4. 최종 리스트 표시
    st.subheader("📊 매물 목록")
    st.dataframe(df, use_container_width=True)
else:
    st.info("아직 등록된 매물이 없습니다. 위 양식을 통해 첫 매물을 등록해 보세요!")
