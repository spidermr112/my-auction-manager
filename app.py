import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="파크부동산 통합 관리 시스템", page_icon="🏘️", layout="wide")

st.title("🏘️ 파크부동산 통합 관리 시스템")

# --- [더미 데이터 생성] 실제 DB 연동 코드로 대체하세요 ---
@st.cache_data
def load_dummy_data():
    data = {
        "접수일": ["2026-05-06", "2026-05-06", "2026-05-06", "2026-05-06", "2026-05-06"],
        "item_category": ["주거용", "주거용", "주거용", "주거용", "주거용"],
        "소분류": ["아파트", "아파트", "아파트", "아파트", "아파트"],
        "의뢰": ["매도", "매도", "매도", "매도", "매도"],
        "구분": ["매매", "매매", "매매", "매매", "매매"],
        "room_count": ["방1", "방1", "방1", "방1", "방1"],
        "bathroom_count": ["화장실1", "화장실1", "화장실1", "화장실1", "화장실1"],
        "가액": [35000, 40000, 25000, 0, 50000], # 정수형으로 저장 (단위: 만원)
        "주소": ["ㅇㅇ", "None", "None", "None", "(미입력)"],
        "area": ["99.17㎡(30.0평)", "30평", "30평", "30평", "99.17㎡(30.0평)"],
        "특약내용": ["None", "None", "ㄴㄴ", "None", "None"]
    }
    return pd.DataFrame(data)

df = load_dummy_data()
# --------------------------------------------------------

# 2. 새 매물 등록 섹션 (Collapsible UI 적용)
with st.expander("➕ 새 매물 등록하기 (클릭하여 입력창 열기)", expanded=False):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.date_input("접수일", datetime.today())
        st.radio("물건 대분류", ["주거용", "비주거용", "토지"], horizontal=True)
        st.radio("의뢰목적", ["매도", "임대", "매수", "임차"], horizontal=True)
    
    with col2:
        st.selectbox("물건 소분류", ["연립/다세대", "아파트", "단독/다가구", "상가/사무실"])
        st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        st.text_input("거래가액", placeholder="예: 3억 5천 / 4000/35")
        
    with col3:
        st.text_input("소재지 상세")
        st.text_input("면적")
        st.text_input("특약내용")
        
    st.write("") # 여백용
    if st.button("🏠 데이터베이스 저장", use_container_width=True):
        st.success("새 매물이 성공적으로 저장되었습니다! (임시 메시지)")

st.divider()

# 3. 검색 및 필터 섹션
st.text_input("🔍 키워드 검색 (주소, 특약 등)", placeholder="검색어를 입력하세요.")

with st.expander("✅ 상세 필터 선택", expanded=True):
    f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns(5)
    with f_col1:
        st.checkbox("주거용")
        st.checkbox("비주거용")
    with f_col2:
        st.checkbox("연립/다세대")
        st.checkbox("상가/사무실")
    with f_col3:
        st.checkbox("단독/다가구")
        st.checkbox("공장/창고")
    with f_col4:
        st.checkbox("전원주택")
        st.checkbox("빌딩/건물")
    with f_col5:
        st.checkbox("아파트")
        st.checkbox("지식산업센터")

# 4. 매물 목록 및 데이터프레임 서식화
st.subheader(f"📊 매물 목록 (조회 결과: {len(df)}건)")

# 데이터프레임 가독성 개선 (column_config 적용)
st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "접수일": st.column_config.DateColumn("접수일", format="YYYY-MM-DD"),
        "가액": st.column_config.NumberColumn(
            "가액(만원)", 
            help="거래가액 단위: 만원",
            format="%d 만원" # 금액을 보기 쉽게 포맷팅 (#,### 만원 형태)
        ),
        "특약내용": st.column_config.TextColumn("특약내용", width="large"),
        "주소": st.column_config.TextColumn("주소", width="medium")
    }
)

# 5. 엑셀(CSV) 다운로드 버튼
@st.cache_data
def convert_df(data):
    # 한글 깨짐 방지를 위해 utf-8-sig 사용
    return data.to_csv(index=False).encode('utf-8-sig')

csv = convert_df(df)

st.download_button(
    label="📥 현재 조회된 매물 목록 다운로드 (CSV)",
    data=csv,
    file_name=f'park_real_estate_{datetime.today().strftime("%Y%m%d")}.csv',
    mime='text/csv',
)
