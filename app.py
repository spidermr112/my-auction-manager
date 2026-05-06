import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# 1. 페이지 설정 및 마우스 커서 CSS 적용
st.set_page_config(page_title="부동산 경매 매물 관리자", layout="wide")

st.markdown("""
    <style>
    input, div[data-baseweb="select"], textarea, .stNumberInput {
        cursor: default !important;
    }
    input::placeholder, textarea::placeholder {
        cursor: default !important;
    }
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
            receipt_date TEXT,
            item_category TEXT,
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

# 3. 사이드바: 매물 등록 기능 (물건종류 그룹화 적용)
with st.sidebar:
    with st.form("input_form", clear_on_submit=True):
        receipt_date = st.date_input("접수일", value=datetime.now())
        
        # --- 물건종류 그룹화 로직 ---
        # 1단계: 큰 분류 선택
        main_category = st.selectbox("물건 대분류", ["주거용", "비주거용", "기타"])
        
        # 2단계: 대분류에 따른 세부 종류 설정
        if main_category == "주거용":
            sub_options = ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택"]
        elif main_category == "비주거용":
            sub_options = ["상가/근린시설", "사무실", "공장/창고", "지식산업센터", "숙박시설"]
        else:
            sub_options = ["토지", "임야", "잡종지", "기타"]
            
        item_type = st.selectbox("물건 소분류", sub_options)
        # --------------------------

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
        r_date_str = receipt_date.strftime("%Y-%m-%d")
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO auctions (reg_date, receipt_date, item_category, item_type, address, category, price, rooms, area, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (reg_date, r_date_str, main_category, item_type, full_address, category, price, rooms, area, notes))
        conn.commit()
        st.success(f"[{main_category}] {item_type} 저장 완료!")
        st.rerun()

# 4. 메인 화면: 데이터 관리 및 검색
st.title("🏠 부동산 경매 매물 관리 시스템")
st.header("📝 실시간 데이터 관리")

df = pd.read_sql_query("SELECT * FROM auctions ORDER BY id DESC", conn)

search_query = st.text_input("🔍 통합 검색 (예: '주거용 남양주' 입력 시 대분류와 지역 동시 검색)")

if search_query:
    keywords = search_query.split()
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
    column_config={
        "id": None,
        "receipt_date": st.column_config.TextColumn("접수일"),
        "item_category": st.column_config.TextColumn("대분류"),
        "item_type": st.column_config.TextColumn("물건종류"),
        "reg_date": st.column_config.TextColumn("등록일")
    },
    num_rows="dynamic",
    use_container_width=True,
    key="main_editor"
)

# 5. 하단 버튼 영역
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("💾 변경사항 적용"):
        edited_df.to_sql('auctions', conn, if_exists='replace', index=False)
        st.success("반영되었습니다!")
        st.rerun()

with col2:
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 전체 백업(CSV)", data=csv, file_name="auction_backup.csv")
