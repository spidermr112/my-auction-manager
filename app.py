import streamlit as st
import pandas as pd
from datetime import datetime
import re

# 1. 페이지 설정
st.set_page_config(page_title="파크부동산", page_icon="🏘️", layout="wide")
st.title("🏘️ 파크부동산 매물 등록 시스템")

# --- [기존 데이터/유틸리티 로직 - 변경 없음] ---
def get_dynamic_template(sub_cat, deal_type):
    check_items = ["현 시설 상태", "입주시기 협의"]
    res_cats = ["아파트", "연립/다세대", "단독/다가구", "전원주택", "오피스텔(주거)"]
    if sub_cat in res_cats: check_items += ["장기수선충당금", "발코니 확장", "수리 여부"]
    tmpl = f"[{sub_cat} {deal_type} 상세]\n- 비밀번호: \n- 로열층/방향: \n- 관리비: \n- 입주일: "
    return check_items, tmpl

if 'df_list' not in st.session_state:
    st.session_state.df_list = pd.DataFrame(columns=["접수일", "고객명", "연락처", "대분류", "소분류", "면적", "가액", "월세", "상태", "소재지", "특약사항"])

def process_area(input_str):
    if not input_str or input_str.strip() == "": return 0, "-" 
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", input_str)
    if not nums: return 0, "-"
    val = float(nums[0])
    p = int(val) if "평" in input_str else int(round(val * 0.3025))
    return p, f"{p}평"

category_map = {"주거용": ["아파트", "연립/다세대", "단독/다가구", "전원주택", "오피스텔(주거)"], "비주거용": ["상가/사무실", "빌딩/건물", "공장/창고", "지식산업센터", "숙박시설"], "토지": ["대지", "전/답/과수원", "임야", "잡종지", "기타토지", "복수토지"]}

# 2. 매물 등록하기
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

# 3. 매물 필터링 및 목록
with st.expander("🔍 매물 필터링 / 검색", expanded=False):
    f_col1, f_col2, f_col3 = st.columns([1, 1, 1])
    with f_col1: status_list = st.multiselect("상태 선택", ["진행중", "완료", "보류", "삭제"], default=["진행중", "보류"])
    with f_col2: filter_cat = st.multiselect("대분류 선택", list(category_map.keys()), default=list(category_map.keys()))
    with f_col3: search_q = st.text_input("소재지 검색")

df_filtered = st.session_state.df_list.copy()
if not df_filtered.empty:
    df_filtered = df_filtered[df_filtered['상태'].isin(status_list)]
    df_filtered = df_filtered[df_filtered['대분류'].isin(filter_cat)]
    if search_q: df_filtered = df_filtered[df_filtered['소재지'].str.contains(search_q, na=False)]

st.subheader(f"📋 매물 목록 (조회: {len(df_filtered)}건)")

# --- [새로운 방식: 인덱스 선택기] ---
if not df_filtered.empty:
    col_sel, col_empty = st.columns([1, 3])
    with col_sel:
        # 목록 맨 왼쪽의 숫자(Index)를 입력받는 칸입니다.
        # 복수 선택이 원천적으로 불가능하며 딱 하나의 번호만 지정됩니다.
        selected_index = st.number_input("🔍 상세보기 매물 번호(Index) 선택", 
                                         min_value=int(df_filtered.index.min()), 
                                         max_value=int(df_filtered.index.max()), 
                                         value=int(df_filtered.index.min()),
                                         step=1)

    # 데이터 편집기 (오류를 일으키는 최신 인자들 모두 제거)
    edited_data = st.data_editor(
        df_filtered,
        use_container_width=True,
        hide_index=False, # 왼쪽 숫자를 보고 번호를 입력할 수 있게 함
        column_config={
            "상태": st.column_config.SelectboxColumn("상태", options=["진행중", "완료", "보류", "삭제"]),
            "소재지": st.column_config.TextColumn("📍 소재지 상세", width="large"),
            "특약사항": None
        },
        column_order=["상태", "소재지", "소분류", "가액", "월세", "면적", "고객명", "연락처"]
    )

    if st.button("💾 목록 변경 사항 저장", use_container_width=True):
        st.session_state.df_list.update(edited_data)
        st.toast("변경사항이 저장되었습니다.")

    # 4. 하단 상세 정보 연동 (선택된 인덱스 기준)
    st.markdown("---")
    st.markdown(f"### 🔍 [번호 {selected_index}] 매물 상세 특약 확인")
    
    try:
        item = df_filtered.loc[selected_index]
        with st.container(border=True):
            c1, c2 = st.columns([1, 2])
            with c1:
                st.info(f"📍 **{item['소재지']}**")
                st.write(f"🏷️ **분류:** {item['소분류']} ({item['상태']})")
                st.write(f"👤 **고객:** {item['고객명']} / {item['연락처']}")
                st.success(f"💰 **금액:** {item['가액']} / {item['월세']}")
            with c2:
                st.markdown("**📜 상세 특약내용 및 비밀번호**")
                st.text_area("상세내용", value=item.get('특약사항', ""), height=300, label_visibility="collapsed", key=f"view_{selected_index}")
    except:
        st.warning("선택한 번호가 현재 필터링된 목록에 없습니다. 목록 왼쪽의 숫자를 확인해주세요.")
else:
    st.info("조회된 매물이 없습니다.")
