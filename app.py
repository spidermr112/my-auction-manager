import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="부동산 경매 매물 관리자", layout="wide")

# 2. 비밀번호 보안 기능
def check_password():
    def password_entered():
        if st.session_state["password"] == "1234": # 비밀번호 변경 가능
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔒 관리자 인증")
        st.text_input("접속 비밀번호를 입력하세요", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔒 관리자 인증")
        st.text_input("비밀번호가 틀렸습니다. 다시 입력하세요", type="password", on_change=password_entered, key="password")
        st.error("😕 비밀번호가 일치하지 않습니다.")
        return False
    else:
        return True

# 3. 메인 프로그램 시작
if check_password():
    st.title("🏠 부동산 경매 매물 등록 시스템")
    EXCEL_FILE = "RealEstate_Data.xlsx"

    # --- 데이터 불러오기 함수 ---
    def load_data():
        if os.path.exists(EXCEL_FILE):
            return pd.read_excel(EXCEL_FILE)
        return pd.DataFrame()

    # --- 데이터 저장 함수 ---
    def save_data(df):
        df.to_excel(EXCEL_FILE, index=False)

    # 탭 구성 (등록 / 수정 및 삭제)
    tab1, tab2 = st.tabs(["🆕 새 매물 등록", "🛠 매물 수정 및 삭제"])

    with tab1:
        with st.form("input_form", clear_on_submit=True):
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
            
            if st.form_submit_button("엑셀에 저장하기"):
                new_row = {
                    "접수일자": datetime.now().strftime("%Y-%m-%d"),
                    "사건번호": case_no, "물건종류": p_type, "주소": address,
                    "구분": trade_type, "거래가액": price, "방개수": rooms, "면적": area, "비고": memo
                }
                df = load_data()
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df)
                st.success("✅ 저장 완료!")
                st.rerun()

    with tab2
