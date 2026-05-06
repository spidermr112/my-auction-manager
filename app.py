import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# 1. 페이지 설정 및 마우스 커서 CSS 적용
st.set_page_config(page_title="부동산 경매 매물 관리자", layout="wide")

st.markdown("""
    <style>
    /* 모든 입력창, 셀렉트박스, 텍스트 영역의 커서를 화살표(default)로 고정 */
    input, div[data-baseweb="select"], textarea, .stNumberInput {
        cursor: default !important;
    }
    
    /* 입력창 내부의 실제 텍스트 입력 영역도 화살표로 변경 */
    input::placeholder, textarea::placeholder {
        cursor: default !important;
    }

    /* 사이드바 내부의 입력 필드들에 대해서도 강제 적용 */
    [data-testid="stSidebar"] * {
        cursor: default !important;
    }
    </style>
""", unsafe_allow_html=True)

# 2. 데이터베이스 연결 및 테이블 생성
def init_db():
    conn = sqlite3.connect('auction_data.db', check_same_thread=False)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS auctions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_date TEXT,
            case_number TEXT,
            item_type TEXT,
            address TEXT,
            category TEXT,
            price INTEGER,
            rooms TEXT,
            area TEXT,
            notes TEXT
        )
    ''')
    conn.commit()
    return conn

conn = init_db()

# 3. 사이드바: 매물 등록 기능 (제목 삭제 및 디자인 수정)
with st.sidebar:
    # 제목 없이 바로 폼 시작
    with st.form("input_form", clear_on_submit=True):
        case_number = st.text_input("사건번호", value="2025타경")
        item_type = st.selectbox("물건종류", ["아파트", "빌라", "오피스텔", "단독주택", "상가", "토지", "기타"])
        
        address_city = st.selectbox("지역(시/군)", ["남양주시", "구리시", "의정부시", "하남시", "서울시", "기타"])
        address_detail = st.text_input("상세 주소")
        full_address = f"{address_city} {address_detail}"
        
        category = st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        price = st.number_input("거래가액 (만원)", min_value=0, step=100)
        
        rooms = st.selectbox("방 개수", ["방1", "방2", "방3", "방4 이상", "해당없음"])
        area = st.text_input("공급/전용 면적")
        notes = st.text_area("특약사항 및 분석내용")
        
        submit_button = st.form_submit_button("DB에 저장하기")

    if submit_button:
        reg_date = datetime.now().strftime("%Y-%m-%d")
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO auctions (reg_date, case_number, item_type, address, category, price, rooms, area, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (reg_date, case_number, item_type, full_address, category, price, rooms, area, notes))
        conn.commit()
        st.success("저장 완료!")
        st.rerun()

# 4. 메인 화면: 데이터 관리 및 검색
st.title("🏠 부동산 경매 매물 관리 시스템")
st.header("📝 실시간 데이터 관리")

# 데이터 불러오기
df = pd.read_sql_query("SELECT * FROM auctions ORDER BY id DESC", conn)

# 통합 검색 기능 (띄어쓰기 AND 검색 지원)
search_query = st.text_input("🔍 통합 검색 (예: '2025 구리시' 입력 시 두 단어 모두 포함된 행 검색)")

if search_query:
    keywords = search_query.split()
    # 모든 컬럼을 문자열로 합쳐서 검색
    combined_series = df.astype(str).apply(lambda x: ' '.join(x), axis=1)
    mask = True
    for key in keywords:
        mask &= combined_series.str.contains(key, case=False)
    display_df = df[mask]
else:
    display_df = df

st.write(f"📊 검색 결과: {len(display_df)} 건")

# 데이터 편집기
edited_df = st.data_editor(
    display_df,
    column_config={"id": None},
    num_rows="dynamic",
    use_container_width=True,
    key="main_editor"
)

# 5. 하단 버튼 영역
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("💾 변경사항 적용"):
        # 편집된 내용을 DB에 덮어쓰기
        edited_df.to_sql('auctions', conn, if_exists='replace', index=False)
        st.success("반영되었습니다!")
        st.rerun()

with col2:
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 전체 백업(CSV)", data=csv, file_name="auction_backup.csv")
