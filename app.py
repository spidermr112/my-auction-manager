import streamlit as st
import pandas as pd
from datetime import datetime
import re

# 1. 페이지 설정
st.set_page_config(page_title="파크부동산", page_icon="🏘️", layout="wide")
st.title("🏘️ 파크부동산 매물 등록 시스템")

# --- [데이터 정의 및 템플릿 함수] ---
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
        if deal_type == "월세": check_items += ["전기 용량", "관리비 포함 내역"]
    elif sub_cat in ["대지", "전/답/과수원", "임야", "잡종지", "기타토지", "복수토지"]:
        check_items += ["진입로 확인", "지상 적치물", "농취증", "토지거래허가"]

    tmpl = f"[{sub_cat} {deal_type} 상세]\n"
    if sub_cat in residential_cats:
        tmpl += "- 비밀번호: \n- 로열층/방향: \n- 확장유무: \n- 관리비: \n- 입주일: "
    elif sub_cat in commercial_building_cats:
        tmpl += "- 비밀번호: \n- 전용면적: \n- 현재업종: \n- 주차대수: \n- 화장실 위치: "
    else:
        tmpl += "- 용도지역: \n- 지목: \n- 현재이용상태: "

    return check_items, tmpl

# --- [세션 상태 초기화] ---
if 'df_list' not in st.session_state:
    st.session_state.df_list = pd.DataFrame(columns=["접수일", "고객명", "연락처", "대분류", "소분류", "면적", "가액", "월세", "상태", "소재지", "특약사항"])

# --- [유틸리티 함수] ---
def process_area(input_str):
    if not input_str or input_str.strip() == "": return 0, "-" 
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", input_str)
    if not nums: return 0, "-"
    val = float(nums[0])
    if "평" in input_str: return int(val), f"{int(val)}평"
    return int(round(val * 0.3025)), f"{int(round(val * 0.3025))}평"

category_map = {
    "주거용": ["아파트", "연립/다세대", "단독/다가구", "전원주택", "오피스텔(주거)"],
    "비주거용": ["상가/사무실", "빌딩/건물", "공장/창고", "지식산업센터", "숙박시설"],
    "토지": ["대지", "전/답/과수원", "임야", "잡종지", "기타토지", "복수토지"] 
}

# 2. 매물 등록 섹션
with st.expander("➕ 매물 등록하기", expanded=True):
    col1, col2, col3 = st.columns([1, 1, 1.2])
    with col1:
        reg_date = st.date_input("접수일", datetime.today())
        client_name = st.text_input("고객명", key="reg_name")
        client_phone = st.text_input("연락처", key="reg_phone")
        main_cat = st.radio("물건 대분류", list(category_map.keys()), horizontal=True)
    with col2:
        sub_cat = st.selectbox("물건 소분류", category_map[main_cat])
        deal_type = st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        addr = st.text_input("소재지 상세")
        price = st.number_input("가액/보증금 (만원)", step=100)
        rent = st.number_input("월세 (만원)", step=5) if deal_type == "월세" else 0
    with col3:
        area_input = st.text_input("면적 입력 (예: 30평)")
        _, py_display = process_area(area_input)
        _, tmpl = get_dynamic_template(sub_cat, deal_type)
        memo = st.text_area("특약내용", value=tmpl, height=200)

    if st.button("🏠 데이터베이스 저장", use_container_width=True):
        new_data = pd.DataFrame([{"접수일": reg_date.strftime("%Y-%m-%d"), "고객명": client_name, "연락처": client_phone, "대분류": main_cat, "소분류": sub_cat, "면적": py_display, "가액": price, "월세": rent, "상태": "진행중", "소재지": addr, "특약사항": memo}])
        st.session_state.df_list = pd.concat([new_data, st.session_state.df_list], ignore_index=True)
        st.rerun()

st.divider()

# 3. 매물 목록 및 자동 연동 섹션
st.subheader(f"📋 매물 목록 (총 {len(st.session_state.df_list)}건)")
st.caption("💡 왼쪽의 체크박스를 선택하면 하단에 상세 내용이 자동으로 나타납니다.")

# [핵심] selection_mode="single_row"를 사용하여 행 선택 가능하게 설정
event = st.dataframe(
    st.session_state.df_list,
    use_container_width=True,
    hide_index=True,
    on_select="rerun", # 선택 시 즉시 화면 갱신
    selection_mode="single_row", 
    column_config={
        "상태": "⚙️ 상태",
        "소재지": st.column_config.TextColumn("📍 소재지 상세", width="large"),
        "특약사항": None # 표에서는 숨김 (하단에서 크게 보기 위함)
    },
    column_order=["상태", "소재지", "소분류", "가액", "월세", "면적", "고객명", "연락처"]
)

# 4. 하단 상세 연동창
st.markdown("---")
st.markdown("### 🔍 선택 매물 상세 특약 확인")

# 선택된 행이 있는지 확인
selected_rows = event.selection.rows

if selected_rows:
    # 선택된 행의 인덱스를 통해 데이터를 가져옴
    idx = selected_rows[0]
    item = st.session_state.df_list.iloc[idx]
    
    with st.container(border=True):
        c1, c2 = st.columns([1, 2])
        with c1:
            st.info(f"📍 **{item['소재지']}**")
            st.write(f"🏷️ **분류:** {item['소분류']} ({item['상태']})")
            st.write(f"👤 **의뢰인:** {item['고객명']} / {item['연락처']}")
            st.success(f"💰 **금액:** {item['가액']} / {item['월세']}")
        with c2:
            st.markdown("**📜 상세 특약 및 메모**")
            st.text_area("상세내용", value=item['특약사항'], height=300, label_visibility="collapsed", key=f"detail_{idx}")
else:
    st.info("목록에서 매물을 선택(체크)하면 상세 내용이 이곳에 표시됩니다.")
