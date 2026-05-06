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

    # --- 하단: 직관적인 편집기 (에디터) ---
    df = load_data()
    if not df.empty:
        st.markdown("---")
        st.subheader("📝 매물 목록 편집기")
        st.info("💡 표 안의 내용을 클릭해서 직접 수정하거나, 행을 선택하고 [Delete] 키로 삭제할 수 있습니다.")
        
        # 통합 검색 기능 유지
        search = st.text_input("🔍 검색어 입력")
        display_df = df.copy()
        if search:
            display_df = display_df[display_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

        # 엑셀처럼 수정 가능한 데이터 에디터 호출
        edited_df = st.data_editor(
            display_df,
            use_container_width=True,
            num_rows="dynamic", # 행 삭제 및 추가 가능
            hide_index=False,
            column_config={
                "접수일자": st.column_config.Column(disabled=True) # 날짜는 자동입력이니 수정 불가 설정
            }
        )

        # 변경 사항 저장 버튼
        if st.button("💾 변경된 내용 모두 저장하기"):
            # 검색 필터가 걸린 상태에서 수정했을 경우를 대비해 원본과 병합 로직
            if search:
                df.update(edited_df)
            else:
                df = edited_df
                
            save_data(df)
            st.success("✅ 모든 변경 사항이 엑셀 파일에 저장되었습니다!")
            st.rerun()
    else:
        st.info("데이터가 없습니다. 상단에서 매물을 먼저 등록해 보세요.")
