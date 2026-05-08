import streamlit as st
import pandas as pd
from datetime import datetime
import re

# 1. 페이지 설정
st.set_page_config(page_title="파크부동산", page_icon="🏘️", layout="wide")
st.title("🏘️ 파크부동산 매물 등록 시스템")

# --- [데이터 정의 및 템플릿 - 기존 유지] ---
def get_dynamic_template(sub_cat, deal_type):
    check_items = ["현 시설 상태", "입주시기 협의"]
    residential_cats = ["아파트", "연립/다세대", "단독/다가구", "전원주택", "오피스텔(주거)"]
    commercial_building_cats = ["상가/사무실", "빌딩/건물", "공장/창고", "지식산업센터", "숙박시설"]
    if sub_cat in residential_cats:
        check_items += ["장기수선충당금", "발코니 확장", "수리 여부"]
        if deal_type == "매매": check_items += ["융자 상환/말소", "가구 포함 여부"]
        else: check_items += ["수도/난방 점검", "반려동물 여부"]
    elif sub_cat in commercial_building_cats:
        check_items += ["부가세 별도", "권리금 확인", "원상복구", "렌트프리"]
    tmpl = f"[{sub_cat} {deal_type} 상세]\n- 비밀번호: \n- 로열층/방향: \n- 확장유무: \n- 관리비: \n- 입주일: "
    return check_items, tmpl

if 'df_list' not in st.session_state:
    st.session_state.df_list = pd.DataFrame(columns=["접수일", "고객명", "연락처", "대분류", "소분류", "면적", "가액", "월세", "상태", "소재지", "특약사항"])

# 선택된 행의 인덱스를 저장하는 세션 상태 (라디오 버튼 기능 핵심)
if 'selected_idx' not in st.session_state:
    st.session_state.selected_idx = None

def process_area(input_str):
    if not input_str or input_str.strip() == "": return 0, "-" 
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", input_str)
    if not nums: return 0, "-"
    val = float(nums[0])
    if "평" in input_str: return int(val), f"{int(val)}평"
    return int(round(val * 0.3025)), f"{int(round(val * 0.3025))}평"

category_map = {"주거용": ["아파트", "연립/다세대", "단독/다가구", "전원주택", "오피스텔(주거)"], "비주거용": ["상가/사무실", "빌딩/건물", "공장/창고", "지식산업센터", "숙박시설"], "토지": ["대지", "전/답/과수원", "임야", "잡종지", "기타토지", "복수토지"]}

# 2. 매물 등록하기 (기존 유지)
with st.expander("➕ 매물 등록하기", expanded=False):
    col1, col2, col3 = st.columns([1, 1, 1.2])
    with col1:
        reg_date = st.date_input("접수일", datetime.today())
        client_name = st.text_input("고객명", key="reg_name")
        client_phone = st.text_input("연락처", key="reg_phone")
        main_cat = st.radio("물건 대분류", list(category_map.keys()), horizontal=True)
    with col2:
        sub_cat = st.selectbox("물건 소분류", category_map[main_cat])
        deal_type = st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        addr = st.text_input("소재지 상세", key="reg_addr")
        price = st.number_input("가액 (만원)", step=0)
        rent = st.number_input("월세 (만원)", step=0) if deal_type == "월세" else 0
    with col3:
        area_text = st.text_input("면적 입력", key="reg_area")
        _, py_display = process_area(area_text)
        _, dynamic_tmpl = get_dynamic_template(sub_cat, deal_type)
        memo = st.text_area("특약내용", value=dynamic_tmpl, height=200)

    if st.button("🏠 데이터베이스 저장", use_container_width=True):
        new_row = pd.DataFrame([{"접수일": reg_date.strftime("%Y-%m-%d"), "고객명": client_name, "연락처": client_phone, "대분류": main_cat, "소분류": sub_cat, "면적": py_display, "가액": price, "월세": rent, "상태": "진행중", "소재지": addr, "특약사항": memo}])
        st.session_state.df_list = pd.concat([new_row, st.session_state.df_list], ignore_index=True)
        st.rerun()

st.divider()

# 3. 매물 필터링 및 목록 관리
with st.expander("🔍 매물 필터링 / 검색", expanded=False):
    f_col1, f_col2, f_col3 = st.columns([1, 1, 1])
    with f_col1: status_list = st.multiselect("상태 선택", ["진행중", "완료", "보류", "삭제"], default=["진행중", "보류"])
    with f_col2: filter_cat = st.multiselect("대분류 선택", list(category_map.keys()), default=list(category_map.keys()))
    with f_col3: search_q = st.text_input("소재지 검색")

df_filtered = st.session_state.df_list.copy()
if '상태' in df_filtered.columns: df_filtered = df_filtered[df_filtered['상태'].isin(status_list)]
if '대분류' in df_filtered.columns: df_filtered = df_filtered[df_filtered['대분류'].isin(filter_cat)]
if '소재지' in df_filtered.columns and search_q: df_filtered = df_filtered[df_filtered['소재지'].str.contains(search_q, na=False)]

st.subheader(f"📋 매물 목록 (조회: {len(df_filtered)}건)")
st.caption("💡 목록에서 매물을 클릭(선택)하면 하단에 상세 정보가 표시됩니다.")

# [핵심] 단일 선택 라디오 버튼처럼 작동하는 data_editor
# 사용자의 Streamlit 버전에 맞춰 가장 범용적인 'on_change' 혹은 'on_select' 대신 인덱스 직접 활용
df_display = df_filtered.copy()

# 데이터 편집 및 선택 감지
edited_output = st.data_editor(
    df_display,
    use_container_width=True,
    hide_index=False, # 왼쪽 숫자 인덱스를 클릭 포인트로 활용
    num_rows="dynamic",
    on_select="rerun", # 선택 시 즉시 리런
    selection_mode="single_row", # <--- 이 옵션이 '라디오 버튼' 역할을 수행합니다 (중복 선택 불가)
    column_config={
        "상태": st.column_config.SelectboxColumn("상태", options=["진행중", "완료", "보류", "삭제"]),
        "소재지": st.column_config.TextColumn("📍 소재지 상세", width="large"),
        "특약사항": None 
    },
    column_order=["상태", "소재지", "소분류", "가액", "월세", "면적", "고객명", "연락처"]
)

if st.button("💾 목록 변경 사항 저장", use_container_width=True):
    st.session_state.df_list = edited_output
    st.toast("저장되었습니다.")

# 4. 하단 상세 정보 연동 (라디오 방식)
st.markdown("---")
st.markdown("### 🔍 선택 매물 상세 특약 확인")

# 선택된 행 정보를 안전하게 추출
selected_rows = edited_output.selection.rows if hasattr(edited_output, 'selection') else []

if selected_rows:
    idx = selected_rows[0] # single_row 모드라 무조건 1개만 잡힘
    item = df_filtered.iloc[idx]
    
    with st.container(border=True):
        c1, c2 = st.columns([1, 2])
        with c1:
            st.info(f"📍 **{item['소재지']}**")
            st.write(f"🏷️ **분류:** {item['소분류']} ({item['상태']})")
            st.write(f"👤 **고객:** {item['고객명']} / {item['연락처']}")
            st.success(f"💰 **금액:** {item['가액']} / {item['월세']}")
        with c2:
            st.markdown("**📜 상세 특약내용 및 메모**")
            st.text_area("상세내용", value=item.get('특약사항', ""), height=300, label_visibility="collapsed", key=f"v_{idx}")
else:
    st.info("목록 왼쪽의 숫자(행)를 클릭하여 매물을 선택해 주세요.")
