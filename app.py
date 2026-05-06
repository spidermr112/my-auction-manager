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
st.title("🏠 부동산 경매 매물 관리 시스템 (멀티 검색 버전)")

# --- 사이드바: 새 매물 등록 (이전과 동일) ---
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

df = pd.read_sql_query("SELECT * FROM auctions ORDER BY id DESC", conn)

# ⭐ 수정된 검색 로직: "2025 구리시" 처럼 띄어쓰기로 여러 단어 검색 가능
search_query = st.text_input("🔍 통합 검색 (예: '2025 구리시' 입력 시 두 단어 모두 포함된 행 검색)")

if search_query:
    # 1. 검색어를 공백 기준으로 나눕니다 (['2025', '구리시'])
    keywords = search_query.split()
    
    # 2. 모든 행을 문자열 하나로 합친 시리즈 생성
    combined_series = df.astype(str).apply(lambda x: ' '.join(x), axis=1)
    
    # 3. 모든 키워드가 포함되어 있는지 체크 (AND 조건)
    mask = True
    for key in keywords:
        mask &= combined_series.str.contains(key, case=False)
    
    display_df = df[mask]
else:
    display_df = df

st.write(f"📊 검색 결과: {len(display_df)} 건")
edited_df = st.data_editor(
    display_df,
    column_config={"id": None},
    num_rows="dynamic",
    use_container_width=True,
    key="main_editor"
)

# 변경사항 저장 버튼
if st.button("💾 변경사항 적용"):
    edited_df.to_sql('auctions', conn, if_exists='replace', index=False)
    st.success("데이터베이스에 반영되었습니다!")
    st.rerun()
