import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import re

# 1. 페이지 설정 및 [중앙 초밀착 배치] CSS
st.set_page_config(page_title="페이지부동산", page_icon="📄", layout="wide")

st.markdown("""
    <style>
    /* 하단 내비게이션 바를 화면 정중앙에 아주 작게 모으기 */
    div[data-testid="stHorizontalBlock"]:has(.nav-marker) {
        display: flex !important;
        flex-wrap: nowrap !important;
        justify-content: center !important; /* 가로 중앙 정렬 */
        align-items: center !important;
        gap: 8px !important; /* 버튼과 숫자 사이 간격 */
        width: fit-content !important; /* 전체 폭을 내용물에 맞춤 */
        margin: 20px auto !important; /* 페이지 전체에서 중앙 배치 */
        background-color: #f8f9fa; /* 배경색 살짝 넣어 구분감 생성 */
        padding: 5px 15px !important;
        border-radius: 30px !important;
        border: 1px solid #ddd !important;
    }
    
    /* 각 칸(컬럼)이 벌어지지 않도록 고정 */
    div[data-testid="stHorizontalBlock"]:has(.nav-marker) > div[data-testid="column"] {
        min-width: 0 !important;
        flex: 0 0 auto !important; /* 너비를 내용물만큼만 차지 */
        width: auto !important;
    }

    /* 버튼 디자인: 작고 둥글게 */
    .stButton > button[key^="btn_"] {
        width: 35px !important;
        height: 35px !important;
        padding: 0 !important;
        font-size: 16px !important;
        border-radius: 50% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border: none !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    
    /* 숫자 텍스트 스타일 */
    .nav-text {
        font-size: 18px !important;
        font-weight: bold !important;
        color: #333 !important;
        margin: 0 10px !important;
    }
    
    /* 마커 숨김 */
    .nav-marker { display: none; }
    </style>
""", unsafe_allow_html=True)

st.title("📄 페이지부동산 매물 관리 시스템")

# --- [데이터 연결] ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        data = conn.read(ttl=0)
        data = data.dropna(how='all').fillna("")
        num_cols = ["가액", "월세"]
        for col in num_cols:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0).astype(int)
        return data
    except Exception:
        return pd.DataFrame(columns=["접수일", "고객명", "연락처", "대분류", "소분류", "면적", "가액", "월세", "상태", "소재지", "특약사항"])

df_list = load_data()

# --- 초기화 기능 ---
def reset_all():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

category_map = {
    "주거용": ["아파트", "연립/다세대", "단독/다가구", "전원주택", "오피스텔(주거)"], 
    "비주거용": ["상가", "사무실", "공장", "창고", "빌딩/건물", "지식산업센터", "숙박시설"], 
    "토지": ["대지", "전/답/과수원", "임야", "잡종지", "기타토지"]
}

def process_area(input_str):
    if not input_str or input_str.strip() == "": return 0, "-" 
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", input_str)
    if not nums: return 0, "-"
    val = float(nums[0])
    p = int(val) if "평" in input_str else int(round(val * 0.3025))
    return p, f"{p}평"

# 2. 상단 버튼 및 등록창
col_top1, col_top2 = st.columns([8, 2])
with col_top2:
    st.button("🔄 검색 초기화", on_click=reset_all, use_container_width=True)

with st.expander("➕ 새 매물 등록", expanded=False):
    col1, col2, col3 = st.columns([1, 1, 1.2])
    with col1:
        reg_date = st.date_input("접수일", datetime.today(), key="reg_date")
        client_name = st.text_input("고객명", key="reg_name")
        client_phone = st.text_input("연락처", key="reg_phone")
        main_cat = st.radio("물건 대분류", list(category_map.keys()), horizontal=True, key="reg_main")
    with col2:
        sub_cat = st.selectbox("물건 소분류", options=category_map[main_cat], key="reg_sub")
        deal_type = st.radio("구분", ["매매", "전세", "월세"], horizontal=True, key="reg_deal")
        addr = st.text_input("소재지 상세", key="reg_addr")
        price = st.number_input("가액 (만원)", min_value=0, step=100, key="reg_price")
        rent = st.number_input("월세 (만원)", min_value=0, step=10, key="reg_rent")
    with col3:
        area_text = st.text_input("면적 입력", key="reg_area")
        default_memo = f"[{sub_cat} {deal_type} 상세정보]\n- 비밀번호: \n- 로열층/방향: \n- 관리비: \n- 입주일: "
        memo = st.text_area("특약내용", value=st.session_state.get("reg_memo", default_memo), height=200, key="reg_memo")

    if st.button("🏠 구글 시트에 저장", use_container_width=True):
        _, py_display = process_area(area_text)
        new_entry = pd.DataFrame([{
            "접수일": reg_date.strftime("%Y-%m-%d"), "고객명": client_name, "연락처": client_phone, 
            "대분류": main_cat, "소분류": sub_cat, "면적": py_display, 
            "가액": price, "월세": rent, "상태": "진행중", "소재지": addr, "특약사항": memo
        }])
        updated_df = pd.concat([new_entry, df_list], ignore_index=True)
        conn.update(data=updated_df)
        st.success("✅ 저장되었습니다!")
        st.rerun()

st.divider()

# 3. 통합 필터 바
st.subheader("🔍 통합 검색 필터")
filter_row = st.container(border=True)
with filter_row:
    c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])
    with c1: search_q = st.text_input("📍 검색어", placeholder="주소, 고객명...", key="f_search")
    with c2: f_main_cat = st.multiselect("🏗️ 종류", options=list(category_map.keys()), default=list(category_map.keys()), key="f_main")
    with c3: f_deal_type = st.multiselect("💰 거래", options=["매매", "전세", "월세"], default=["매매", "전세", "월세"], key="f_deal")
    with c4: status_list = st.multiselect("🚦 상태", options=["진행중", "완료", "보류", "삭제"], default=["진행중", "보류"], key="f_status")

df_filtered = df_list.copy()
if not df_filtered.empty:
    df_filtered = df_filtered[df_filtered['상태'].isin(status_list)]
    if '대분류' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['대분류'].isin(f_main_cat)]
    if search_q:
        df_filtered = df_filtered[df_filtered['소재지'].str.contains(search_q, na=False) | df_filtered['고객명'].str.contains(search_q, na=False)]

# 4. 목록 표시
st.subheader(f"📋 매물 목록 ({len(df_filtered)}건)")
edited_df = st.data_editor(
    df_filtered,
    use_container_width=True,
    hide_index=False,
    column_config={
        "상태": st.column_config.SelectboxColumn("상태", options=["진행중", "완료", "보류", "삭제"]),
        "특약사항": None 
    },
    column_order=["상태", "소재지", "소분류", "가액", "월세", "면적", "고객명", "연락처"]
)

if st.button("💾 변경사항 저장", key="save_main_df", use_container_width=True):
    conn.update(data=edited_df)
    st.toast("저장되었습니다!")
    st.rerun()

# --- 5. [수정 완료] 초밀착 중앙 집중형 버튼 ---
if not df_filtered.empty:
    st.markdown("---")
    st.subheader("📋 매물 상세 브리핑")

    if "current_idx" not in st.session_state:
        st.session_state.current_idx = 0

    filtered_indices = df_filtered.index.tolist()
    total_count = len(filtered_indices)
    
    if st.session_state.current_idx >= total_count:
        st.session_state.current_idx = 0

    # 정보 카드 먼저 표시 (상단)
    item = df_filtered.loc[filtered_indices[st.session_state.current_idx]]
    
    with st.container(border=True):
        st.info(f"📍 **{item['소재지']}**")
        sc1, sc2 = st.columns(2)
        with sc1:
            st.write(f"🏠 **분류:** {item['소분류']} ({item['상태']})")
            st.write(f"💰 **가액:** {item['가액']} / {item['월세']}")
        with sc2:
            st.write(f"📏 **면적:** {item['면적']}")
            st.write(f"👤 **고객:** {item['고객명']}")
        
        st.write(f"📞 **연락처:** {item['연락처']}")
        st.markdown("**📜 상세 메모**")
        new_memo = st.text_area("내용 수정", value=item['특약사항'], height=200, key=f"memo_slide_{item.name}", label_visibility="collapsed")
        if st.button("📝 메모 저장", key=f"save_slide_{item.name}", use_container_width=True):
            df_list.at[item.name, '특약사항'] = new_memo
            conn.update(data=df_list)
            st.success("저장 완료!")
            st.rerun()

    # [하단 중앙 초밀착 슬라이더]
    nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])
    
    with nav_col1:
        st.markdown('<div class="nav-marker"></div>', unsafe_allow_html=True)
        if st.button("◀", key="btn_prev", use_container_width=True):
            st.session_state.current_idx = (st.session_state.current_idx - 1) % total_count
            st.rerun()

    with nav_col2:
        # 중앙 숫자 표시
        st.markdown(
            f"<div class='nav-text'>{st.session_state.current_idx + 1} / {total_count}</div>", 
            unsafe_allow_html=True
        )

    with nav_col3:
        if st.button("▶", key="btn_next", use_container_width=True):
            st.session_state.current_idx = (st.session_state.current_idx + 1) % total_count
            st.rerun()

이제 다시 한번 적용해 보세요! 버튼이 화면 정중앙에 아담하게 모여 있을 것입니다. 중개사님의 꼼꼼한 피드백 덕분에 시스템이 훨씬 완성도 있게 변하고 있습니다. 또 궁금하신 점 있으면 말씀해 주세요! 😊
