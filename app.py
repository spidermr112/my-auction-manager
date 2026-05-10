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
        # 숫자 컬럼 변환
        num_cols = ["가액", "월세"]
        for col in num_cols:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0).astype(int)
        return data
    except Exception:
        return pd.DataFrame(columns=["접수일", "고객명", "연락처", "대분류", "소분류", "면적", "가액", "월세", "상태", "소재지", "특약사항"])

df_list = load_data()

# --- [기능 1] 최상단 초기화 버튼 ---
def reset_all_fields():
    for key in list(st.session_state.keys()):
        if key.startswith("reg_"):
            del st.session_state[key]
    st.rerun()

st.button("🔄 입력창 전체 초기화 (새 매물 작성)", on_click=reset_all_fields, use_container_width=True)

# [데이터 구조]
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

# 2. 매물 등록하기
with st.expander("➕ 새 매물 등록", expanded=True):
    col1, col2, col3 = st.columns([1, 1, 1.2])
    
    with col1:
        reg_date = st.date_input("접수일", datetime.today(), key="reg_date")
        client_name = st.text_input("고객명", key="reg_name")
        client_phone = st.text_input("연락처", key="reg_phone")
        main_cat = st.radio("물건 대분류", list(category_map.keys()), horizontal=True, key="reg_main")
        
    with col2:
        # 실시간 연동되는 소분류
        sub_cat = st.selectbox("물건 소분류", options=category_map[main_cat], key="reg_sub")
        deal_type = st.radio("구분", ["매매", "전세", "월세"], horizontal=True, key="reg_deal")
        addr = st.text_input("소재지 상세", key="reg_addr")
        price = st.number_input("가액 (만원)", min_value=0, step=100, key="reg_price")
        rent = st.number_input("월세 (만원)", min_value=0, step=10, key="reg_rent")
        
    with col3:
        area_text = st.text_input("면적 입력", key="reg_area")
        # 동적 템플릿
        default_memo = f"[{sub_cat} {deal_type} 상세정보]\n- 비밀번호: \n- 로열층/방향: \n- 관리비: \n- 입주일: "
        # 사용자가 직접 입력한 값이 있으면 그것을 유지하고, 없으면 기본 템플릿 사용
        memo = st.text_area("특약내용 및 상세설명", value=st.session_state.get("reg_memo", default_memo), height=200, key="reg_memo")

    if st.button("🏠 구글 시트에 저장", use_container_width=True):
        _, py_display = process_area(area_text)
        new_entry = pd.DataFrame([{
            "접수일": reg_date.strftime("%Y-%m-%d"), 
            "고객명": client_name, "연락처": client_phone, 
            "대분류": main_cat, "소분류": sub_cat, "면적": py_display, 
            "가액": price, "월세": rent, "상태": "진행중", 
            "소재지": addr, "특약사항": memo
        }])
        updated_df = pd.concat([new_entry, df_list], ignore_index=True)
        conn.update(data=updated_df)
        st.success("✅ 저장이 완료되었습니다!")
        reset_all_fields() # 저장 후 자동 초기화

st.divider()

# 3. 매물 목록 검색 및 필터
st.subheader("🔍 매물 검색 및 관리")
f_col1, f_col2 = st.columns([1, 2])
with f_col1:
    search_q = st.text_input("📍 소재지 또는 고객명 검색")
with f_col2:
    status_list = st.multiselect("상태 필터", ["진행중", "완료", "보류", "삭제"], default=["진행중", "보류"])

df_filtered = df_list.copy()
if not df_filtered.empty:
    df_filtered = df_filtered[df_filtered['상태'].isin(status_list)]
    if search_q:
        df_filtered = df_filtered[
            df_filtered['소재지'].str.contains(search_q, na=False) | 
            df_filtered['고객명'].str.contains(search_q, na=False)
        ]

# 4. 데이터 에디터 (표 형태)
edited_df = st.data_editor(
    df_filtered,
    use_container_width=True,
    hide_index=False,
    column_config={
        "상태": st.column_config.SelectboxColumn("상태", options=["진행중", "완료", "보류", "삭제"]),
        "특약사항": None # 표에서는 숨기고 상세 카드에서 확인
    },
    column_order=["상태", "소재지", "소분류", "가액", "월세", "면적", "고객명", "연락처"]
)

if st.button("💾 목록의 변경사항(상태 등) 시트 반영", use_container_width=True):
    conn.update(data=edited_df)
    st.toast("변경사항이 구글 시트에 저장되었습니다!")
    st.rerun()

# --- [기능 2] 매물 상세 카드 (목록에서 볼 수 없는 숨은 내용 보기) ---
st.markdown("---")
st.subheader("📋 선택 매물 상세 브리핑 카드")

if not df_filtered.empty:
    # 선택 박스 생성
    property_options = {i: f"[{row['소분류']}] {row['소재지']} - {row['고객명']}님" for i, row in df_filtered.iterrows()}
    selected_idx = st.selectbox("🎯 상세 내용을 확인(수정)할 매물을 선택하세요", 
                                options=list(property_options.keys()), 
                                format_func=lambda x: property_options[x])

    if selected_idx is not None:
        item = df_filtered.loc[selected_idx]
        
        # 카드 디자인 섹션
        with st.container(border=True):
            c1, c2 = st.columns([1.5, 2.5])
            with c1:
                st.markdown(f"### 📍 {item['소재지']}")
                st.markdown(f"**🏠 분류:** {item['대분류']} > {item['소분류']} ({item['상태']})")
                st.markdown(f"**💰 가액:** 매매/보증금 {item['가액']} / 월세 {item['월세']}")
                st.markdown(f"**📏 면적:** {item['면적']}")
                st.markdown(f"**👤 고객:** {item['고객명']} ({item['연락처']})")
                st.markdown(f"**📅 접수:** {item['접수일']}")
            
            with c2:
                st.markdown("**📜 특약 및 상세 메모 (편집 가능)**")
                # 상세 카드 내에서 바로 메모 수정 가능하도록 구성
                new_memo = st.text_area("특약사항 수정", value=item['특약사항'], height=250, key=f"card_memo_{selected_idx}")
                if st.button("📝 이 매물의 특약사항만 즉시 업데이트"):
                    df_list.at[selected_idx, '특약사항'] = new_memo
                    conn.update(data=df_list)
                    st.success("해당 매물의 상세 정보가 수정되었습니다.")
                    st.rerun()
else:
    st.info("검색 결과가 없습니다.")
