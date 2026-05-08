import streamlit as st
import pandas as pd
from datetime import datetime
import re

# 1. 페이지 설정
st.set_page_config(page_title="파크부동산", page_icon="🏘️", layout="wide")
st.title("🏘️ 파크부동산 매물 등록 시스템")

# --- [기존 데이터 정의 및 템플릿 함수 - 수정 없음] ---
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
    tmpl = f"[{sub_cat} {deal_type} 상세]\n- 비밀번호: \n- 로열층/방향: \n- 관리비: \n- 입주일: "
    return check_items, tmpl

if 'df_list' not in st.session_state:
    st.session_state.df_list = pd.DataFrame(columns=["접수일", "고객명", "연락처", "대분류", "소분류", "면적", "가액", "월세", "상태", "소재지", "특약사항"])

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
        client_name = st.text_input("고객명")
        client_phone = st.text_input("연락처")
        main_cat = st.radio("물건 대분류", list(category_map.keys()), horizontal=True)
    with col2:
        sub_cat = st.selectbox("물건 소분류", category_map[main_cat])
        deal_type = st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        addr = st.text_input("소재지 상세")
        price = st.number_input("가액 (만원)", step=0)
        rent = st.number_input("월세 (만원)", step=0) if deal_type == "월세" else 0
    with col3:
        area_text = st.text_input("면적 입력")
        _, py_display = process_area(area_text)
        _, dynamic_tmpl = get_dynamic_template(sub_cat, deal_type)
        memo = st.text_area("특약내용", value=dynamic_tmpl, height=200)

    if st.button("🏠 데이터베이스 저장", use_container_width=True):
        new_row = pd.DataFrame([{"접수일": reg_date.strftime("%Y-%m-%d"), "고객명": client_name, "연락처": client_phone, "대분류": main_cat, "소분류": sub_cat, "면적": py_display, "가액": price, "월세": rent, "상태": "진행중", "소재지": addr, "특약사항": memo}])
        st.session_state.df_list = pd.concat([new_row, st.session_state.df_list], ignore_index=True)
        st.rerun()

st.divider()

# --- [3. 매물 목록 및 "클릭 선택" 기능] ---
if not st.session_state.df_list.empty:
    st.subheader(f"📋 매물 목록 (총 {len(st.session_state.df_list)}건)")
    st.caption("💡 표 맨 왼쪽의 라디오 버튼을 클릭하면 하단 상세 정보가 바뀝니다.")

    # [핵심] st.data_editor에 selection_mode를 추가하여 클릭 감지
    event = st.data_editor(
        st.session_state.df_list,
        use_container_width=True,
        hide_index=False,
        on_select="rerun", # 클릭 시 즉시 화면 갱신
        selection_mode="single_row", # 행 단위 선택 활성화
        column_config={
            "상태": st.column_config.SelectboxColumn("상태", options=["진행중", "완료", "보류", "삭제"]),
            "소재지": st.column_config.TextColumn("📍 소재지 상세", width="large"),
            "특약사항": None # 표에서는 숨겨서 깔끔하게 유지
        },
        column_order=["상태", "소재지", "소분류", "가액", "월세", "면적", "고객명", "연락처"]
    )

    # 4. 하단 상세 정보 자동 연동
    st.markdown("---")
    st.markdown("### 🔍 선택 매물 상세 특약 확인")

    # 선택된 행이 있는지 확인 (사용자가 버튼을 눌렀을 때)
    if hasattr(event, 'selection') and event.selection.rows:
        selected_idx = event.selection.rows[0]
        item = st.session_state.df_list.iloc[selected_idx]
        
        with st.container(border=True):
            c1, c2 = st.columns([1, 2])
            with c1:
                st.info(f"📍 **{item['소재지']}**")
                st.write(f"🏷️ **분류:** {item['소분류']} ({item['상태']})")
                st.write(f"👤 **의뢰인:** {item['고객명']} / {item['연락처']}")
                st.success(f"💰 **금액:** {item['가액']} / {item['월세']}")
            with c2:
                st.markdown("**📜 상세 특약 및 메모**")
                st.text_area("상세내용", value=item.get('특약사항', ""), height=300, label_visibility="collapsed", key=f"v_{selected_idx}")
    else:
        st.info("목록 왼쪽의 체크박스를 선택하면 상세 내용이 여기에 표시됩니다.")
else:
    st.info("매물을 등록해주세요.")
