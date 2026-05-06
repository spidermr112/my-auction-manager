import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# 1. 페이지 설정 및 엔터 키 동작 제어 스크립트
st.set_page_config(page_title="부동산 경매 매물 관리자", layout="wide")

# [추가] 만원 단위 숫자를 한글(억, 만원)로 변환하는 함수
def format_korean_price(price_manwon):
    if price_manwon is None or price_manwon == 0:
        return ""
    
    eok = price_manwon // 10000
    man = price_manwon % 10000
    
    result = []
    if eok > 0:
        result.append(f"{int(eok)}억")
    if man > 0:
        result.append(f"{int(man):,}만원") # 천단위 쉼표 포함
    
    return " ".join(result)

st.markdown("""
    <script>
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            const inputs = Array.from(document.querySelectorAll('input, textarea, select'));
            const index = inputs.indexOf(document.activeElement);
            if (index > -1 && index < inputs.length - 1) {
                inputs[index + 1].focus();
                e.preventDefault(); 
            }
        }
    });
    </script>
    <style>
    input, div[data-baseweb="select"], textarea, .stNumberInput { cursor: default !important; }
    [data-testid="stSidebar"] * { cursor: default !important; }
    </style>
""", unsafe_allow_html=True)

# 2. DB 초기화
def init_db():
    conn = sqlite3.connect('auction_data.db', check_same_thread=False)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS auctions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_date TEXT, receipt_date TEXT, item_category TEXT, item_type TEXT,
            request_goal TEXT, room_count TEXT, bath_count TEXT, address TEXT,
            category TEXT, price INTEGER, area TEXT, notes TEXT
        )
    ''')
    conn.commit()
    return conn

conn = init_db()

# 3. 사이드바: 매물 등록
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

    if main_category == "주거용":
        request_goal = st.radio("의뢰목적", ["매수/임차", "매도/임대"], horizontal=True)
        category = st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        room_count = st.radio("방 개수", ["방1", "방2", "방3", "방4 이상"], horizontal=True)
        bath_count = st.radio("화장실 개수", ["화장실1", "화장실2", "화장실3 이상"], horizontal=True)
    else:
        request_goal, category, room_count, bath_count = "", "", "", ""

    # 거래가액 입력
    price = st.number_input("거래가액 (만원)", min_value=0, value=None, step=100, placeholder="숫자 입력")
    
    # [추가된 핵심 기능] 숫자를 입력하면 바로 아래에 한글 단위로 표시
    if price:
        st.info(f"💰 **한글 확인: {format_korean_price(price)}**")

    address = st.text_input("소재지 (상세 주소 포함)")
    area = st.text_input("공급/전용 면적 (㎡)")
    notes = st.text_area("특약사항 및 분석내용")
    
    if st.button("🏠 데이터베이스에 저장"):
        reg_date_str = datetime.now().strftime("%Y-%m-%d")
        r_date_str = receipt_date.strftime("%Y-%m-%d")
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO auctions (reg_date, receipt_date, item_category, item_type, request_goal, 
            room_count, bath_count, address, category, price, area, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (reg_date_str, r_date_str, main_category, item_type, request_goal, 
              room_count, bath_count, address, category, price, area, notes))
        conn.commit()
        st.success("✅ 저장이 완료되었습니다!")
        st.rerun()

# 4. 메인 화면
st.title("🏠 부동산 경매 매물 관리 시스템")
df = pd.read_sql_query("SELECT * FROM auctions ORDER BY id DESC", conn)

if not df.empty:
    edited_df = st.data_editor(
        df,
        column_config={
            "id": None, "reg_date": "등록일", "receipt_date": "접수일", 
            "item_category": "대분류", "item_type": "물건종류", 
            "price": st.column_config.NumberColumn("가액(만원)", format="%d") # 소수점 제거
        },
        num_rows="dynamic", use_container_width=True
    )
    if st.button("💾 변경사항 적용"):
        edited_df.to_sql('auctions', conn, if_exists='replace', index=False)
        st.rerun()
