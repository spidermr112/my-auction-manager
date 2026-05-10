import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import re

# 1. 페이지 설정
st.set_page_config(page_title="페이지부동산", page_icon="📄", layout="wide")
st.title("📄 페이지부동산 매물 관리 시스템")

# --- [연결] 구글 스프레드시트 연결 ---
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

def process_area(input_str):
    if not input_str or input_str.strip() == "": return 0, "-" 
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", input_str)
    if not nums: return 0, "-"
    val = float(nums[0])
    p = int(val) if "평" in input_str else int(round(val * 0.3025))
    return p, f"{p}평"

# 카테고리 맵
category_map = {
    "주거용": ["아파트", "연립/다세대", "단독/다가구", "전원주택", "오피스텔(주거)"], 
    "비주거용": ["상가", "사무실", "공장", "창고", "빌딩/건물", "지식산업센터", "숙박시설"], 
    "토지": ["대지", "전/답/과수원", "임야", "잡종지", "기타토지"]
}

# 2. 매물 등록하기 (st.form을 제거하여 실시간 연동 구현)
with st.expander("➕ 새 매물 등록", expanded=True):
    col1, col2, col3 = st.columns([1, 1, 1.2])
    
    with col1:
        reg_date = st.date_input("접수일", datetime.today())
        # key를 부여하여 나중에 수동으로 비울 수 있게 합니다.
        client_name = st.text_input("고객명", key="in_name")
        client_phone = st.text_input("연락처", key="in_phone")
        # [실시간 연동] 라디오 버튼 클릭 시 즉시 스크립트가 재실행됩니다.
        main_cat = st.radio("물건 대분류", list(category_map.keys()), horizontal=True, key="in_main")
        
    with col2:
        # [실시간 연동] 위에서 선택한 main_cat에 따라 options가 즉시 바뀝니다.
        sub_cat = st.selectbox("물건 소분류", options=category_map[main_cat], key="in_sub")
        deal_type = st.radio("구분", ["매매", "전세", "월세"], horizontal=True, key="in_deal")
        addr = st.text_input("소재지 상세", key="in_addr")
        price = st.number_input("가액 (만원)", min_value=0, step=100, key="in_price")
        rent = st.number_input("월세 (만원)", min_value=0, step=10, key="in_rent")
        
    with col3:
        area_text = st.text_input("면적 입력", key="in_area")
        # 소분류가 바뀔 때마다 템플릿 문구도 자동으로 변경됩니다.
        dynamic_tmpl = f"[{sub_cat} {deal_type} 상세정보]\n- 비밀번호: \n- 로열층/방향: \n- 관리비: \n- 입주일: "
        memo = st.text_area("특약내용 및 상세설명", value=dynamic_tmpl, height=200, key="in_memo")

    # 저장 버튼 (st.form 외부이므로 일반 st.button 사용)
    if st.button("🏠 구글 시트에 저장", use_container_width=True):
        _, py_display = process_area(area_text)
        
        new_entry = pd.DataFrame([{
            "접수일": reg_date.strftime("%Y-%m-%d"), 
            "고객명": client_name, "연락처": client_phone, 
            "대분류": main_cat, "소분류": sub_cat, "면적": py_display, 
            "가액": price, "월세": rent, "상태": "진행중", 
            "소재지": addr, "특약사항": memo
        }])
        
        # 구글 시트 업데이트
        updated_df = pd.concat([new_entry, df_list], ignore_index=True)
        conn.update(data=updated_df)
        
        # [중요] 저장 후 모든 입력창 초기화 로직
        for key in ["in_name", "in_phone", "in_addr", "in_area", "in_price", "in_rent", "in_memo"]:
            if key in st.session_state:
                st.session_state[key] = "" if "price" not in key and "rent" not in key else 0
        
        st.success("✅ 저장이 완료되었습니다!")
        st.rerun() # 전체 화면을 새로고침하여 초기 상태로 복구

st.divider()

# 3. 매물 목록 및 수정 섹션 (기존 코드와 동일)
with st.expander("🔍 매물 검색 및 필터", expanded=False):
    f_col1, f_col2, f_col3 = st.columns([1, 1, 1])
    with f_col1: status_list = st.multiselect("상태", ["진행중", "완료", "보류", "삭제"], default=["진행중", "보류"])
    with f_col2: filter_cat = st.multiselect("대분류", list(category_map.keys()), default=list(category_map.keys()))
    with f_col3: search_q = st.text_input("소재지 검색")

df_filtered = df_list.copy()
if not df_filtered.empty:
    if '상태' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['상태'].isin(status_list)]
    if '대분류' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['대분류'].isin(filter_cat)]
    if search_q and '소재지' in df_filtered.columns: 
        df_filtered = df_filtered[df_filtered['소재지'].str.contains(search_q, na=False)]

st.subheader(f"📋 매물 목록 (총 {len(df_filtered)}건)")

if not df_filtered.empty:
    edited_df = st.data_editor(
        df_filtered,
        use_container_width=True,
        hide_index=True,
        column_config={
            "상태": st.column_config.SelectboxColumn("상태", options=["진행중", "완료", "보류", "삭제"]),
            "소재지": st.column_config.TextColumn("📍 소재지 상세", width="large"),
        },
        column_order=["상태", "소재지", "소분류", "가액", "월세", "면적", "고객명", "연락처"]
    )

    if st.button("💾 변경 사항 구글 시트 반영", use_container_width=True):
        conn.update(data=edited_df)
        st.toast("변경사항이 반영되었습니다.")
        st.rerun()
else:
    st.info("조회된 매물이 없습니다.")
