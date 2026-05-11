import streamlit as st
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="페이지부동산 매물 관리", layout="wide")

# 제목 섹션
st.title("📄 페이지부동산 매물 관리 시스템")

# 상단 버튼 (검색 초기화 등)
col_header1, col_header2 = st.columns([8, 2])
with col_header2:
    if st.button("🔄 검색 초기화"):
        st.rerun()

# 1. 새 매물 등록 섹션
with st.expander("➕ 새 매물 등록"):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.date_input("접수일", datetime.now())
        st.text_input("고객명")
    with col2:
        st.text_input("연락처")
        st.radio("물건 대분류", ["주거용", "비주거용", "토지"], horizontal=True)
    with col3:
        st.text_input("물건 소분류", value="아파트")
        st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
    
    st.text_input("소재지 상세")
    
    col4, col5, col6 = st.columns(3)
    with col4:
        st.number_input("가액 (만원)", value=0)
    with col5:
        st.number_input("월세 (만원)", value=0)
    with col6:
        st.text_input("면적 입력")
        
    st.text_area("특약내용", value="[아파트 매매 상세정보] - 비밀번호: - 로열층/방향: - 관리비: - 입주일:")
    
    if st.button("🏠 구글 시트에 저장"):
        st.success("저장되었습니다! (기능 연결 필요)")

# --- 1번 요청: 새 매물등록 하단 가로줄 제거 완료 ---

# 2. 매물 목록 섹션 (3번 요청에 의해 위로 이동)
st.subheader("📋 매물 목록 (8건)")
# 샘플 데이터 (기존 데이터 로드 로직이 있다면 해당 로직 사용)
data = {
    "상태": ["진행중", "진행중"],
    "소재지": ["수산리 93-3", "수산리 93번지"],
    "소분류": ["지식산업센터", "대지"],
    "가액": [80000, 90000],
    "월세": [1000, 0],
    "면적": ["400평", "450평"],
    "고객명": ["임경아", "이성준"],
    "연락처": ["010-1234-5678", "010-9876-5432"]
}
df = pd.DataFrame(data)
st.data_editor(df, use_container_width=True)

if st.button("💾 변경사항 저장"):
    st.info("변경사항이 반영되었습니다.")

# --- 2번 요청: 매물목록 하단 가로줄 제거 완료 ---

# 3. 통합 검색 필터 섹션 (3번 요청에 의해 목록 하단으로 이동)
st.subheader("🔍 통합 검색 필터")
f_col1, f_col2, f_col3, f_col4 = st.columns(4)
with f_col1:
    st.text_input("📍 검색어", placeholder="주소, 고객명...")
with f_col2:
    st.multiselect("🏗️ 종류", ["주거용", "비주거용", "토지"], default=["주거용", "비주거용", "토지"])
with f_col3:
    st.multiselect("💰 거래", ["매매", "전세", "월세"], default=["매매", "전세", "월세"])
with f_col4:
    st.multiselect("🚦 상태", ["진행중", "보류"], default=["진행중", "보류"])

# 4. 매물 상세 브리핑 섹션
st.subheader("📋 매물 상세 브리핑")
brief_col1, brief_col2 = st.columns([1, 1])

with brief_col1:
    st.markdown("### 📍 수산리 93-3")
    st.write("🏠 **종류:** 지식산업센터 (진행중)")
    st.write("💰 **가액:** 80000 / 1000")
    st.write("📏 **면적:** 400평")
    st.write("👤 **고객:** 임경아")
    st.write("📞 **연락처:** 010-1234-5678")

with brief_col2:
    st.write("📜 **상세 메모**")
    st.text_area("메모 수정", value="[아파트 매매 상세정보] - 비밀번호: - 로열층/방향: - 관리비: - 입주일:", label_visibility="collapsed")
    
    page_col1, page_col2, page_col3 = st.columns([1, 1, 1])
    with page_col1:
        st.button("◀ 이전")
    with page_col2:
        st.write("1 / 8")
    with page_col3:
        st.button("다음 ▶")
    
    st.button("💾 메모 내용 저장하기")
