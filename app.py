import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="부동산 경매 매물 관리자", layout="wide")

# 2. 비밀번호 보안 기능
def check_password():
    def password_entered():
        if st.session_state["password"] == "1234":
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

    def load_data():
        if os.path.exists(EXCEL_FILE):
            try:
                return pd.read_excel(EXCEL_FILE)
            except:
                return pd.DataFrame()
        return pd.DataFrame()

    def save_data(df):
        df.to_excel(EXCEL_FILE, index=False)

    # 탭 구성
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

    with tab2:
        df = load_data()
        if not df.empty:
            st.subheader("📋 데이터 관리 (수정/삭제)")
            col_edit, col_del = st.columns(2)
            
            with col_del:
                st.write("🗑️ **데이터 삭제**")
                del_idx = st.number_input("삭제할 행 번호(Index) 입력", min_value=0, max_value=len(df)-1, step=1)
                if st.button("선택한 행 삭제"):
                    df = df.drop(df.index[del_idx]).reset_index(drop=True)
                    save_data(df)
                    st.warning(f"⚠️ {del_idx}번 행이 삭제되었습니다.")
                    st.rerun()

            with col_edit:
                st.write("✏️ **데이터 수정**")
                edit_idx = st.number_input("수정할 행 번호(Index) 입력", min_value=0, max_value=len(df)-1, step=1)
                if st.button("해당 데이터 불러오기"):
                    st.session_state['edit_data'] = df.iloc[edit_idx].to_dict()
                    st.session_state['edit_idx'] = edit_idx

            if 'edit_data' in st.session_state:
                st.markdown("---")
                with st.form("edit_form"):
                    e_data = st.session_state['edit_data']
                    st.write(f"🔄 **{st.session_state['edit_idx']}번 매물 수정 중**")
                    col1, col2 = st.columns(2)
                    with col1:
                        u_case = st.text_input("사건번호", value=e_data.get('사건번호', ''))
                        u_addr = st.text_input("소재지", value=e_data.get('주소', ''))
                    with col2:
                        u_price = st.text_input("거래가액", value=e_data.get('거래가액', ''))
                        u_memo = st.text_area("비고", value=e_data.get('비고', ''))
                    
                    if st.form_submit_button("수정 내용 적용"):
                        df.at[st.session_state['edit_idx'], '사건번호'] = u_case
                        df.at[st.session_state['edit_idx'], '주소'] = u_addr
                        df.at[st.session_state['edit_idx'], '거래가액'] = u_price
                        df.at[st.session_state['edit_idx'], '비고'] = u_memo
                        save_data(df)
                        del st.session_state['edit_data']
                        st.success("✅ 수정 완료!")
                        st.rerun()

    # 목록 표시
    df = load_data()
    if not df.empty:
        st.markdown("---")
        st.subheader("📊 전체 매물 목록")
        search = st.text_input("🔍 검색 (사건번호, 주소 등)")
        if search:
            df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
        st.dataframe(df, use_container_width=True)
