import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# 1. 페이지 설정 및 엔터 키/커서 제어 스크립트
st.set_page_config(page_title="부동산 경매 매물 관리자", layout="wide")

# 한글 금액 변환 함수
def format_korean_price(price_manwon):
    if price_manwon is None or price_manwon == 0:
        return "0원"
    eok = price_manwon // 10000
    man = price_manwon % 10000
    result = []
    if eok > 0:
        result.append(f"{int(eok)}억")
    if man > 0:
        result.append(f"{int(man):,}만원")
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

# 2. 데이터베이스 초기화 및 자동 보수 로직
def init_db():
    conn = sqlite3.connect('auction_data.db', check_same_thread=False)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS auctions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_date TEXT, receipt_date TEXT, item_category TEXT, item_type TEXT,
            request_goal TEXT, room_count TEXT, bath_count TEXT, address TEXT,
            category TEXT, price INTEGER, deposit INTEGER, monthly_rent INTEGER, 
            converted_deposit INTEGER, area TEXT, notes TEXT
        )
    ''')
    conn.commit()
    return conn

conn = init_db()

# 3. 사이드바: 매물 등록 기능
with st.sidebar:
    st.subheader("🏠 매물 등록")
    
    receipt_date = st.date_input("접수일", value=datetime.now())
    main_category = st.selectbox("물건 대분류", ["주거용", "비주거용", "토지"])
    
    # 소분류 설정 (복수 선택)
    sub_map = {
        "주거용": ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택"],
        "비주거용": ["상가/점포", "사무실/오피스", "공장/창고", "지식산업센터", "빌딩/근생건물", "숙박시설"],
        "토지": ["토지"]
    }
    selected_sub = st.multiselect("물건 소분류 (복수 선택)", sub_map[main_category])
    item_type = ", ".join(selected_sub)

    # 의뢰목적 선택 (복수 선택)
    goal_options = ["매도", "임대", "매수", "임차", "교환"]
    goals = st.multiselect("의뢰목적 (복수 선택)", goal_options)
    request_goal = ", ".join(goals)

    # 상태 체크 로직
    is_lease = any(x in goals for x in ["임대", "임차"])
    is_sale = any(x in goals for x in ["매도", "매수", "교환"])

    if main_category == "주거용":
        category = st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        room_count = st.radio("방 개수", ["방1", "방2", "방3", "방4 이상"], horizontal=True)
        bath_count = st.radio("화장실 개수", ["화장실1", "화장실2", "화장실3 이상"], horizontal=True)
    else:
        category, room_count, bath_count = "", "", ""

    # --- 금액 입력부 로직 수정 ---
    deposit, monthly_rent, converted_deposit, price = 0, 0, 0, 0

    # 1. 임대/임차 관련 입력 (보증금, 차임)
    if is_lease:
        col1, col2 = st.columns(2)
        with col1:
            deposit = st.number_input("보증금 (만원)", min_value=0, value=None, step=100)
        with col2:
            monthly_rent = st.number_input("차임 (만원)", min_value=0, value=None, step=10)
        
        calc_deposit = deposit if deposit is not None else 0
        calc_rent = monthly_rent if monthly_rent is not None else 0
        converted_deposit = calc_deposit + (calc_rent * 100)
        st.info(f"⚖️ **환산보증금: {format_korean_price(converted_deposit)}**")

    # 2. 매도/매수/교환 관련 입력 (거래가액)
    # 임대차와 매매가 동시에 선택되었거나, 매매류만 선택되었을 때 나타남
    if is_sale:
        price = st.number_input("거래가액 (만원)", min_value=0, value=None, step=100, placeholder="매매/교환가 입력")
        if price:
            st.info(f"💰 **거래가액 확인: {format_korean_price(price)}**")
    
    # 만약 아무것도 선택 안된 초기 상태라면 기본 거래가액 창 보여주기
    if not is_lease and not is_sale:
        price = st.number_input("거래가액 (만원)", min_value=0, value=None, step=100)

    address = st.text_input("소재지 (상세 주소 포함)")
    area = st.text_input("공급/전용 면적 (㎡)")
    notes = st.text_area("특약사항 및 분석내용")
    
    if st.button("🏠 데이터베이스에 저장"):
        reg_date_str = datetime.now().strftime("%Y-%m-%d")
        r_date_str = receipt_date.strftime("%Y-%m-%d")
        cur = conn.cursor()
        try:
            cur.execute('''
                INSERT INTO auctions (
                    reg_date, receipt_date, item_category, item_type, request_goal, 
                    room_count, bath_count, address, category, price, 
                    deposit, monthly_rent, converted_deposit, area, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (reg_date_str, r_date_str, main_category, item_type, request_goal, 
                  room_count, bath_count, address, category, price, 
                  deposit, monthly_rent, converted_deposit, area, notes))
            conn.commit()
            st.success("✅ 저장이 완료되었습니다!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ 저장 오류 발생: {e}")

# 4. 메인 화면
st.title("🏠 부동산 경매 매물 관리 시스템")
df = pd.read_sql_query("SELECT * FROM auctions ORDER BY id DESC", conn)

if not df.empty:
    edited_df = st.data_editor(
        df,
        column_config={
            "id": None, "reg_date": "등록일", "receipt_date": "접수일", 
            "item_category": "대분류", "item_type": "물건종류", "request_goal": "의뢰목적",
            "price": st.column_config.NumberColumn("가액(만원)", format="%d"),
            "deposit": st.column_config.NumberColumn("보증금", format="%d"),
            "monthly_rent": st.column_config.NumberColumn("차임", format="%d"),
            "converted_deposit": st.column_config.NumberColumn("환산보증금", format="%d"),
        },
        num_rows="dynamic", use_container_width=True
    )
    if st.button("💾 변경사항 적용"):
        edited_df.to_sql('auctions', conn, if_exists='replace', index=False)
        st.success("🔄 업데이트 완료!")
        st.rerun()
