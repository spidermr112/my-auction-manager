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

    # --- 상단: 새 매물 등록 폼 ---
    with st.expander("➕ 새 매물 등록하기", expanded=True):
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
                st.success("✅ 신규 매물이 등록되었습니다!")
                st.rerun()

    # --- 하단: 즉시 저장 에디터 & 되돌리기 보험 ---
    df = load_data()
    if not df.empty:
        st.markdown("---")
        col_title, col_undo = st.columns([3, 1])
        with col_title:
            st.subheader("📝 매물 목록 관리 (즉시 저장 모드)")
        
        # [보험 기능] 되돌리기 버튼
        with col_undo:
            if "last_df" in st.session_state:
                if st.button("⏪ 방금 수정한 내용 되돌리기"):
                    save_data(st.session_state["last_df"])
                    del st.session_state["last_df"]
                    st.success("데이터를 복구했습니다!")
                    st.rerun()

        st.info("💡 수정하거나 삭제(행 선택 후 Delete)하면 즉시 엑셀에 반영됩니다.")
        
        search = st.text_input("🔍 검색어 입력")
        display_df = df.copy()
        if search:
            display_df = display_df[display_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

        # 데이터 에디터 (수정 시 즉시 트리거)
        edited_df = st.data_editor(
            display_df,
            use_container_width=True,
            num_rows="dynamic",
            hide_index=False,
            key="main_editor",
            column_config={"접수일자": st.column_config.Column(disabled=True)}
        )

        # 수정이 감지되었을 때 자동 저장 로직
        # 현재 화면의 데이터와 실제 저장된 데이터가 다를 경우에만 실행
        if not edited_df.equals(display_df):
            # 되돌리기용으로 현재 상태를 저장
            st.session_state["last_df"] = df.copy()
            
            # 실제 데이터 업데이트 및 저장
            if search:
                df.update(edited_df)
            else:
                df = edited_df
            
            save_data(df)
            st.toast("저장되었습니다!", icon="💾")
            # st.rerun()을 쓰면 깜빡임이 생기므로 toast로 확인만 줌
            
    else:
        st.info("데이터가 없습니다. 상단에서 매물을 먼저 등록해 보세요.")
