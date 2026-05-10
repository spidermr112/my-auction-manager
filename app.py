import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import re

# 1. 페이지 설정
st.set_page_config(page_title="파크부동산", page_icon="🏘️", layout="wide")
st.title("🏘️ 부동산 매물 등록 시스템 (클라우드 연동)")

# --- [연결] 구글 스프레드시트 연결 ---
# Streamlit Secrets에 저장된 정보를 자동으로 읽어오도록 설정합니다.
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    """구글 시트에서 데이터를 불러오고 형식을 정제합니다."""
    try:
        # 캐시 없이 실시간 데이터를 가져옵니다.
        data = conn.read(ttl=0)
        
        # 데이터 정제: 빈 행 삭제 및 빈 칸 처리
        data = data.dropna(how='all')
        data = data.fillna("")
        
        # 숫자 컬럼 강제 변환 (가액, 월세) - 오류 방지 핵심
        num_cols = ["가액", "월세"]
        for col in num_cols:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0).astype(int)
        
        return data
    except Exception as e:
        # 시트 연결 실패 시 기본 빈 데이터프레임 반환
        return pd.DataFrame(columns=["접수일", "고객명", "연락처", "대분류", "소분류", "면적", "가액", "월세", "상태", "소재지", "특약사항"])

# 데이터 로드
df_list = load_data()

# --- [함수] 비즈니스 로직 ---
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

    if st.button("🏠 구글 시트에 저장", use_container_width=True):
        new_entry = pd.DataFrame([{
            "접수일": reg_date.strftime("%Y-%m-%d"), 
            "고객명": client_name, "연락처": client_phone, 
            "대분류": main_cat, "소분류": sub_cat, "면적": py_display, 
            "가액": price, "월세": rent, "상태": "진행중", 
            "소재지": addr, "특약사항": memo
        }])
        
        # 새 데이터와 기존 데이터 합치기
        updated_df = pd.concat([new_entry, df_list], ignore_index=True)
        # 구글 시트에 쓰기 작업 실행
        conn.update(data=updated_df)
        st.success("구글 시트에 안전하게 저장되었습니다!")
        st.rerun()

st.divider()

# 3. 매물 필터링 및 목록 출력
with st.expander("🔍 매물 필터링 / 검색", expanded=False):
    f_col1, f_col2, f_col3 = st.columns([1, 1, 1])
    with f_col1: status_list = st.multiselect("상태 선택", ["진행중", "완료", "보류", "삭제"], default=["진행중", "보류"])
    with f_col2: filter_cat = st.multiselect("대분류 선택", list(category_map.keys()), default=list(category_map.keys()))
    with f_col3: search_q = st.text_input("소재지 검색")

# 필터링 로직
df_filtered = df_list.copy()
if not df_filtered.empty:
    if '상태' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['상태'].isin(status_list)]
    if '대분류' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['대분류'].isin(filter_cat)]
    if search_q and '소재지' in df_filtered.columns: 
        df_filtered = df_filtered[df_filtered['소재지'].str.contains(search_q, na=False)]

st.subheader(f"📋 매물 목록 (조회: {len(df_filtered)}건)")

if not df_filtered.empty:
    select_options = {i: f"{row['소재지']} ({row['고객명']})" for i, row in df_filtered.iterrows()}
    target_idx = st.selectbox("🎯 상세 정보를 보려면 매물을 선택하세요", 
                             options=list(select_options.keys()), 
                             format_func=lambda x: select_options[x])

    # 데이터 수정 표
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
        st.toast("변경사항이 클라우드에 반영되었습니다.")
        st.rerun()

    # 4. 하단 상세 정보창
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
                st.success("특약사항이 클라우드에 저장되었습니다.")
                st.rerun()
else:
    st.info("조회된 매물이 없습니다. 매물을 먼저 등록해 주세요.")
