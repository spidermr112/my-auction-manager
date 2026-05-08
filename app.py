import streamlit as st
from datetime import datetime

# 1. 소분류별 체크리스트 항목 정의
CHECKLIST_ITEMS = {
    "연립/다세대": ["결로/곰팡이 없음 확인", "수도/난방 정상 작동", "주차 공간 확인", "불법건축물 해당없음"],
    "아파트": ["장기수선충당금 정산", "관리비 완납 확인", "발코니 확장형", "커뮤니티 시설 안내"],
    "상가/사무실": ["부가세 별도", "권리금 유무 확인", "전기 용량 확인", "원상복구 의무 명시", "렌트프리 기간"],
    "토지": ["진입로 확보", "지상 적치물 제거", "농지취득자격증명 필요", "토지거래허가구역 확인"]
}

# 2. 기본 텍스트 템플릿
TEMPLATES = {
    "연립/다세대": "🏠 [연립/다세대 상세]\n- 비밀번호: \n- 방/욕실 수: ",
    "아파트": "🏢 [아파트 상세]\n- 입주가능일: \n- 수리상태: ",
    "상가/사무실": "🛍️ [상가 상세]\n- 현 업종: \n- 추천 업종: ",
    "토지": "🌳 [토지 상세]\n- 용도지역: \n- 지목: "
}

def app():
    st.set_page_config(layout="wide")
    st.title("🏘️ 파크부동산 매물 등록 시스템")

    with st.expander("➕ 매물 등록하기", expanded=True):
        col1, col2, col3 = st.columns([1, 1, 1.5])
        
        with col1:
            st.date_input("접수일", datetime.now())
            st.radio("의뢰목적", ["매도의뢰", "매수의뢰"], horizontal=True)
            category_main = st.radio("물건 대분류", ["주거용", "비주거용", "토지"], horizontal=True)

        with col2:
            # 대분류에 따른 소분류 설정
            sub_options = ["연립/다세대", "아파트"] if category_main == "주거용" else \
                          (["상가/사무실"] if category_main == "비주거용" else ["토지"])
            
            category_sub = st.selectbox("물건 소분류", sub_options)
            st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
            st.text_input("소재지 상세")
            st.number_input("가액/보증금 (만원)", min_value=0, step=100)

        with col3:
            st.subheader("📝 특약 구성 가이드")
            
            # (1) 체크리스트 표시
            st.caption(f"💡 {category_sub} 필수 체크 항목:")
            selected_checks = []
            items = CHECKLIST_ITEMS.get(category_sub, [])
            
            # 체크박스를 2열로 배치
            check_cols = st.columns(2)
            for i, item in enumerate(items):
                with check_cols[i % 2]:
                    if st.checkbox(item, key=f"chk_{item}"):
                        selected_checks.append(f"✅ {item}")

            # (2) 기본 템플릿 + 체크된 항목 합치기
            base_text = TEMPLATES.get(category_sub, "")
            checklist_text = "\n".join(selected_checks)
            
            # 최종 텍스트 결합
            final_text = f"{base_text}\n\n[체크사항]\n{checklist_text}" if selected_checks else base_text

            # (3) 특약내용 입력창 (동적으로 텍스트가 채워짐)
            special_terms = st.text_area(
                "최종 특약내용", 
                value=final_text,
                height=250
            )

        if st.button("🏠 데이터베이스 저장", use_container_width=True):
            st.success("데이터베이스에 성공적으로 저장되었습니다!")

if __name__ == "__main__":
    app()
