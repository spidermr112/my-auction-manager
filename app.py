import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import re

# 💡 연락처 하이픈 자동 변환 함수
def format_phone_number(input_str):
    if not input_str:
        return ""
    nums = "".join(filter(str.isdigit, input_str))
    if len(nums) == 8:
        nums = "010" + nums
    if len(nums) == 11:
        return f"{nums[:3]}-{nums[3:7]}-{nums[7:]}"
    elif len(nums) == 10:
        return f"{nums[:3]}-{nums[3:6]}-{nums[6:]}"
    return input_str

# 1. 페이지 설정 및 모바일 최적화 CSS
st.set_page_config(page_title="페이지부동산", page_icon="📄", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    
    /* 탭 메뉴 디자인 세련되게 변경 */
    button[data-baseweb="tab"] {
        font-size: 16px !important;
        font-weight: bold !important;
        padding: 12px 20px !important;
    }
    
    div[data-testid="stHorizontalBlock"]:has(.nav-marker) {
        display: flex !important;
        flex-direction: row !important;
        justify-content: center !important;
        align-items: center !important;
        gap: 0px !important;
        width: fit-content !important;
        margin: 10px auto !important;
        padding: 0 !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.nav-marker) > div[data-testid="column"] {
        flex: 0 0 auto !important; width: auto !important; min-width: 0 !important; padding: 0 !important;
    }
    .stButton > button[key^="btn_nav_"] {
        border: 1px solid #dcdfe6 !important; background: white !important; color: #606266 !important;
        font-weight: 700 !important; font-size: 14px !important; height: 36px !important;
        padding: 0 15px !important; border-radius: 8px !important; box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
        transition: all 0.2s !important;
    }
    .stButton > button[key^="btn_nav_"]:hover { border-color: #007AFF !important; color: #007AFF !important; background-color: #f0f7ff !important; }
    .nav-counter { font-family: 'Inter', sans-serif; font-weight: 700; color: #303133; font-size: 15px; line-height: 36px; padding: 0 15px; text-align: center; }
    .nav-marker { display: none; }
    
    .stButton > button[key^="save_slide_"] {
        margin-top: 5px !important; height: 42px !important; border-radius: 8px !important;
        font-weight: 600 !important; background-color: #ffffff !important; border: 1px solid #007AFF !important; color: #007AFF !important;
    }
    .stButton > button[key^="save_slide_"]:hover { background-color: #007AFF !important; color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

st.title("📄 페이지부동산 매물 관리 시스템")

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


# 🔄 요청하신 순서대로 3단 탭 구성 변경!
tab_register, tab_list, tab_search = st.tabs([
    "➕ 신규 매물 등록", 
    "📋 전체 목록 현황", 
    "🔍 매물 검색 및 브리핑"
])


# ==========================================
# 1번째 탭: 신규 매물 등록
# ==========================================
with tab_register:
    st.subheader("➕ 신규 매물 등록 시스템")
    
    with st.container(border=True):
        col1, col2, col3 = st.columns([1, 1, 1.2])
        with col1:
            reg_date = st.date_input("접수일", datetime.today(), key="reg_date")
            client_name = st.text_input("고객명", key="reg_name")
            client_phone = st.text_input("연락처", placeholder="010-    -    (숫자만 쳐도 무관)", key="reg_phone")
            
            if client_phone:
                preview_phone = format_phone_number(client_phone)
                st.caption(f"ℹ️ 저장 예정 포맷: `{preview_phone}`")
                
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

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🏠 구글 시트에 매물 저장", use_container_width=True):
            if not client_name or not addr:
                st.warning("⚠️ 고객명과 소재지 상세는 필수 입력 항목입니다.")
            else:
                _, py_display = process_area(area_text)
                formatted_phone = format_phone_number(client_phone)
                
                new_entry = pd.DataFrame([{
                    "접수일": reg_date.strftime("%Y-%m-%d"), "고객명": client_name, "연락처": formatted_phone, 
                    "대분류": main_cat, "소분류": sub_cat, "면적": py_display, 
                    "가액": price, "월세": rent, "상태": "진행중", "소재지": addr, "특약사항": memo
                }])
                updated_df = pd.concat([new_entry, df_list], ignore_index=True)
                conn.update(data=updated_df)
                st.success("🎉 새로운 매물이 구글 시트에 완벽하게 기록되었습니다!")
                
                # 저장 후 등록 입력 폼 비우기 위해 리런
                st.rerun()


# ==========================================
# 2번째 탭: 전체 목록 현황
# ==========================================
with tab_list:
    st.subheader(f"📋 등록 매물 목록 ({len(df_list)}건)")
    
    # 탭 1에서 새로 등록된 내용을 즉각 반영하여 전체 리스트를 깔끔한 정렬 순서로 표출
    st.data_editor(
        df_list,
        use_container_width=True,
        hide_index=False,
        column_config={
            "상태": st.column_config.SelectboxColumn("상태", options=["진행중", "완료", "보류", "삭제"]),
            "특약사항": None  # 목록 표에서는 메모 공간 제외
        },
        column_order=["상태", "소분류", "소재지", "면적", "가액", "월세", "고객명", "연락처"]
    )


# ==========================================
# 3번째 탭: 매물 검색 및 브리핑
# ==========================================
with tab_search:
    col_top1, col_top2 = st.columns([8, 2])
    with col_top2:
        st.button("🔄 검색 초기화", on_click=reset_all, use_container_width=True, key="btn_reset_tab1")

    # 통합 필터 바
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

    # 상세 브리핑 영역
    if df_filtered.empty:
        st.warning("⚠️ 검색 조건에 맞는 매물이 없습니다. 필터를 조정해 주세요.")
    else:
        st.subheader(f"📋 매물 상세 브리핑 (필터 결과: {len(df_filtered)}건)")

        if "current_idx" not in st.session_state:
            st.session_state.current_idx = 0

        filtered_indices = df_filtered.index.tolist()
        total_count = len(filtered_indices)
        
        if st.session_state.current_idx >= total_count:
            st.session_state.current_idx = 0

        item = df_filtered.loc[filtered_indices[st.session_state.current_idx]]
        
        with st.container(border=True):
            st.info(f"📍 **{item['소재지']}**")
            sc1, sc2 = st.columns(2)
            with sc1:
                st.write(f"🏠 **종류:** {item['소분류']} ({item['상태']})")
                st.write(f"💰 **가액:** {item['가액']} / {item['월세']}")
            with sc2:
                st.write(f"📏 **면적:** {item['면적']}")
                st.write(f"👤 **고객:** {item['고객명']}")
            
            st.write(f"📞 **연락처:** {item['연락처']}")
            st.markdown("**📜 상세 메모**")
            
            new_memo = st.text_area("내용 수정", value=item['특약사항'], height=200, key=f"memo_slide_{item.name}", label_visibility="collapsed")
            
            nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])
            with nav_col1:
                st.markdown('<div class="nav-marker"></div>', unsafe_allow_html=True)
                if st.button("◀ 이전", key="btn_nav_prev"):
                    st.session_state.current_idx = (st.session_state.current_idx - 1) % total_count
                    st.rerun()
            with nav_col2:
                st.markdown(f"<div class='nav-counter'>{st.session_state.current_idx + 1} / {total_count}</div>", unsafe_allow_html=True)
            with nav_col3:
                if st.button("다음 ▶", key="btn_nav_next"):
                    st.session_state.current_idx = (st.session_state.current_idx + 1) % total_count
                    st.rerun()

            if st.button("💾 메모 내용 저장하기", key=f"save_slide_{item.name}", use_container_width=True):
                df_list.at[item.name, '특약사항'] = new_memo
                conn.update(data=df_list)
                st.toast("저장 완료!")
                st.rerun()
