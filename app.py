import streamlit as st
import pandas as pd
from datetime import datetime
import re

# 1. 페이지 설정
st.set_page_config(page_title="파크부동산", page_icon="🏘️", layout="wide")
st.title("🏘️ 파크부동산 매물 등록 시스템")

# --- [기존 데이터 정의 및 템플릿 함수 생략] ---
def get_dynamic_template(sub_cat, deal_type):
    check_items = ["현 시설 상태", "입주시기 협의"]
    residential_cats = ["아파트", "연립/다세대", "단독/다가구", "전원주택", "오피스텔(주거)"]
    commercial_building_cats = ["상가/사무실", "빌딩/건물", "공장/창고", "지식산업센터", "숙박시설"]
    if sub_cat in residential_cats:
        check_items += ["장기수선충당금", "발코니 확장", "수리 여부"]
        if deal_type == "매매": check_items += ["융자 상환/말소", "가구 포함 여부"]
        else: check_items += ["수도/난방 점검", "반려동물 여부"]
    elif sub_cat in commercial_building_cats:
        check_items += ["부가세 별도", "권리금 확인", "원상복구", "렌트프리"]
    
    tmpl = f"[{sub_cat} {deal_type} 상세]\n- 비밀번호: \n- 로열층/방향: \n- 관리비: \n- 입주일: "
    return check_items, tmpl

# --- [세션 상태 초기화] ---
if 'df_list' not in st.session_state:
    st.session_state.df_list = pd.DataFrame(columns=["접수일", "고객명", "연락처", "대분류", "소분류", "면적", "가액", "월세", "상태", "소재지", "특약사항"])

# --- [기존 매물 등록 섹션 생략] ---
with st.expander("➕ 매물 등록하기", expanded=False):
    # 등록 관련 코드는 기존과 동일하게 유지...
    pass

st.divider()

# --- [2. 매물 목록 관리 및 클릭 연동] ---
if not st.session_state.df_list.empty:
    # 필터링 로직 (기존 유지)
    df_filtered = st.session_state.df_list.copy()
    
    st.subheader(f"📋 매물 목록 (조회: {len(df_filtered)}건)")
    st.caption("💡 표 아래의 [매물 선택]에서 번호를 고르면 상세 특약이 자동으로 표시됩니다.")

    # [수정포인트] 기존 data_editor를 그대로 두어 편집 기능 유지
    edited_df = st.data_editor(
        df_filtered,
        use_container_width=True,
        hide_index=False, # 인덱스 번호를 보여주어 선택을 돕게 함
        column_config={
            "상태": st.column_config.SelectboxColumn("상태", options=["진행중", "완료", "보류", "삭제"]),
            "소재지": st.column_config.TextColumn("📍 소재지 상세", width="large"),
            "특약사항": None # 표에서는 숨김
        },
        column_order=["상태", "소재지", "소분류", "가액", "월세", "면적", "고객명", "연락처"]
    )

    if st.button("💾 목록 변경 사항 저장"):
        st.session_state.df_list.update(edited_df)
        st.toast("저장되었습니다!")

    # --- [핵심 기능: 셀 클릭 대신 안전한 행 선택 방식] ---
    # 표 바로 아래에 선택 박스를 두어 하단 상세창과 연결합니다.
    options = {i: f"{row['소재지']} ({row['고객명']})" for i, row in df_filtered.iterrows()}
    selected_idx = st.selectbox("📖 상세 내용을 확인할 매물을 선택하세요 (목록의 왼쪽 번호 참고)", 
                               options.keys(), 
                               format_func=lambda x: options[x])

    # --- [3. 하단 상세 특약 확인 창] ---
    st.markdown("---")
    st.markdown("### 🔍 선택 매물 상세 특약 확인")
    
    # 선택된 인덱스의 데이터를 가져옴
    item = st.session_state.df_list.loc[selected_idx]
    
    with st.container(border=True):
        c1, c2 = st.columns([1, 2])
        with c1:
            st.info(f"📍 **{item['소재지']}**")
            st.write(f"🏷️ **분류:** {item['소분류']} ({item['상태']})")
            st.write(f"👤 **의뢰인:** {item['고객명']} / {item['연락처']}")
            st.success(f"💰 **금액:** {item['가액']} / {item['월세']}")
        with c2:
            st.markdown("**📜 상세 특약 및 메모**")
            # 선택된 행의 특약사항이 자동으로 텍스트 영역에 표시됨
            st.text_area("상세내용", value=item.get('특약사항', ""), height=300, label_visibility="collapsed", key=f"view_{selected_idx}")
else:
    st.info("등록된 매물이 없습니다.")
