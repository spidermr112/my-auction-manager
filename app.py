import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# 1. 데이터베이스 연결 및 테이블 생성
# SQLite는 파일 하나로 관리되며, 다중 접속 환경(Streamlit)을 위해 check_same_thread=False 설정이 중요합니다.
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
st.title("🏠 부동산 경매 매물 관리 시스템 (SQLite 버전)")

# --- 사이드바: 새 매물 등록 ---
with st.sidebar:
    st.header("➕ 새 매물 등록하기")
    with st.form("input_form", clear_on_submit=True):
        case_number = st.text_input("사건번호", value="2025타경")
        item_type = st.text_input("물건종류", value="빌라")
        address = st.text_input("소재지", value="남양주시")
        category = st.radio("구분", ["매매", "전세", "월세"])
        price = st.number_input("거래가액 (만원)", min_value=0, step=100)
        rooms = st.text_input("방 개수", value="방1")
        area = st.text_input("공급/전용 면적")
        notes = st.text_area("특약사항 및 분석내용")
        
        submit_button = st.form_submit_button("DB에 저장하기")

    if submit_button:
        reg_date = datetime.now().strftime("%Y-%m-%d")
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO auctions (reg_date, case_number, item_type, address, category, price, rooms, area, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (reg_date, case_number, item_type, address, category, price, rooms, area, notes))
        conn.commit()
        st.success("데이터베이스에 안전하게 저장되었습니다!")
        st.rerun()

# --- 메인 화면: 데이터 관리 ---
st.header("📝 실시간 데이터 관리")

# 1. 데이터 불러오기
df = pd.read_sql_query("SELECT * FROM auctions ORDER BY id DESC", conn)

# 2. 검색 기능
search_query = st.text_input("🔍 검색어 입력 (사건번호, 주소 등 모든 항목 검색)")
if search_query:
    df = df[df.apply(lambda row: row.astype(str).str.contains(search_query).any(), axis=1)]

# 3. 데이터 편집기 (st.data_editor)
# 여기서 수정한 내용은 '변경사항 적용' 버튼을 눌러야 실제 DB에 반영됩니다.
st.write("💡 표 안의 내용을 클릭해서 직접 수정할 수 있습니다.")
edited_df = st.data_editor(
    df,
    column_config={"id": None}, # ID 열은 내부 관리용이므로 숨김
    num_rows="dynamic", # 행 추가/삭제 가능
    use_container_width=True,
    key="main_editor"
)

# 4. 저장 및 관리 버튼
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button("💾 변경사항 적용"):
        # 편집된 데이터를 통째로 DB에 다시 씀 (데이터 양이 적을 때 효율적)
        edited_df.to_sql('auctions', conn, if_exists='replace', index=False)
        st.success("수정사항이 반영되었습니다.")
        st.rerun()

with col2:
    # 엑셀 백업 기능 (CSV 형식)
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 엑셀(CSV) 백업",
        data=csv,
        file_name=f"경매매물백업_{datetime.now().strftime('%Y%m%d')}.csv",
        mime='text/csv'
    )

with col3:
    if st.button("⚠️ 전체 데이터 초기화"):
        if st.checkbox("정말로 삭제하시겠습니까? (체크 후 버튼 클릭)"):
            cur = conn.cursor()
            cur.execute("DELETE FROM auctions")
            conn.commit()
            st.warning("모든 데이터가 삭제되었습니다.")
            st.rerun()
