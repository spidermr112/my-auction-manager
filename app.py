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

# 2. 데이터베이스 연결 및 테이블 생성 (request_goal 컬럼 추가)
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
    conn.commit()
    return conn

conn = init_db()

# 3. 사이드바: 매물 등록 기능
with st.sidebar:
    st.subheader("📋 신규 등록")
    
    receipt_date = st.date_input("접수일", value=datetime.now())
    main_category = st.selectbox("물건 대분류", ["주거용", "비주거용", "토지"])
    
    if main_category == "주거용":
        sub_options = ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택"]
    elif main_category == "비주거용":
        sub_options = ["상가/점포", "사무실/오피스", "공장/창고", "지식산업센터", "빌딩/근생건물", "숙박시설"]
    else:
        sub_options = ["토지"]
        
    item_type = st.selectbox("물건 소분류", sub_options)

    with st.form("remaining_form", clear_on_submit=True):
        
        # [핵심 수정] 주거용일 때만 나타나는 전용 옵션
        if main_category == "주거용":
            # 1. 의뢰목적 (새로 추가된 항목)
            request_goal = st.radio("의뢰목적", ["매수/임차", "매도/임대"], horizontal=True)
            
            # 2. 구분 (매매/전세/월세)
            category = st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
            
            # 3. 방 및 화장실 개수
            col1, col2 = st.columns(2)
            with col1:
                room_count = st.selectbox("방 개수", ["방1", "방2", "방3", "방4 이상"])
            with col2:
                bath_count = st.selectbox("화장실 개수", ["화장실1", "화장실2", "화장실3 이상"])
        else:
            request_goal = "해당없음"
            category = "해당없음"
            room_count = "N/A"
            bath_count = "N/A"

        address = st.text_input("소재지 (상세 주소 포함)")
        price = st.number_input("거래가액 (만원)", min_value=0, step=100)
        area = st.text_input("공급/전용 면적 (㎡)")
        notes = st.text_area("특약사항 및 분석내용")
        
        submit_button = st.form_submit_button("🏠 DB에 저장하기")

    if submit_button:
        reg_date = datetime.now().strftime("%Y-%m-%d")
        r_date_str = receipt_date.strftime("%Y-%m-%d")
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO auctions (reg_date, receipt_date, item_category, item_type, request_goal, room_count, bath_count, address, category, price, area, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (reg_date, r_date_str, main_category, item_type, request_goal, room_count, bath_count, address, category, price, area, notes))
        conn.commit()
        st.success(f"등록 완료!")
        st.rerun()

# 4. 메인 화면: 데이터 관리 및 검색
st.title("🏠 부동산 경매 매물 관리 시스템")
st.header("📝 실시간 데이터 관리")

df = pd.read_sql_query("SELECT * FROM auctions ORDER BY id DESC", conn)

search_query = st.text_input("🔍 통합 검색")

if search_query:
    keywords = search_query.split()
    combined_series = df.astype(str).apply(lambda x: ' '.join(x), axis=1)
    mask = True
    for key in keywords:
        mask &= combined_series.str.contains(key, case=False)
    display_df = df[mask]
else:
    display_df = df

# 데이터 편집기 (의뢰목적 컬럼 추가)
edited_df = st.data_editor(
    display_df,
    column_config={
        "id": None,
        "reg_date": st.column_config.TextColumn("등록일"),
        "receipt_date": st.column_config.TextColumn("접수일"),
        "item_category": st.column_config.TextColumn("대분류"),
        "item_type": st.column_config.TextColumn("물건종류"),
        "request_goal": st.column_config.TextColumn("의뢰목적"), # 추가
        "room_count": st.column_config.TextColumn("방수"),
        "bath_count": st.column_config.TextColumn("화장실수"),
        "address": st.column_config.TextColumn("주소"),
        "category": st.column_config.TextColumn("구분"),
        "price": st.column_config.NumberColumn("가액(만원)"),
        "area": st.column_config.TextColumn("면적"),
        "notes": st.column_config.TextColumn("비고")
    },
    num_rows="dynamic",
    use_container_width=True,
    key="main_editor"
)

col1, col2 = st.columns([1, 4])
with col1:
    if st.button("💾 변경사항 적용"):
        edited_df.to_sql('auctions', conn, if_exists='replace', index=False)
        st.success("반영되었습니다!")
        st.rerun()

with col2:
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 전체 백업(CSV)", data=csv, file_name="auction_backup.csv")
