import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# 1. 데이터베이스 연결
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

# --- 화면 구성 ---
st.set_page_config(page_title="부동산 경매 매물 관리자", layout="wide")
st.title("🏠 부동산 경매 매물 관리 시스템")

# --- 사이드바: 새 매물 등록 ---
with st.sidebar:
    st.header("➕ 새 매물 등록하기")
    with st.form("input_form", clear_on_submit=True):
        case_number = st.text_input("사건번호", value="2025타경")
        item_type = st.selectbox("물건종류", ["아파트", "빌라", "오피스텔", "단독주택", "상가", "토지", "기타"])
        
        address_city = st.selectbox("지역(시/군)", ["남양주시", "구리시", "의정부시", "하남시", "서울시", "기타"])
        address_detail = st.text_input("상세 주소")
        full_address = f"{address_city} {address_detail}"
        
        category = st.radio("구분", ["매매", "전세", "월세"])
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

# --- 메인 화면: 데이터 관리 ---
st.header("📝 실시간 데이터 관리")

# 전체 데이터 불러오기
df = pd.read_sql_query("SELECT * FROM auctions ORDER BY id DESC", conn)

# ⭐ 핵심: 통합 검색 기능
# 검색창에 입력하면 사건번호, 주소, 메모 등 '모든 컬럼'에서 해당 글자를 찾습니다.
search_query = st.text_input("🔍 통합 검색 (사건번호, 주소, 메모 등 아무거나 입력하세요)")

if search_query:
    # 모든 셀의 내용을 문자열로 합쳐서 검색어가 포함되어 있는지 검사 (대소문자 무시)
    mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
    display_df = df[mask]
else:
    display_df = df

# 데이터 편집기 출력
st.write(f"📊 검색 결과: {len(display_df)} 건")
edited_df = st.data_editor(
    display_df,
    column_config={"id": None}, # ID 열 숨김
    num_rows="dynamic",
    use_container_width=True,
    key="main_editor"
)

# 변경사항 저장 및 기타 버튼
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    if st.button("💾 변경사항 적용"):
        # 편집기에서 수정한 내용을 실제 DB에 덮어씌움
        # 주의: 검색 중일 때는 필터링된 데이터만 있으므로 전체 데이터 관리에 유의해야 합니다.
        edited_df.to_sql('auctions', conn, if_exists='replace', index=False)
        st.success("반영되었습니다!")
        st.rerun()

with col2:
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 전체 백업(CSV)", data=csv, file_name="auction_data.csv")
