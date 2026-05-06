import streamlit as st
import sqlite3
import pandas as pd
import re
from datetime import datetime

# 1. 페이지 설정 및 엔터 키 제어
st.set_page_config(page_title="부동산 경매 매물 관리자", layout="wide")

def format_korean_price(price_manwon):
    if price_manwon is None or price_manwon == 0: return "0원"
    eok = price_manwon // 10000
    man = price_manwon % 10000
    result = []
    if eok > 0: result.append(f"{int(eok)}억")
    if man > 0: result.append(f"{int(man):,}만원")
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
    input, textarea, .stNumberInput { cursor: default !important; }
    [data-testid="stSidebar"] * { cursor: default !important; }
    div[data-testid="stWidgetLabel"] { font-weight: bold; margin-bottom: -5px; }
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
            category TEXT, price INTEGER, deposit INTEGER, monthly_rent INTEGER, 
            converted_deposit INTEGER, area TEXT, notes TEXT
        )
    ''')
    conn.commit()
    return conn

conn = init_db()

# 3. 사이드바: 매물 등록
with st.sidebar:
    st.subheader("🏠 매물 등록")
    
    receipt_date = st.date_input("접수일", value=datetime.now())
    
    # [대분류] 라디오 버튼
    main_category = st.radio("물건 대분류", ["주거용", "비주거용", "토지"], horizontal=True)
    
    # [소분류] 라디오 버튼
    sub_map = {
        "주거용": ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택"],
        "비주거용": ["상가/점포", "사무실/오피스", "공장/창고", "지식산업센터", "빌딩/근생건물", "숙박시설"],
        "토지": ["토지"]
    }
    item_type = st.radio("물건 소분류", sub_map[main_category], horizontal=True)

    # [의뢰목적] 라디오 버튼 (복수선택 제거하여 깔끔하게 통일)
    request_goal = st.radio("의뢰목적", ["매도", "임대", "매수", "임차", "교환"], horizontal=True)

    # 임대/매매 여부 판단
    is_lease = request_goal in ["임대", "임차"]
    is_sale = request_goal in ["매도", "매수", "교환"]

    # 주거용 부가 정보
    if main_category == "주거용":
        category = st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        room_count = st.radio("방 개수", ["방1", "방2", "방3", "방4 이상"], horizontal=True)
        bath_count = st.radio("화장실 개수", ["화장실1", "화장실2", "화장실3 이상"], horizontal=True)
    else:
        category, room_count, bath_count = "", "", ""

    # 금액 입력부
    deposit, monthly_rent, converted_deposit, price = 0, 0, 0, 0
    if is_lease:
        col1, col2 = st.columns(2)
        with col1: deposit = st.number_input("보증금 (만원)", min_value=0, value=None, step=100)
        with col2: monthly_rent = st.number_input("차임 (만원)", min_value=0, value=None, step=10)
        c_dep = deposit if deposit is not None else 0
        c_rent = monthly_rent if monthly_rent is not None else 0
        converted_deposit = c_dep + (c_rent * 100)
        st.info(f"⚖️ **환산보증금: {format_korean_price(converted_deposit)}**")

    if is_sale:
        price = st.number_input("거래가액 (만원)", min_value=0, value=None, step=100)
        if price: st.info(f"💰 **거래가액 확인: {format_korean_price(price)}**")

    address = st.text_input("소재지 (상세 주소 포함)")
    
    # 면적 자동 변환
    area_raw = st.text_input("면적 (평 또는 ㎡)", placeholder="입력 후 엔터")
    final_area = ""
    if area_raw:
        if "평" in area_raw:
            try:
                num = float(re.findall(r"\d+\.?\d*", area_raw)[0])
                final_area = f"{round(num * 3.3058, 2)}㎡ ({num}평)"
            except: final_area = area_raw
        else: final_area = f"{area_raw}㎡"
        st.info(f"📐 **최종 면적: {final_area}**")
            
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
                  deposit, monthly_rent, converted_deposit, final_area, notes))
            conn.commit()
            st.success("✅ 저장이 완료되었습니다!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ 저장 오류 발생: {e}")

# 4. 메인 화면
st.title("🏠 부동산 경매 매물 관리 시스템")
df = pd.read_sql_query("SELECT * FROM auctions ORDER BY id DESC", conn)

if not df.empty:
    st.data_editor(
        df,
        column_config={
            "id": None, "price": st.column_config.NumberColumn("가액(만원)", format="%d"),
            "deposit": st.column_config.NumberColumn("보증금", format="%d"),
            "monthly_rent": st.column_config.NumberColumn("차임", format="%d"),
            "converted_deposit": st.column_config.NumberColumn("환산보증금", format="%d"),
        },
        num_rows="dynamic", use_container_width=True
    )
