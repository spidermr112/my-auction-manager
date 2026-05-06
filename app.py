import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="부동산 경매 매물 관리자", layout="wide")

# 2. 보안 및 세션 상태 초기화
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False
if "history" not in st.session_state:
    st.session_state["history"] = [] # 최대 10개의 과거 데이터를 담는 리스트

# 비밀번호 보안 기능
def check_password():
    def password_entered():
        if st.session_state["password"] == "1234":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.title("🔒 관리자 인증")
        st.text_input("접속 비밀번호를 입력하세요", type="password", on_change=password_entered, key="password")
        return False
    return True

# 3. 메인 프로그램 시작
if check_password():
    st.title("🏠 부동산 경매 매물 관리 시스템 v3.0")
    EXCEL_FILE = "RealEstate_Data.xlsx"

    def load_data():
        if os.path.exists(EXCEL_FILE):
            try: return pd.read_excel(EXCEL_FILE)
            except: return pd.DataFrame()
        return pd.DataFrame()

    def save_data(df):
        df.to_excel(EXCEL_FILE, index=False)

    # --- 상단: 새 매물 등록 폼 ---
    with st.expander("➕ 새 매물 등록하기", expanded=False):
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
                # 저장 전 현재 상태를 히스토리에 추가 (보험)
                st.session_state["history"].append(df.copy())
                if len(st.session_state["history"]) > 10: st.session_state["history"].pop(0)
                
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df)
                st.success("✅ 신규 매물이 등록되었습니다!")
                st.rerun()

    # --- 하단: 스마트 관리 및 10단계 되돌리기 ---
    df = load_data()
    if not df.empty:
        st.markdown("---")
        col_t, col_h = st.columns([3, 1])
        with col_t:
            st.subheader("📝 실시간 데이터 관리")
        with col_h:
            h_count = len(st.session_state["history"])
            if h_count > 0:
                if st.button(f"⏪ 되돌리기 ({h_count}/10)"):
                    prev_df = st.session_state["history"].pop()
                    save_data(prev_df)
                    st.toast("이전 단계로 복구되었습니다.")
                    st.rerun()

        st.info("💡 수정/삭제 시 즉시 저장됩니다. 실수는 '되돌리기' 버튼을 이용하세요.")
        search = st.text_input("🔍 검색어 입력 (모든 항목 검색)")
        
        display_df = df.copy()
        if search:
            display_df = display_df[display_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

        # 데이터 에디터
        edited_df = st.data_editor(
            display_df,
            use_container_width=True,
            num_rows="dynamic",
            key="data_editor",
            column_config={"접수일자": st.column_config.Column(disabled=True)}
        )

        # 자동 저장 및 히스토리 관리 로직
        if not edited_df.equals(display_df):
            # 현재 상태를 히스토리에 저장 (최대 10개)
            st.session_state["history"].append(df.copy())
            if len(st.session_state["history"]) > 10:
                st.session_state["history"].pop(0)
            
            # 실제 데이터 업데이트
            if search:
                df.update(edited_df)
            else:
                df = edited_df
            
            save_data(df)
            st.toast("실시간 저장 완료 💾")
    else:
        st.info("데이터가 없습니다.")
