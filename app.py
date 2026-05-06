import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="부동산 경매 매물 관리자", layout="wide")

# 마우스 커서 디자인 유지
st.markdown("""
    <style>
    input, div[data-baseweb="select"], textarea, .stNumberInput { cursor: default !important; }
    [data-testid="stSidebar"] * { cursor: default !important; }
    </style>
""", unsafe_allow_html=True)

# 2. 데이터베이스 초기화 로직
def init_db():
    db_name = 'auction_data.db'
    conn = sqlite3.connect(db_name, check_same_thread=False)
    cur = conn.cursor()
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS auctions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_date TEXT,
            receipt_date TEXT,
            item_category TEXT,
            item_type TEXT,
            request_goal TEXT,
            room_count TEXT,
            bath_count TEXT,
            address TEXT,
            category TEXT,
            price INTEGER,
            area TEXT,
            notes TEXT
        )
    ''')
    
    # 컬럼 누락 방지 (OperationalError 예방)
    columns = [col[1] for col in cur.execute("PRAGMA table_info(auctions)").fetchall()]
    check_cols = ["request_goal", "room_count", "bath_count", "receipt_date"]
    for col in check_cols:
        if col not in columns:
            cur.execute(f"ALTER TABLE auctions ADD COLUMN {col} TEXT")
            
    conn.commit()
    return conn

conn = init_db()

# 3. 사이드바: 매물 등록 기능
with st.sidebar:
    st.subheader("🏠 매물 등록")
    
    receipt_date = st.date_input("접수일", value=datetime.now())
    main_category = st.selectbox("물건 대분류", ["주거용", "비주거용", "토지"])
    
    if main_category == "주거용":
        sub_options = ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택"]
    elif main_category == "비주거용":
        sub_options = ["상가/점포", "사무실/오피스", "공장/창고", "지식산업센터", "빌딩/근생건물", "숙박시설"]
    else:
        sub_options = ["토지"]
        
    item_type = st.selectbox("물건 소분류", sub_options)

    with st.form("input_form", clear_on_submit=True):
        if main_category == "주거용":
            request_goal = st.radio("의뢰목적", ["매수/임차", "매도/임대"], horizontal=True)
            category = st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
            room_count = st.radio("방 개수", ["방1", "방2", "방3", "방4 이상"], horizontal=True)
            bath_count = st.radio("화장실 개수", ["화장실1", "화장실2", "화장실3 이상"], horizontal=True)
        else:
            request_goal, category, room_count, bath_count = "", "", "", ""

        # [수정] 거래가액 기본값을 5000으로 설정
        price = st.number_input("거래가액 (만원)", min_value=0, value=5000, step=100)
        address = st.text_input("소재지 (상세 주소 포함)")
        area = st.text_input("공급/전용 면적 (㎡)")
        notes = st.text_area("특약사항 및 분석내용")
        
        submit_button = st.form_submit_button("🏠 데이터베이스에 저장")

    if submit_button:
        reg_date_str = datetime.now().strftime("%Y-%m-%d")
        r_date_str = receipt_date.strftime("%Y-%m-%d")
        cur = conn.cursor()
        
        try:
            cur.execute('''
                INSERT INTO auctions (
                    reg_date, receipt_date, item_category, item_type, request_goal, 
                    room_count, bath_count, address, category, price, area, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (reg_date_str, r_date_str, main_category, item_type, request_goal, 
                  room_count, bath_count, address, category, price, area, notes))
            conn.commit()
            st.success("✅ 저장이 완료되었습니다!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ 저장 중 오류 발생: {e}")

# 4. 메인 화면
st.title("🏠 부동산 경매 매물 관리 시스템")

try:
    df = pd.read_sql_query("SELECT * FROM auctions ORDER BY id DESC", conn)
    if not df.empty:
        edited_df = st.data_editor(
            df,
            column_config={
                "id": None, "reg_date": "등록일", "receipt_date": "접수일", 
                "item_category": "대분류", "item_type": "물건종류", 
                "request_goal": "의뢰목적", "room_count": "방수", 
                "bath_count": "화장실수", "address": "주소", 
                "category": "구분", "price": "가액(만원)", 
                "area": "면적", "notes": "비고"
            },
            num_rows="dynamic", use_container_width=True
        )
        if st.button("💾 변경사항 적용"):
            edited_df.to_sql('auctions', conn, if_exists='replace', index=False)
            st.success("🔄 데이터가 업데이트되었습니다!")
            st.rerun()
    else:
        st.info("등록된 매물이 없습니다.")
except:
    st.warning("데이터베이스를 준비 중입니다...")
