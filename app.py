import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="파크부동산 통합 관리 시스템", layout="wide")

# 2. 스타일 커스텀 (CSS)
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
    }
    div[data-testid="stExpander"] {
        background-color: white;
        border: 1px solid #e6e9ef;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. 초기 데이터 세팅 (세션 상태 저장)
if 'property_db' not in st.session_state:
    # 이미지 기반 샘플 데이터
    data = [
        ["2024-05-06", "아파트", "매도", "매매", "방3/화1", "3억", "35.0/112.0", "OO동 아파트", "올수리", "진행중"],
        ["2024-05-06", "아파트", "매도", "전세", "방2/화1", "1억 8천", "25.0/84.0", "XX동 빌라", "역세권", "진행중"],
        ["2024-05-06", "상가", "임대", "월세", "1층", "2000/120", "15.0", "△△동 상가", "무권리금", "계약완료"],
        ["2024-05-06", "오피스텔", "매도", "매매", "원룸", "1억 2천", "7.0/15.0", "□□동 오피", "풀옵션", "진행중"],
    ]
    st.session_state.property_db = pd.DataFrame(data, columns=[
        "접수일", "물건분류", "매도매수", "거래유형", "방/화", "거래가액", "면적(전용/공급)", "소재지", "특징", "상태"
    ])

# --- 사이드바: 필터 영역 ---
with st.sidebar:
    st.title("📂 필터링")
    
    st.subheader("물건 종류")
    categories = ["단독/다가구", "빌라/연립", "아파트", "오피스텔(주거)", "바닥/상가", "공장/창고", "토지"]
    selected_cats = []
    for cat in categories:
        if st.checkbox(cat, value=True):
            selected_cats.append(cat)
            
    st.divider()
    
    st.subheader("의뢰목적")
    purpose = st.radio("구분", ["매도", "임대", "매수", "임차"], horizontal=True)
    
    st.subheader("거래유형")
    trade_type = st.multiselect("유형", ["매매", "전세", "월세"], default=["매매", "전세", "월세"])

# --- 메인 영역 ---
st.title("🏠 파크부동산 매물 관리 시스템")

# [개선 1] 매물 등록 섹션을 Expander로 격리
with st.expander("➕ 새 매물 등록하기 (클릭하여 입력창 열기)", expanded=False):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        new_date = st.date_input("접수일", datetime.now())
        new_cat = st.selectbox("물건분류", categories)
        new_purpose = st.radio("매도/매수", ["매도", "임대", "매수", "임차"], horizontal=True)
        
    with col2:
        new_trade = st.radio("거래유형", ["매매", "전세", "월세"], horizontal=True)
        new_price = st.text_input("거래가액", placeholder="예: 3억 5,000 / 2000-100")
        new_room = st.text_input("방/화 수", placeholder="예: 방3 화2")
        
    with col3:
        new_area = st.text_input("면적 (전용/공급)", placeholder="예: 84/112")
        new_addr = st.text_input("소재지 상세")
        new_desc = st.text_area("특징 및 비고", height=68)

    if st.button("💾 데이터베이스 저장", type="primary"):
        new_data = {
            "접수일": new_date.strftime("%Y-%m-%d"),
            "물건분류": new_cat,
            "매도매수": new_purpose,
            "거래유형": new_trade,
            "방/화": new_room,
            "거래가액": new_price,
            "면적(전용/공급)": new_area,
            "소재지": new_addr,
            "특징": new_desc,
            "상태": "진행중"
        }
        st.session_state.property_db = pd.concat([pd.DataFrame([new_data]), st.session_state.property_db], ignore_index=True)
        st.success("매물이 성공적으로 등록되었습니다!")
        st.rerun()

st.divider()

# --- 매물 목록 섹션 ---
st.subheader(f"📊 매물 목록 (조회 결과: {len(st.session_state.property_db)}건)")

# [개선 2] st.dataframe 스타일링 및 가독성 개선
def apply_style(df):
    def style_row(row):
        if row['상태'] == '계약완료':
            return ['background-color: #f1f3f5; color: #adb5bd; text-decoration: line-through'] * len(row)
        elif row['상태'] == '보류':
            return ['background-color: #fff9db; color: #868e96'] * len(row)
        return [''] * len(row)
    
    return df.style.apply(style_row, axis=1)

# 필터링 로직 적용
filtered_df = st.session_state.property_db[
    (st.session_state.property_db['물건분류'].isin(selected_cats)) &
    (st.session_state.property_db['거래유형'].isin(trade_type))
]

# 데이터프레임 출력
st.dataframe(
    apply_style(filtered_df),
    use_container_width=True,
    column_config={
        "접수일": st.column_config.DateColumn("접수일"),
        "거래가액": st.column_config.TextColumn("가격", help="단위: 만원 또는 억"),
        "상태": st.column_config.SelectboxColumn(
            "매물상태",
            options=["진행중", "계약완료", "보류"],
            required=True
        ),
        "소재지": st.column_config.TextColumn("상세 주소", width="medium"),
        "특징": st.column_config.TextColumn("비고/특징", width="large")
    },
    hide_index=True,
    height=500
)

# 하단 정보
st.caption("Tip: '계약완료' 상태로 변경된 행은 자동으로 회색 처리됩니다.")
