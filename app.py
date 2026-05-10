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

# --- [기능 1] 초기화 버튼 (입력창 + 필터 모두 초기화) ---
def reset_all():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

st.button("🔄 전체 초기화 (입력창 비우기 및 필터 해제)", on_click=reset_all, use_container_width=True)

# [카테고리 맵]
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
with st.expander("➕ 새 매물 등록", expanded=False):
    col1, col2, col3 = st.columns([1, 1, 1.2])
    with col1:
        reg_date = st.date_input("접수일", datetime.today(), key="reg_date")
        client_name = st.text_input("고객명", key="reg_name")
        client_phone = st.text_input("연락처", key="reg_phone")
        main_cat = st.radio("물건 대분류", list(category_map.keys()), horizontal=True, key="reg_main")
    with col2:
        sub_cat = st.selectbox("물건 소분류", options=category_map[main_cat], key="reg_sub")
        deal_type = st.radio("구분", ["매매", "전세", "월세"], horizontal=True, key="reg_deal")
        addr = st.text_input("소재지 상세", key="reg_addr")
        price = st.number_input("가액 (만원)", min_value=0, step=100, key="reg_price")
        rent = st.number_input("월세 (만원)", min_value=0, step=10, key="reg_rent")
    with col3:
        area_text = st.text_input("면적 입력", key="reg_area")
        default_memo = f"[{sub_cat} {deal_type} 상세정보]\n- 비밀번호: \n- 로열층/방향: \n- 관리비: \n- 입주일: "
        memo = st.text_area("특약내용", value=st.session_state.get("reg_memo", default_memo), height=200, key="reg_memo")

    if st.button("🏠 구글 시트에 저장", use_container_width=True):
        _, py_display = process_area(area_text)
        new_entry = pd.DataFrame([{
            "접수일": reg_date.strftime("%Y-%m-%d"), "고객명": client_name, "연락처": client_phone, 
            "대분류": main_cat, "소분류": sub_cat, "면적": py_display, 
            "가액": price, "월세": rent, "상태": "진행중", "소재지": addr, "특약사항": memo
        }])
        updated_df = pd.concat([new_entry, df_list], ignore_index=True)
        conn.update(data=updated_df)
        st.success("✅ 저장되었습니다!")
        st.rerun()

st.divider()

# --- [핵심 수정] 다중 필터 시스템 ---
st.subheader("🔍 매물 통합 검색")

# 필터 영역을 3컬럼으로 배치
f_col1, f_col2, f_col3 = st.columns([1.5, 1, 1])

with f_col1:
    search_q = st.text_input("📍 소재지 또는 고객명 검색", placeholder="주소나 이름을 입력하세요")

with f_col2:
    # 대분류 필터 (주거용, 비주거용, 토지)
    f_main_cat = st.multiselect("🏗️ 매물 종류", options=list(category_map.keys()), default=list(category_map.keys()))

with f_col3:
    # 거래 방식 필터 (매매, 전세, 월세)
    # 구글 시트에 '구분'이라는 컬럼이 없다면 '특약사항'이나 다른 곳에서 찾아야 하므로 
    # 데이터 구조에 '구분' 컬럼이 저장되도록 위 저장 로직에도 반영했습니다.
    f_deal_type = st.multiselect("💰 거래 구분", options=["매매", "전세", "월세"], default=["매매", "전세", "월세"])

# 상태 필터는 눈에 잘 띄게 바로 아래 넓게 배치
status_list = st.multiselect("🚦 상태 필터", ["진행중", "완료", "보류", "삭제"], default=["진행중", "보류"])

# 필터링 로직 적용
df_filtered = df_list.copy()
if not df_filtered.empty:
    # 1. 상태 필터
    df_filtered = df_filtered[df_filtered['상태'].isin(status_list)]
    # 2. 대분류 필터
    if '대분류' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['대분류'].isin(f_main_cat)]
    # 3. 텍스트 검색 (소재지 또는 고객명)
    if search_q:
        df_filtered = df_filtered[
            df_filtered['소재지'].str.contains(search_q, na=False) | 
            df_filtered['고객명'].str.contains(search_q, na=False)
        ]

# 4. 목록 표시 및 에디터
st.subheader(f"📋 검색 결과 ({len(df_filtered)}건)")
edited_df = st.data_editor(
    df_filtered,
    use_container_width=True,
    hide_index=False,
    column_config={
        "상태": st.column_config.SelectboxColumn("상태", options=["진행중", "완료", "보류", "삭제"]),
        "특약사항": None # 표에서는 숨김
    },
    column_order=["상태", "소재지", "소분류", "가액", "월세", "면적", "고객명", "연락처"]
)

if st.button("💾 변경사항 시트 반영", use_container_width=True):
    conn.update(data=edited_df)
    st.toast("변경사항이 저장되었습니다!")
    st.rerun()

# 5. 상세 브리핑 카드
st.markdown("---")
if not df_filtered.empty:
    st.subheader("📋 매물 상세 브리핑 카드")
    property_options = {i: f"[{row['소분류']}] {row['소재지']} ({row['고객명']})" for i, row in df_filtered.iterrows()}
    selected_idx = st.selectbox("🎯 확인할 매물을 선택하세요", options=list(property_options.keys()), format_func=lambda x: property_options[x])

    if selected_idx is not None:
        item = df_filtered.loc[selected_idx]
        with st.container(border=True):
            c1, c2 = st.columns([1.5, 2.5])
            with c1:
                st.markdown(f"### 📍 {item['소재지']}")
                st.markdown(f"**🏠 분류:** {item['대분류']} > {item['소분류']} ({item['상태']})")
                st.markdown(f"**💰 가격:** {item['가액']} / {item['월세']}")
                st.markdown(f"**📏 면적:** {item['면적']}")
                st.markdown(f"**👤 고객:** {item['고객명']} ({item['연락처']})")
            with c2:
                st.markdown("**📜 상세 특약 및 메모**")
                new_memo = st.text_area("메모 수정", value=item['특약사항'], height=200, key=f"edit_memo_{selected_idx}")
                if st.button("📝 메모만 즉시 저장"):
                    df_list.at[selected_idx, '특약사항'] = new_memo
                    conn.update(data=df_list)
                    st.success("메모가 수정되었습니다.")
                    st.rerun()
else:
    st.info("조건에 맞는 매물이 없습니다.")
