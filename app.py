import streamlit as st

st.title("🏠 나의 부동산 경매 관리자")
case_number = st.text_input("사건번호 입력", "2025타경959")
address = st.text_input("소재지", "남양주시 화도읍 가곡리")
memo = st.text_area("특이사항 및 권리분석")

if st.button("저장하기"):
    st.success(f"{case_number} 물건 정보가 저장되었습니다!")