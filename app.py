import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="파크부동산 통합 관리 시스템", page_icon="🏘️", layout="wide")
st.title("🏘️ 파크부동산 통합 관리 시스템")

# --- [데이터 정의] 대분류에 따른 소분류 매핑 ---
category_map = {
    "주거용": ["아파트", "연립/다세대", "단독/다가구", "전원주택", "오피스텔(주거)"],
    "비주거용": ["상가/사무실", "빌딩/건물", "공장/창고", "지식산업센터", "숙박시설"],
    "토지": ["대지", "전/답/과수원", "임야", "잡종지", "기타토지"]
}

# --- [더미 데이터] 실제 DB 연동 전 테스트용 ---
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame({
        "접수일": ["2026-05-07", "2026-05-07"],
        "item_category": ["주거용", "토지"],
        "소분류": ["아파트", "대지"],
        "의뢰": ["매도", "매도"],
        "구분": ["매매", "매매"],
        "가액": [35000, 120000],
        "주소": ["서울시 강남구 역삼동", "경기도 양평군..."],
        "area": ["84㎡", "500㎡"],
        "특약내용": ["입주일 협의", "현 상태 인도"]
    })

# 2. 매물 등록 섹션 (접이식 UI)
with st.expander("➕ 새 매물 등록하기 (클릭하여 입력창 열기)", expanded=False):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.date_input("접수일", datetime.today())
        # 대분류 선택 (라디오 버튼)
        main_cat = st.radio("물건 대분류", list(category_map.keys()), horizontal=True)
        st.radio("의뢰목적", ["매도", "임대", "매수", "임차"], horizontal=True)
    
    with col2:
        # [수정 사항] 대분류(main_cat) 선택에 따라 소분류 리스트가 동적으로 변함
        st.selectbox("물건 소분류", category_map[main_cat])
        st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        
        # [수정 사항] 거래가액 입력: 예시 문구 제거, 숫자 전용 입력창
        st.number_input("거래가액 (만원 단위)", min_value=0, step=100, format="%d")
        
    with col3:
        st.text_input("소재지 상세")
        st.text_input("면적")
        st.text_area("특약내용", height=68)
        
    st.write("")
    if st.button("🏠 데이터베이스 저장", use_container_width=True):
        st.success("새 매물이 성공적으로 등록되었습니다!")

st.divider()

# 3. 검색 및 필터링
st.text_input("🔍 키워드 검색 (주소, 특약 등)", placeholder="검색어를 입력하세요.")

with st.expander("✅ 상세 필터 선택", expanded=True):
    f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns(5)
    with f_col1:
        st.checkbox("주거용", key="f1")
        st.checkbox("비주거용", key="f2")
    with f_col2:
        st.checkbox("연립/다세대", key="f3")
        st.checkbox("상가/사무실", key="f4")
    with f_col3:
        st.checkbox("단독/다가구", key="f5")
        st.checkbox("공장/창고", key="f6")
    with f_col4:
        st.checkbox("전원주택", key="f7")
        st.checkbox("빌딩/건물", key="f8")
    with f_col5:
        st.checkbox("아파트", key="f9")
        st.checkbox("지식산업센터", key="f10")

# 4. 매물 목록 표시 (가독성 개선)
st.subheader(f"📊 매물 목록 (조회 결과: {len(st.session_state.df)}건)")

st.dataframe(
    st.session_state.df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "가액": st.column_config.NumberColumn(
            "가액(만원)",
            help="거래 금액입니다.",
            format="%d 만원" # [수정 사항] 숫자 끝에 '만원' 표시 및 천단위 콤마 자동 적용
        ),
        "접수일": st.column_config.DateColumn("접수일"),
        "특약내용": st.column_config.TextColumn("특약내용", width="large"),
    }
)

# 5. 엑셀 다운로드 기능
@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8-sig')

csv_data = convert_df(st.session_state.df)

st.download_button(
    label="📥 현재 조회된 매물 목록 다운로드 (CSV)",
    data=csv_data,
    file_name=f'park_estate_{datetime.today().strftime("%Y%m%d")}.csv',
    mime='text/csv',
)
