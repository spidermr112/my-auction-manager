import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="부동산 경매 매물 관리자", layout="wide")
st.title("🏠 부동산 경매 매물 등록 시스템")

# 파일 경로 설정 (저장될 엑셀 파일명)
EXCEL_FILE = "RealEstate_Data.xlsx"

# 입력 폼 생성
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
        df = pd.DataFrame([new_data])
        
        if not os.path.exists(EXCEL_FILE):
            df.to_excel(EXCEL_FILE, index=False)
        else:
            with pd.ExcelWriter(EXCEL_FILE, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                try:
                    existing_df = pd.read_excel(EXCEL_FILE)
                    updated_df = pd.concat([existing_df, df], ignore_index=True)
                    updated_df.to_excel(writer, index=False)
                except:
                    df.to_excel(writer, index=False)
        
        st.success(f"✅ {case_no} 물건 정보가 성공적으로 저장되었습니다!")

# 저장된 데이터 미리보기 (선택 사항)
if os.path.exists(EXCEL_FILE):
    st.subheader("📊 현재 등록된 매물 목록")
    st.dataframe(pd.read_excel(EXCEL_FILE), use_container_width=True)
