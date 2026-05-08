import streamlit as st
import pandas as pd
from datetime import datetime
import re

# 1. 페이지 설정
st.set_page_config(page_title="파크부동산", page_icon="🏘️", layout="wide")
st.title("🏘️ 파크부동산 매물 등록 시스템")

# --- [데이터 정의: 특약 템플릿 및 체크리스트] ---
TEMPLATES = {
    "아파트": "🏢 [아파트 상세]\n- 로열층 여부: \n- 확장/수리 상태: \n- 관리비 정산: \n- 입주 가능일: ",
    "연립/다세대": "🏠 [연립/다세대 상세]\n- 결로/곰팡이 확인: \n- 방/욕실 수: \n- 주차 가능여부: \n- 불법건축물 여부: ",
    "상가/사무실": "🛍️ [상가 상세]\n- 부가세 별도 여부: \n- 권리금 유무: \n- 전기 용량: \n- 원상복구 조건: ",
    "대지": "🌳 [토지 상세]\n- 지목/용도: \n- 진입로 확보: \n- 지상물 처리: \n- 개발부담금: ",
}

CHECKLIST_ITEMS = {
    "아파트": ["장기수선충당금", "커뮤니티 시설", "융자 상환 조건"],
    "연립/다세대": ["결로/곰팡이 없음", "수도/난방 정상", "내부 비번 확보"],
    "상가/사무실": ["부가세 별도 명시", "렌트프리 기간", "현 업종 승계"],
    "대지": ["진입로 확인", "농취증 필요여부", "토지거래허가"]
}

# --- [세션 상태 초기화] ---
if 'land_price' not in st.session_state: st.session_state.land_price = 0
if 'py_price' not in st.session_state: st.session_state.py_price = 0
if 'search_query' not in st.session_state: st.session_state.search_query = "" 
if 'df_list' not in st.session_state:
    st.session_state.df_list = pd.DataFrame(columns=["접수일", "대분류", "소분류", "가액", "면적", "상태", "소재지"])

# --- [유틸리티 함수] ---
def process_area(input_str):
    if not input_str or input_str.strip() == "": return 0, "-" 
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", input_str)
    if not nums: return 0, "-"
    val = float(nums[0])
    if "평" in input_str: return int(val), f"{int(val)}평"
    return int(round(val * 0.3025)), f"{int(round(val * 0.3025))}평"

def calc_values():
    area_text = st.session_state.get('area_input', '')
    py_num, _ = process_area(area_text)
    current_py_price = st.session_state.get('py_price', 0)
    current_land_price = st.session_state.get('land_price', 0)

    if py_num > 0 and current_py_price > 0:
        st.session_state.land_price = int(current_py_price * py_num)
    elif py_num > 0 and current_land_price > 0 and current_py_price == 0:
        st.session_state.py_price = int(current_land_price / py_num)

category_map = {
    "주거용": ["아파트", "연립/다세대", "단독/다가구", "전원주택", "오피스텔(주거)"],
    "비주거용": ["상가/사무실", "빌딩/건물", "공장/창고", "지식산업센터", "숙박시설"],
    "토지": ["대지", "전/답/과수원", "임야", "잡종지", "기타토지"]
}

# 2. 매물 등록하기
with st.expander("➕ 매물 등록하기", expanded=True):
    col1, col2, col3 = st.columns([1, 1, 1.2])
    
    with col1:
        reg_date = st.date_input("접수일", datetime.today())
        purpose = st.radio("의뢰목적", ["매도의뢰", "매수의뢰"], horizontal=True)
        main_cat = st.radio("물건 대분류", list(category_map.keys()), horizontal=True, index=0)

    with col2:
        sub_cat = st.selectbox("물건 소분류", category_map[main_cat])
        st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        addr = st.text_input("소재지 상세", key="addr_input")
        
        # 가액 입력창 (토지일 경우 평단가 연동 활성화)
        if main_cat == "토지":
            st.number_input("평단가 (만원)", key="py_price", step=0, format="%d", on_change=calc_values)
            st.number_input("거래가액 (만원)", key="land_price", step=0, format="%d", on_change=calc_values)
        else:
            st.number_input("거래가액 (만원)", key="land_price", step=0, format="%d")

    with col3:
        # 면적 입력 및 자동 계산
        area_text = st.text_input("면적 입력", placeholder="예: 100평 또는 330", key="area_input", on_change=calc_values)
        py_num, py_display = process_area(area_text)
        if area_text: st.info(f"💾 계산 기준 면적: {py_display}")
        
        # --- [특약 구성 가이드 섹션 추가] ---
        st.markdown("**📝 특약 체크리스트**")
        selected_checks = []
        checks = CHECKLIST_ITEMS.get(sub_cat, [])
        c_cols = st.columns(2)
        for i, item in enumerate(checks):
            with c_cols[i % 2]:
                if st.checkbox(item, key=f"check_{item}"):
                    selected_checks.append(f"✅ {item}")

        # 템플릿 + 체크항목 결합
        base_tmpl = TEMPLATES.get(sub_cat, "상세 내용을 입력하세요.")
        checked_str = "\n".join(selected_checks)
        combined_memo = f"{base_tmpl}\n\n[체크사항]\n{checked_str}" if selected_checks else base_tmpl

        # 최종 특약내용 입력창 (value에 결합된 텍스트 연동)
        memo = st.text_area("특약내용", value=combined_memo, height=200, key="memo_input")

    if st.button("🏠 데이터베이스 저장", use_container_width=True):
        new_data = {
            "접수일": reg_date.strftime("%Y-%m-%d"),
            "대분류": main_cat, "소분류": sub_cat,
            "가액": st.session_state.land_price, "면적": py_display,
            "상태": "진행중", "소재지": addr
        }
        st.session_state.df_list = pd.concat([st.session_state.df_list, pd.DataFrame([new_data])], ignore_index=True)
        st.success(f"[{sub_cat}] 매물이 성공적으로 등록되었습니다!")
        st.balloons()

st.divider()

# 3. 매물 필터링 및 목록 관리 (기존 유지)
with st.expander("🔍 매물 필터링 / 검색", expanded=True):
    f_col1, f_col2, f_col3 = st.columns([1, 1, 1])
    with f_col1:
        filter_status = st.multiselect("상태 선택", ["진행중", "완료", "보류", "삭제"], default=["진행중", "보류"])
    with f_col2:
        filter_cat = st.multiselect("대분류 선택", list(category_map.keys()), default=list(category_map.keys()))
    with f_col3:
        search_input = st.text_input("소재지 검색", placeholder="동네 이름이나 주소")
        if st.button("🔍 검색", use_container_width=True):
            st.session_state.search_query = search_input

df_filtered = st.session_state.df_list.copy()
if filter_status: df_filtered = df_filtered[df_filtered['상태'].isin(filter_status)]
if filter_cat: df_filtered = df_filtered[df_filtered['대분류'].isin(filter_cat)]
if st.session_state.search_query:
    df_filtered = df_filtered[df_filtered['소재지'].str.contains(st.session_state.search_query, na=False)]

st.subheader(f"📋 매물 목록 관리 (조회: {len(df_filtered)}건)")
edited_df = st.data_editor(
    df_filtered,
    use_container_width=True,
    hide_index=True,
    num_rows="dynamic", 
    column_config={
        "접수일": st.column_config.TextColumn("📅 접수일"),
        "소재지": st.column_config.TextColumn("📍 소재지 상세", width="large"),
        "가액": st.column_config.NumberColumn("💰 가액(만원)", format="%d"),
        "상태": st.column_config.SelectboxColumn("⚙️ 상태", options=["진행중", "완료", "보류", "삭제"], required=True),
    },
    disabled=["접수일", "대분류", "소분류"] 
)

if st.button("💾 모든 변경 사항 저장", use_container_width=True):
    st.session_state.df_list = edited_df
    st.toast("목록이 성공적으로 업데이트되었습니다!")
