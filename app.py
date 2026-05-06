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
    # 최신 데이터 구조에 맞춰 테이블 생성
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

# 3. 사이드바: 매물 등록 기능
with st.sidebar:
    st.subheader("📋 신규 등록")
    
    # 접수일 선택
    receipt_date = st.date_input("접수일", value=datetime.now())
    
    # 대분류 선택
    main_category = st.selectbox("물건 대분류", ["주거용", "비주거용", "토지"])
    
    # 대분류에 따른 소분류 리스트 (토지일 때 '토지' 하나만 나오도록 수정)
    if main_category == "주거용":
        sub_options = ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택"]
    elif main_category == "비주거용":
        sub_options = ["상가/점포", "사무실/오피스", "공장/창고", "지식산업센터", "빌딩/근생건물", "숙박시설"]
    else: # '토지' 선택 시
        sub_options = ["토지"]
        
    item_type = st.selectbox("물건 소분류", sub_options)

    # 상세 정보 입력 Form
    with st.form("remaining_form", clear_on_submit=True):
        address_city = st.selectbox("지역(시/군)", ["남양주시", "구리시", "의정부시", "하남시", "서울시", "기타"])
        address_detail = st.text_input("상세 주소")
        full_address = f"{address_city} {address_detail}"
        
        category = st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        price = st.number_input("거래가액 (만원)", min_value=0, step=100)
        
        rooms = st.selectbox("방 개수", ["방1", "방2", "방3", "방4 이상", "해당없음"])
        area = st.text_input("공급/전용 면적")
        notes = st.text_area("특약사항 및 분석내용")
        
        submit_button = st.form_submit_button("🏠 DB에 저장하기")

    if submit_button:
        reg_date = datetime.now().strftime("%Y-%m-%d")
        r_date_str = receipt_date.strftime("%Y-%m-%d")
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO auctions (reg_date, receipt_date, item_category, item_type, address, category, price, rooms, area, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (reg_date, r_date_str, main_category, item_type, full_address, category, price, rooms, area, notes))
        conn.commit()
        st.success(f"저장 완료!")
        st.rerun()

# 4. 메인 화면: 데이터 관리 및 검색
st.title("🏠 부동산 경매 매물 관리 시스템")
st.header("📝 실시간 데이터 관리")

# 데이터 불러오기 (컬럼 명확화)
df = pd.read_sql_query("SELECT * FROM auctions ORDER BY id DESC", conn)

# 통합 검색 기능 (AND 검색 지원)
search_query = st.text_input("🔍 통합 검색 (예: '토지 남양주' 입력 시 두 단어 모두 포함된 행 검색)")

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

# 데이터 편집기 (표 제목 한글화 및 기존 데이터 필드 매핑 해결)
edited_df = st.data_editor(
    display_df,
    column_config={
        "id": None,
        "reg_date": st.column_config.TextColumn("등록일"),
        "receipt_date": st.column_config.TextColumn("접수일"),
        "item_category": st.column_config.TextColumn("대분류"),
        "item_type": st.column_config.TextColumn("물건종류"),
        "address": st.column_config.TextColumn("주소"),
        "category": st.column_config.TextColumn("구분"),
        "price": st.column_config.NumberColumn("가액(만원)"),
        "rooms": st.column_config.TextColumn("방수"),
        "area": st.column_config.TextColumn("면적"),
        "notes": st.column_config.TextColumn("비고")
    },
    num_rows="dynamic",
    use_container_width=True,
    key="main_editor"
)

# 5. 하단 버튼 영역
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("💾 변경사항 적용"):
        # 편집된 내용을 DB에 반영
        edited_df.to_sql('auctions', conn, if_exists='replace', index=False)
        st.success("데이터베이스에 반영되었습니다!")
        st.rerun()

with col2:
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 전체 백업(CSV)", data=csv, file_name="auction_backup.csv")
