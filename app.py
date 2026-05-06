import streamlit as st
import sqlite3
import pandas as pd
import re
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="파크부동산 매물관리", layout="wide")

# --- 스타일 정의 (구글 스타일 검색바 및 UI) ---
st.markdown("""
    <style>
    /* 구글 스타일 검색창 서식 */
    .search-container {
        display: flex;
        justify-content: center;
        padding: 20px 0;
    }
    .stTextInput input {
        border-radius: 24px !important;
        padding-left: 20px !important;
        border: 1px solid #dfe1e5 !important;
        box-shadow: none !important;
        height: 45px !important;
    }
    .stTextInput input:focus {
        border: 1px solid #dfe1e5 !important;
        box-shadow: 0 1px 6px rgba(32,33,36,0.28) !important;
    }
    /* 타이틀 스타일 */
    .main-title {
        font-size: 40px !important;
        color: #2E5077;
        font-weight: bold;
        text-align: center;
        margin-bottom: 5px;
    }
    .sub-title {
        text-align: center;
        color: #666;
        margin-bottom: 30px;
    }
    /* 테이블 가독성 */
    [data-testid="stDataTable"] {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# 2. DB 초기화 및 데이터 로드
def init_db():
    conn = sqlite3.connect('park_real_estate.db', check_same_thread=False)
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

# 3. 사이드바 (입력 파트 - 기존 라디오 버튼 스타일 유지)
with st.sidebar:
    st.subheader("📍 매물 등록")
    receipt_date = st.date_input("접수일", value=datetime.now())
    main_category = st.radio("물건 대분류", ["주거용", "비주거용", "토지"], horizontal=True)
    sub_map = {
        "주거용": ["아파트", "빌라/다세대", "단독/다가구", "오피스텔(주거)", "전원주택"],
        "비주거용": ["상가/점포", "사무실/오피스", "공장/창고", "지식산업센터", "빌딩/근생건물", "숙박시설"],
        "토지": ["토지"]
    }
    item_type = st.radio("물건 소분류", sub_map[main_category], horizontal=True)
    request_goal = st.radio("의뢰목적", ["매도", "임대", "매수", "임차", "교환"], horizontal=True)

    is_lease = request_goal in ["임대", "임차"]
    is_sale = request_goal in ["매도", "매수", "교환"]

    if main_category == "주거용":
        category = st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        room_count = st.radio("방 개수", ["방1", "방2", "방3", "방4 이상"], horizontal=True)
        bath_count = st.radio("화장실 개수", ["화장실1", "화장실2", "화장실3 이상"], horizontal=True)
    else: category, room_count, bath_count = "", "", ""

    deposit, monthly_rent, price = 0, 0, 0
    if is_lease:
        c1, c2 = st.columns(2)
        with c1: deposit = st.number_input("보증금(만원)", min_value=0, value=None)
        with c2: monthly_rent = st.number_input("차임(만원)", min_value=0, value=None)
    if is_sale:
        price = st.number_input("거래가액(만원)", min_value=0, value=None)

    address = st.text_input("소재지 상세")
    area_raw = st.text_input("면적 (평/㎡)")
    final_area = ""
    if area_raw:
        if "평" in area_raw:
            num = float(re.findall(r"\d+\.?\d*", area_raw)[0])
            final_area = f"{round(num * 3.3058, 2)}㎡ ({num}평)"
        else: final_area = f"{area_raw}㎡"
            
    notes = st.text_area("특약 및 분석내용")
    
    if st.button("🏠 데이터베이스 저장"):
        reg_date_str = datetime.now().strftime("%Y-%m-%d")
        r_date_str = receipt_date.strftime("%Y-%m-%d")
        converted_deposit = (deposit if deposit else 0) + ((monthly_rent if monthly_rent else 0) * 100)
        cur = conn.cursor()
        cur.execute('INSERT INTO auctions (reg_date, receipt_date, item_category, item_type, request_goal, room_count, bath_count, address, category, price, deposit, monthly_rent, converted_deposit, area, notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', 
                    (reg_date_str, r_date_str, main_category, item_type, request_goal, room_count, bath_count, address, category, price, deposit, monthly_rent, converted_deposit, final_area, notes))
        conn.commit()
        st.success("저장 완료!")
        st.rerun()

# 4. 메인 검색 및 결과 파트
st.markdown('<p class="main-title">🏘️ 파크부동산</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">스페이스바로 키워드를 구분하여 검색하세요 (예: 가곡리 빌라 매매)</p>', unsafe_allow_html=True)

# --- [핵심] 구글 스타일 검색창 구현 ---
search_query = st.text_input("", placeholder="🔍 검색어를 입력하세요 (예: 가곡리 아파트 방3)", key="main_search")

# 데이터 불러오기
df = pd.read_sql_query("SELECT * FROM auctions ORDER BY id DESC", conn)

# --- [핵심] 다중 키워드 교차 검색 엔진 ---
if search_query:
    keywords = search_query.split()  # 공백으로 키워드 분리
    filtered_df = df.copy()
    
    for kw in keywords:
        # 각 행의 모든 컬럼을 하나의 문자열로 합쳐서 키워드 포함 여부 확인 (셀 경계 무시)
        mask = filtered_df.astype(str).apply(lambda x: x.str.contains(kw, case=False, na=False)).any(axis=1)
        filtered_df = filtered_df[mask]
    
    display_df = filtered_df
else:
    display_df = df

# 결과 출력
if not display_df.empty:
    st.write(f"검색 결과: **{len(display_df)}** 건")
    st.data_editor(
        display_df,
        column_config={
            "id": None, "price": "가액", "deposit": "보증금", "monthly_rent": "차임", "converted_deposit": "환산보증금", "area": "면적", "reg_date": "등록일", "receipt_date": "접수일"
        },
        num_rows="dynamic", use_container_width=True, key="data_view"
    )
else:
    st.warning("검색 결과가 없습니다.")
