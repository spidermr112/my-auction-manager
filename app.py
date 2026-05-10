import streamlit as st
import pandas as pd
from datetime import datetime
import re
import json
import os

# --- [설정] 데이터 저장 파일 경로 ---
DB_FILE = "property_data.json"

# --- [함수] 데이터 로드 및 저장 로직 ---
def load_data():
    """JSON 파일을 읽어서 데이터프레임으로 변환합니다."""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return pd.DataFrame(data)
        except Exception:
            # 파일이 손상되었거나 비어있을 경우 빈 구조 반환
            return pd.DataFrame(columns=["접수일", "고객명", "연락처", "대분류", "소분류", "면적", "가액", "월세", "상태", "소재지", "특약사항"])
    return pd.DataFrame(columns=["접수일", "고객명", "연락처", "대분류", "소분류", "면적", "가액", "월세", "상태", "소재지", "특약사항"])

def save_data(df):
    """데이터프레임을 JSON 파일로 물리 저장합니다."""
    # datetime 객체 등이 있을 수 있으므로 처리 후 저장
    data = df.to_dict(orient='records')
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 1. 페이지 설정
st.set_page_config(page_title="파크부동산", page_icon="🏘️", layout="wide")
st.title("🏘️ 부동산 매물 등록 시스템")

# --- 세션 상태 초기화 (앱 시작 시 JSON에서 데이터 로드) ---
if 'df_list' not in st.session_state:
    st.session_state.df_list = load_data()

# --- 비즈니스 로직 함수 ---
def get_dynamic_template(sub_cat, deal_type):
    tmpl = f"[{sub_cat} {deal_type} 상세]\n- 비밀번호: \n- 로열층/방향: \n- 관리비: \n- 입주일: "
    return tmpl

def process_area(input_str):
    if not input_str or input_str.strip() == "": return 0, "-" 
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", input_str)
    if not nums: return 0, "-"
    val = float(nums[0])
    p = int(val) if "평" in input_str else int(round(val * 0.3025))
    return p, f"{p}평"

category_map = {
    "주거용": ["아파트", "연립/다세대", "단독/다가구", "전원주택", "오피스텔(주거)"], 
    "비주거용": ["상가/사무실", "빌딩/건물", "공장/창고", "지식산업센터", "숙박시설"], 
    "토지": ["대지", "전/답/과수원", "임야", "잡종지", "기타토지", "복수토지"]
}

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
        dynamic_tmpl = get_dynamic_template(sub_cat, deal_type)
        memo = st.text_area("특약내용", value=dynamic_tmpl, height=200)

    if st.button("🏠 데이터베이스 저장", use_container_width=True):
        new_entry = {
            "접수일": reg_date.strftime("%Y-%m-%d"), 
            "고객명": client_name, 
            "연락처": client_phone, 
            "대분류": main_cat, 
            "소분류": sub_cat, 
            "면적": py_display, 
            "가액": price, 
            "월세": rent, 
            "상태": "진행중", 
            "소재지": addr, 
            "특약사항": memo
        }
        new_row = pd.DataFrame([new_entry])
        # 세션 상태 업데이트 및 파일 저장
        st.session_state.df_list = pd.concat([new_row, st.session_state.df_list], ignore_index=True)
        save_data(st.session_state.df_list)
        st.success("매물이 성공적으로 저장되었습니다.")
        st.rerun()

st.divider()

# 3. 매물 필터링
with st.expander("🔍 매물 필터링 / 검색", expanded=False):
    f_col1, f_col2, f_col3 = st.columns([1, 1, 1])
    with f_col1: status_list = st.multiselect("상태 선택", ["진행중", "완료", "보류", "삭제"], default=["진행중", "보류"])
    with f_col2: filter_cat = st.multiselect("대분류 선택", list(category_map.keys()), default=list(category_map.keys()))
    with f_col3: search_q = st.text_input("소재지 검색")

# 필터링 적용된 데이터프레임 생성
df_display = st.session_state.df_list.copy()
if not df_display.empty:
    df_display = df_display[df_display['상태'].isin(status_list)]
    df_display = df_display[df_display['대분류'].isin(filter_cat)]
    if search_q: 
        df_display = df_display[df_display['소재지'].str.contains(search_q, na=False)]

st.subheader(f"📋 매물 목록 (조회: {len(df_display)}건)")

if not df_display.empty:
    # 매물 선택 드롭다운
    select_options = {i: f"{row['소재지']} ({row['고객명']})" for i, row in df_display.iterrows()}
    target_idx = st.selectbox("🎯 상세 정보를 보려면 매물을 선택하세요", 
                             options=list(select_options.keys()), 
                             format_func=lambda x: select_options[x])

    # 데이터 에디터 (목록 수정용)
    edited_df = st.data_editor(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "상태": st.column_config.SelectboxColumn("상태", options=["진행중", "완료", "보류", "삭제"]),
            "소재지": st.column_config.TextColumn("📍 소재지 상세", width="large"),
            "특약사항": None # 목록에서는 숨김
        },
        column_order=["상태", "소재지", "소분류", "가액", "월세", "면적", "고객명", "연락처"]
    )

    if st.button("💾 목록 변경 사항 저장", use_container_width=True):
        # 수정된 행들을 원본 데이터에 반영
        for i, row in edited_df.iterrows():
            st.session_state.df_list.loc[i] = row
        save_data(st.session_state.df_list)
        st.toast("변경사항이 JSON 파일에 저장되었습니다.")
        st.rerun()

    # 4. 하단 상세 정보창
    st.markdown("---")
    item = df_display.loc[target_idx]
    st.markdown(f"### 🔍 [{item['소재지']}] 상세 정보")
    
    with st.container(border=True):
        c1, c2 = st.columns([1, 2])
        with c1:
            st.info(f"📍 **{item['소재지']}**")
            st.write(f"🏷️ **분류:** {item['소분류']} ({item['상태']})")
            st.write(f"📞 **고객:** {item['고객명']} / {item['연락처']}")
            st.success(f"💰 **가액:** {item['가액']} / {item['월세']}")
        with c2:
            st.markdown("**📜 상세 특약 및 메모**")
            # 상세 내용 수정 후 저장할 수 있도록 text_area 유지
            updated_memo = st.text_area("내용 수정", value=item.get('특약사항', ""), height=300, label_visibility="collapsed", key=f"memo_{target_idx}")
            if updated_memo != item.get('특약사항'):
                if st.button("📝 특약사항 개별 저장"):
                    st.session_state.df_list.at[target_idx, '특약사항'] = updated_memo
                    save_data(st.session_state.df_list)
                    st.success("특약사항이 수정되었습니다.")
                    st.rerun()
else:
    st.info("조회된 매물이 없습니다.")
