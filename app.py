import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import re

# 1. 페이지 설정 (브라우저 탭 이름과 아이콘 변경)
st.set_page_config(page_title="페이지부동산", page_icon="📄", layout="wide")

# 메인 타이틀 (수산리 전문성 강조)
st.title("📄 페이지부동산 : 수산리 전원주택·토지·경매")
st.markdown("> **인생의 새로운 페이지를 함께 그려가는 수산리 전문 파트너**")

# --- [연결] 구글 스프레드시트 연결 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    """구글 시트에서 데이터를 불러오고 형식을 정제합니다."""
    try:
        data = conn.read(ttl=0)
        data = data.dropna(how='all')
        data = data.fillna("")
        
        # 숫자 컬럼 강제 변환 (가액, 월세)
        num_cols = ["가액", "월세"]
        for col in num_cols:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0).astype(int)
        
        return data
    except Exception as e:
        return pd.DataFrame(columns=["접수일", "고객명", "연락처", "대분류", "소분류", "면적", "가액", "월세", "상태", "소재지", "특약사항"])

# 데이터 로드
df_list = load_data()

# --- [함수] 비즈니스 로직 ---
def get_dynamic_template(sub_cat, deal_type):
    tmpl = f"[{sub_cat} {deal_type} 상세]\n- 비밀번호: \n- 로열층/방향: \n- 관리비: \n- 입주일: \n- 경매사건번호(해당시): "
    return tmpl

def process_area(input_str):
    if not input_str or input_str.strip() == "": return 0, "-" 
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", input_str)
    if not nums: return 0, "-"
    val = float(nums[0])
    p = int(val) if "평" in input_str else int(round(val * 0.3025))
    return p, f"{p}평"

# 수산리 특성에 맞춘 카테고리 구성
category_map = {
    "토지/전원": ["전원주택", "대지", "전/답/과수원", "임야", "기타토지"],
    "수익/상가": ["상가/사무실", "빌딩/건물", "공장/창고", "오피스텔"],
    "경매물건": ["주거용경매", "토지경매", "상업용경매", "공장경매"]
}

# 2. 매물 등록하기
with st.expander("➕ 새 매물 페이지 등록", expanded=False):
    col1, col2, col3 = st.columns([1, 1, 1.2])
    with col1:
        reg_date = st.date_input("접수일", datetime.today())
        client_name = st.text_input("고객명(소유주)", key="reg_name")
        client_phone = st.text_input("연락처", key="reg_phone")
        main_cat = st.radio("물건 성격", list(category_map.keys()), horizontal=True)
    with col2:
        sub_cat = st.selectbox("세부 분류", category_map[main_cat])
        deal_type = st.radio("거래 형식", ["매매", "전세", "월세"], horizontal=True)
        addr = st.text_input("수산리 상세 소재지", key="reg_addr")
        price = st.number_input("가액 (만원)", step=0)
        rent = st.number_input("월세 (만원)", step=0) if deal_type == "월세" else 0
    with col3:
        area_text = st.text_input("면적(평수/㎡)", key="reg_area")
        _, py_display = process_area(area_text)
        dynamic_tmpl = get_dynamic_template(sub_cat, deal_type)
        memo = st.text_area("매물 상세 기록 (특약/분석)", value=dynamic_tmpl, height=200)

    if st.button("🏠 페이지 저장하기", use_container_width=True):
        new_entry = pd.DataFrame([{
            "접수일": reg_date.strftime("%Y-%m-%d"), 
            "고객명": client_name, "연락처": client_phone, 
            "대분류": main_cat, "소분류": sub_cat, "면적": py_display, 
            "가액": price, "월세": rent, "상태": "진행중", 
            "소재지": addr, "특약사항": memo
        }])
        
        updated_df = pd.concat([new_entry, df_list], ignore_index=True)
        conn.update(data=updated_df)
        st.success("새로운 매물 페이지가 저장되었습니다!")
        st.rerun()

st.divider()

# 3. 매물 목록 및 필터링
with st.expander("🔍 매물 페이지 검색", expanded=False):
    f_col1, f_col2, f_col3 = st.columns([1, 1, 1])
    with f_col1: status_list = st.multiselect("진행 상태", ["진행중", "완료", "보류", "삭제"], default=["진행중", "보류"])
    with f_col2: filter_cat = st.multiselect("카테고리", list(category_map.keys()), default=list(category_map.keys()))
    with f_col3: search_q = st.text_input("소재지 또는 키워드 검색")

df_filtered = df_list.copy()
if not df_filtered.empty:
    if '상태' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['상태'].isin(status_list)]
    if '대분류' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['대분류'].isin(filter_cat)]
    if search_q and '소재지' in df_filtered.columns: 
        df_filtered = df_filtered[df_filtered['소재지'].str.contains(search_q, na=False)]

st.subheader(f"📋 관리 중인 매물 (총 {len(df_filtered)}건)")

if not df_filtered.empty:
    select_options = {i: f"{row['소재지']} ({row['고객명']})" for i, row in df_filtered.iterrows()}
    target_idx = st.selectbox("🎯 상세 페이지 열기", 
                             options=list(select_options.keys()), 
                             format_func=lambda x: select_options[x])

    edited_df = st.data_editor(
        df_filtered,
        use_container_width=True,
        hide_index=True,
        column_config={
            "상태": st.column_config.SelectboxColumn("상태", options=["진행중", "완료", "보류", "삭제"]),
            "소재지": st.column_config.TextColumn("📍 소재지", width="large"),
            "특약사항": None
        },
        column_order=["상태", "소재지", "소분류", "가액", "월세", "면적", "고객명", "연락처"]
    )

    if st.button("💾 변경된 내용 클라우드 반영", use_container_width=True):
        df_list.update(edited_df)
        conn.update(data=df_list)
        st.toast("페이지가 성공적으로 업데이트되었습니다.")
        st.rerun()

    # 4. 상세 페이지 뷰
    st.markdown("---")
    item = df_filtered.loc[target_idx]
    st.markdown(f"### 🔍 [{item['소재지']}] 상세 페이지")
    
    with st.container(border=True):
        c1, c2 = st.columns([1, 2])
        with c1:
            st.info(f"📍 **{item['소재지']}**")
            st.write(f"🏷️ **분류:** {item['소분류']} ({item['상태']})")
            st.write(f"📞 **고객:** {item['고객명']} / {item['연락처']}")
            st.success(f"💰 **가액:** {item['가액']} / {item['월세']}")
        with c2:
            st.markdown("**📜 매물 상세 분석 및 특약**")
            updated_memo = st.text_area("기록 수정", value=item.get('특약사항', ""), height=300, key=f"memo_{target_idx}")
            if st.button("📝 기록 수정 저장"):
                df_list.at[target_idx, '특약사항'] = updated_memo
                conn.update(data=df_list)
                st.success("상세 기록이 저장되었습니다.")
                st.rerun()
else:
    st.info("아직 등록된 매물 페이지가 없습니다.")
