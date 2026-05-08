import streamlit as st
import pandas as pd
from datetime import datetime
import re

# 1. 페이지 설정
st.set_page_config(page_title="파크부동산", page_icon="🏘️", layout="wide")
st.title("🏘️ 파크부동산 매물 등록 시스템")

# --- [데이터 정의: 소분류 + 구분에 따른 정교한 템플릿] ---
def get_dynamic_template(sub_cat, deal_type):
    check_items = ["현 시설 상태", "입주시기 협의"]
    
    # 카테고리 그룹 정의
    residential_cats = ["아파트", "연립/다세대", "단독/다가구", "전원주택", "오피스텔(주거)"]
    commercial_building_cats = ["상가/사무실", "빌딩/건물", "공장/창고", "지식산업센터", "숙박시설"]
    
    # 1. 체크리스트 항목 설정
    if sub_cat in residential_cats:
        check_items += ["장기수선충당금", "발코니 확장", "수리 여부"]
        if deal_type == "매매": check_items += ["융자 상환/말소", "가구 포함 여부"]
        else: check_items += ["수도/난방 점검", "반려동물 여부"]
    elif sub_cat in commercial_building_cats:
        check_items += ["부가세 별도", "권리금 확인", "원상복구", "렌트프리"]
        if deal_type == "월세": check_items += ["전기 용량", "관리비 포함 내역"]
    elif sub_cat in ["대지", "전/답/과수원", "임야", "잡종지", "기타토지", "복수토지"]:
        check_items += ["진입로 확인", "지상 적치물", "농취증", "토지거래허가"]
        if sub_cat == "복수토지":
            check_items += ["필지별 면적 확인", "건물 포함 여부", "개별매매 불가 명시"]

    # 2. 텍스트 템플릿 설정
    tmpl = f"[{sub_cat} {deal_type} 상세]\n"
    if sub_cat in residential_cats:
        tmpl += "- 로열층/방향: \n- 확장유무: \n- 관리비: \n- 입주일: "
    elif sub_cat in commercial_building_cats: # 빌딩/건물 등 포함
        tmpl += "- 전용면적: \n- 현재업종: \n- 주차대수: \n- 화장실 위치: "
    elif sub_cat == "복수토지":
        tmpl += "- 매각 대상 필지수: \n- 총 면적 합계: \n- 건물 포함 여부: \n- 공부상 지목들: "
    else: # 순수 토지류
        tmpl += "- 용도지역: \n- 지목: \n- 현재이용상태: "

    return check_items, tmpl

# --- [세션 상태 초기화] ---
if 'land_price' not in st.session_state: st.session_state.land_price = 0
if 'py_price' not in st.session_state: st.session_state.py_price = 0
if 'monthly_rent' not in st.session_state: st.session_state.monthly_rent = 0
if 'search_query' not in st.session_state: st.session_state.search_query = "" 
if 'df_list' not in st.session_state:
    st.session_state.df_list = pd.DataFrame(columns=["접수일", "고객명", "연락처", "대분류", "소분류", "면적", "가액", "월세", "상태", "소재지"])

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
    "토지": ["대지", "전/답/과수원", "임야", "잡종지", "기타토지", "복수토지"] 
}

# 2. 매물 등록하기
with st.expander("➕ 매물 등록하기", expanded=True):
    col1, col2, col3 = st.columns([1, 1, 1.2])
    
    with col1:
        reg_date = st.date_input("접수일", datetime.today())
        purpose = st.radio("의뢰목적", ["매도의뢰", "매수의뢰"], horizontal=True)
        st.markdown("👤 **고객 정보**")
        client_name = st.text_input("고객명", placeholder="이름 입력", key="client_name")
        client_phone = st.text_input("연락처", placeholder="010-0000-0000", key="client_phone")
        main_cat = st.radio("물건 대분류", list(category_map.keys()), horizontal=True)

    with col2:
        sub_cat = st.selectbox("물건 소분류", category_map[main_cat])
        deal_type = st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        addr = st.text_input("소재지 상세", key="addr_input")
        
        if main_cat == "토지":
            st.number_input("평단가 (만원)", key="py_price", step=0, format="%d", on_change=calc_values)
            st.number_input("거래가액 (만원)", key="land_price", step=0, format="%d", on_change=calc_values)
        else:
            st.number_input("가액/보증금 (만원)", key="land_price", step=0, format="%d")
            if deal_type == "월세":
                st.number_input("월세 (만원)", key="monthly_rent", step=0, format="%d")

    with col3:
        area_text = st.text_input("면적 입력", placeholder="예: 100평 또는 330", key="area_input", on_change=calc_values)
        py_num, py_display = process_area(area_text)
        if area_text: st.info(f"💾 계산 기준 면적: {py_display}")
        
        st.markdown("**📝 특약 체크리스트**")
        dynamic_checks, dynamic_tmpl = get_dynamic_template(sub_cat, deal_type)
        
        selected_checks = []
        c_cols = st.columns(2)
        for i, item in enumerate(dynamic_checks):
            with c_cols[i % 2]:
                if st.checkbox(item, key=f"cb_{sub_cat}_{deal_type}_{item}"):
                    selected_checks.append(f"✅ {item}")

        checked_str = "\n".join(selected_checks)
        combined_memo = f"{dynamic_tmpl}\n\n[체크사항]\n{checked_str}" if selected_checks else dynamic_tmpl
        
        # 동적 Key 부여로 입력창 즉시 갱신
        memo_key = f"memo_{sub_cat}_{deal_type}_{len(selected_checks)}"
        memo = st.text_area("특약내용", value=combined_memo, height=200, key=memo_key)

    if st.button("🏠 데이터베이스 저장", use_container_width=True):
        new_row = pd.DataFrame([{
            "접수일": reg_date.strftime("%Y-%m-%d"),
            "고객명": client_name, "연락처": client_phone,
            "대분류": main_cat, "소분류": sub_cat,
            "면적": py_display,
            "가액": st.session_state.get('land_price', 0), 
            "월세": st.session_state.get('monthly_rent', 0) if deal_type == "월세" else 0,
            "상태": "진행중", "소재지": addr
        }])
        st.session_state.df_list = pd.concat([new_row, st.session_state.df_list], ignore_index=True)
        st.success(f"[{client_name}]님의 매물이 저장되었습니다!")
        st.balloons()
        st.rerun()

st.divider()

# --- [매물 필터링 및 목록 관리 (기존 유지)] ---
# (이후 코드는 이전과 동일하므로 생략 가능하나 전체 코드가 필요하시면 위 내용대로 사용하시면 됩니다)
