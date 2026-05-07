# 2. 매물 등록하기 섹션
with st.expander("➕ 매물 등록하기", expanded=False):
    col1, col2, col3 = st.columns(3)
    with col1:
        reg_date = st.date_input("접수일", datetime.today())
        main_cat = st.radio("물건 대분류", list(category_map.keys()), horizontal=True, index=2)
    
    with col2:
        sub_cat = st.selectbox("물건 소분류", category_map[main_cat])
        # 'gubun' 변수를 사용하여 매매 여부를 판단합니다.
        gubun = st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        addr = st.text_input("소재지 상세", key="addr_input")
        
        # --- [로직 핵심: 대분류 상관없이 '매매'라면 3단 연동 로직 활성화] ---
        if gubun == "매매":
            st.number_input("평단가 (만원)", key="py_price", step=0, format="%d", on_change=calc_values)
            st.number_input("거래가액 (만원)", key="land_price", step=0, format="%d", on_change=calc_values)
        else:
            # 매매가 아닐 경우(전세/월세)에는 평단가 없이 가액(보증금 등)만 입력받습니다.
            st.number_input("거래가액 (만원)", key="land_price", step=0, format="%d")
            
    with col3:
        area_text = st.text_input("면적 입력", placeholder="예: 100평 또는 330", key="area_input", on_change=calc_values)
        py_num, py_display = process_area(area_text)
        if area_text: 
            st.info(f"💾 계산 기준 면적: {py_display}")
        st.text_area("특약내용", height=110, key="memo_input")

    # [저장 버튼 로직]
    if st.button("🏠 데이터베이스 저장", use_container_width=True):
        new_data = {
            "접수일": reg_date.strftime("%Y-%m-%d"),
            "대분류": main_cat, 
            "소분류": sub_cat,
            "구분": gubun, # 구분을 데이터에 추가하면 나중에 필터링하기 더 좋습니다.
            "가액": st.session_state.get('land_price', 0), 
            "면적": py_display,
            "상태": "진행중", 
            "소재지": addr
        }
        st.session_state.df_list = pd.concat([st.session_state.df_list, pd.DataFrame([new_data])], ignore_index=True)
        save_data(st.session_state.df_list) # 이전에 만든 파일 저장 함수 실행
        st.success("매물이 등록되었습니다!")
