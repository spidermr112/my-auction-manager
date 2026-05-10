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

# 데이터 로드
df_list = load_data()

# --- [핵심] 입력 필드 초기화 함수 ---
def clear_inputs():
    """입력 필드에 연결된 세션 상태를 직접 초기화합니다."""
    # 위젯에 연결된 key들을 초기화 (이 기능은 rerun 없이도 값만 비워줍니다)
    st.session_state["reg_name"] = ""
    st.session_state["reg_phone"] = ""
    st.session_state["reg_addr"] = ""
    st.session_state["reg_area"] = ""
    st.session_state["reg_price"] = 0
    st.session_state["reg_rent"] = 0
    # 메모는 기본 템플릿으로 복구하거나 비웁니다.
    st.session_state["reg_memo"] = ""

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
with st.expander("➕ 새 매물 등록", expanded=False):
    col1, col2, col3 = st.columns([1, 1, 1.2])
    with col1:
        reg_date = st.date_input("접수일", datetime.today())
        # 위젯에 key를 부여하면 st.session_state[key]로 접근 가능합니다.
        client_name = st.text_input("고객명", key="reg_name")
        client_phone = st.text_input("연락처", key="reg_phone")
        main_cat = st.radio("물건 대분류", list(category_map.keys()), horizontal=True)
    with col2:
        sub_cat = st.selectbox("물건 소분류", category_map[main_cat])
        deal_type = st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        addr = st.text_input("소재지 상세", key="reg_addr")
        price = st.number_input("가액 (만원)", step=0, key="reg_price")
        rent = st.number_input("월세 (만원)", step=0, key="reg_rent") if deal_type == "월세" else 0
    with col3:
        area_text = st.text_input("면적 입력", key="reg_area")
        _, py_display = process_area(area_text)
        
        # 특약내용 초기 템플릿 설정 (session_state에 값이 없을 때만)
        if "reg_memo" not in st.session_state or st.session_state["reg_memo"] == "":
            st.session_state["reg_memo"] = f"[{sub_cat} {deal_type} 상세]\n- 비밀번호: \n- 로열층/방향: \n- 관리비: \n- 입주일: "
            
        memo = st.text_area("특약내용", height=200, key="reg_memo")

    # 저장 로직
    if st.button("🏠 구글 시트에 저장", use_container_width=True):
        if client_name and addr:
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
            
            # [수정된 부분] 강제로 모든 값을 비우고 화면을 완전히 새로고침합니다.
            st.success("저장 완료! 입력창을 초기화합니다.")
            
            # 세션 스테이트를 완전히 비우는 방식 (가장 안전)
            for key in ["reg_name", "reg_phone", "reg_addr", "reg_area", "reg_price", "reg_rent", "reg_memo"]:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.rerun() # 앱을 처음부터 다시 실행하여 모든 위젯을 깨끗하게 만듦
        else:
            st.error("고객명과 소재지를 입력해주세요!")

st.divider()

# --- 이하 목록 및 상세정보 코드는 기존과 동일 ---
# (공간 절약을 위해 생략하지만, 실제 파일에는 그대로 유지하시면 됩니다)
with st.expander("🔍 매물 검색 및 필터", expanded=False):
    f_col1, f_col2, f_col3 = st.columns([1, 1, 1])
    with f_col1: status_list = st.multiselect("상태 선택", ["진행중", "완료", "보류", "삭제"], default=["진행중", "보류"])
    with f_col2: filter_cat = st.multiselect("대분류 선택", list(category_map.keys()), default=list(category_map.keys()))
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
    select_options = {i: f"{row['소재지']} ({row['고객명']})" for i, row in df_filtered.iterrows()}
    target_idx = st.selectbox("🎯 상세 정보를 보려면 매물을 선택하세요", 
                             options=list(select_options.keys()), 
                             format_func=lambda x: select_options[x])

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
        df_list.update(edited_df)
        conn.update(data=df_list)
        st.toast("구글 시트 업데이트 완료!")
        st.rerun()

    st.markdown("---")
    item = df_filtered.loc[target_idx]
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
            updated_memo = st.text_area("내용 수정", value=item.get('특약사항', ""), height=300, key=f"memo_{target_idx}")
            if st.button("📝 특약사항만 즉시 저장"):
                df_list.at[target_idx, '특약사항'] = updated_memo
                conn.update(data=df_list)
                st.success("구글 시트에 특약사항이 반영되었습니다.")
                st.rerun()
else:
    st.info("조회된 매물이 없습니다.")
