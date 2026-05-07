import streamlit as st
import pandas as pd
from datetime import datetime
import re

# 1. 페이지 설정
st.set_page_config(page_title="파크부동산 통합 관리 시스템", page_icon="🏘️", layout="wide")
st.title("🏘️ 파크부동산 통합 관리 시스템")

# --- [세션 상태 초기화] ---
# 입력창 값 관리
if 'land_price' not in st.session_state: st.session_state.land_price = None
if 'py_price' not in st.session_state: st.session_state.py_price = None
if 'land_area_val' not in st.session_state: st.session_state.land_area_val = 0 
# ★ 실제 목록 데이터 저장소
if 'df_list' not in st.session_state:
    st.session_state.df_list = pd.DataFrame(columns=["접수일", "대분류", "소분류", "가액", "면적", "상태"])

# --- [단위 판별 및 변환 로직 - 오류 수정 버전] ---
def process_area_input(input_str):
    if not input_str or input_str.strip() == "": 
        return 0, "0평", "면적을 입력해주세요."
    
    # 숫자 추출 (소수점 포함)
    numbers = re.findall(r"[-+]?\d*\.\d+|\d+", input_str)
    if not numbers: 
        return 0, "0평", "숫자를 포함하여 입력해주세요."
    
    val = float(numbers[0])
    
    # '평' 글자가 있으면 그대로 평, 숫자만 있으면 ㎡로 간주하여 환산
    if "평" in input_str:
        py_val = int(val)
        msg = f"✅ '평' 입력 감지: {py_val}평"
    else:
        py_val = int(round(val * 0.3025))
        msg = f"🔄 ㎡ 환산 완료: {py_val}평"
        
    return py_val, f"{py_val}평", msg

# --- [연동 계산 함수] ---
def update_by_total():
    if st.session_state.land_area_val > 0 and st.session_state.land_price:
        st.session_state.py_price = int(st.session_state.land_price / st.session_state.land_area_val)

def update_by_py_price():
    if st.session_state.land_area_val > 0 and st.session_state.py_price:
        st.session_state.land_price = int(st.session_state.py_price * st.session_state.land_area_val)

# 2. 새 매물 등록 섹션
category_map = {
    "주거용": ["아파트", "연립/다세대", "단독/다가구", "전원주택", "오피스텔(주거)"],
    "비주거용": ["상가/사무실", "빌딩/건물", "공장/창고", "지식산업센터", "숙박시설"],
    "토지": ["대지", "전/답/과수원", "임야", "잡종지", "기타토지"]
}

with st.expander("➕ 새 매물 등록하기", expanded=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        reg_date = st.date_input("접수일", datetime.today())
        main_cat = st.radio("물건 대분류", list(category_map.keys()), horizontal=True, index=2)
        st.radio("의뢰목적", ["매도", "임대", "매수", "임차"], horizontal=True)
    
    with col2:
        sub_cat = st.selectbox("물건 소분류", category_map[main_cat])
        st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        
        if main_cat == "토지":
            st.text_input("소재지 상세", placeholder="소재지 상세 주소를 입력하세요", key="addr_input")
            # step=0으로 설정하여 +,- 버튼 제거
            st.number_input("평단가 (만원)", key="py_price", value=st.session_state.py_price, step=0, format="%d", on_change=update_by_py_price)
            st.number_input("거래가액 (만원)", key="land_price", value=st.session_state.land_price, step=0, format="%d", on_change=update_by_total)
        else:
            st.number_input("거래가액 (만원)", step=0, format="%d", value=None)
    
    with col3:
        # 면적 입력창 (텍스트 입력)
        area_text = st.text_input("면적 입력", placeholder="예: 100평 또는 330", key="area_input")
        py_num, py_display, msg = process_area_input(area_text)
        st.session_state.land_area_val = py_num 
        
        if area_text:
            st.info(msg)
            
        st.text_area("특약내용", height=110, placeholder="특약사항을 입력하세요", key="memo_input")

    # ★ 데이터 저장 버튼 (목록에 실제로 쌓이게 함)
    if st.button("🏠 데이터베이스 저장", use_container_width=True):
        if area_text and (st.session_state.land_price or 0) > 0:
            new_entry = {
                "접수일": reg_date.strftime("%Y-%m-%d"),
                "대분류": main_cat,
                "소분류": sub_cat,
                "가액": st.session_state.land_price if st.session_state.land_price else 0,
                "면적": py_display,
                "상태": "진행중"
            }
            # 데이터프레임에 추가
            st.session_state.df_list = pd.concat([st.session_state.df_list, pd.DataFrame([new_entry])], ignore_index=True)
            st.success("매물이 성공적으로 목록에 등록되었습니다!")
        else:
            st.warning("면적과 가액 정보를 입력해주세요.")

st.divider()

# 3. 매물 관리 목록 (수정 가능 버전)
st.subheader("🔍 매물 관리 목록")
if not st.session_state.df_list.empty:
    edited_df = st.data_editor(
        st.session_state.df_list,
        use_container_width=True,
        hide_index=True,
        column_config={
            "상태": st.column_config.SelectboxColumn("상태", options=["진행중", "완료", "보류", "삭제"], required=True),
            "가액": st.column_config.NumberColumn("가액(만원)", format="%d 만원"),
        },
        disabled=["접수일", "대분류", "소분류", "가액", "면적"]
    )
    
    if st.button("💾 상태 변경 사항 저장"):
        st.session_state.df_list = edited_df
        st.toast("상태 정보가 업데이트되었습니다!")
else:
    st.info("등록된 매물이 없습니다. 위에서 새 매물을 등록해 주세요.")
