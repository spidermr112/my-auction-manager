# (상단 생략... 5번 상세 브리핑 부분만 수정하세요)

if not df_filtered.empty:
    st.markdown("---")
    st.subheader("📋 매물 상세 브리핑")

    if "current_idx" not in st.session_state:
        st.session_state.current_idx = 0

    filtered_indices = df_filtered.index.tolist()
    total_count = len(filtered_indices)
    
    if st.session_state.current_idx >= total_count:
        st.session_state.current_idx = 0

    # --- [핵심 수정] 칸을 5개로 쪼개서 버튼 크기를 줄이고 강제로 좌우 배치 ---
    # b1(이전), empty1(공백), count(숫자), empty2(공백), b2(다음)
    b_col1, b_col2, b_col3, b_col4, b_col5 = st.columns([1, 0.5, 2, 0.5, 1])
    
    with b_col1:
        if st.button("◀️", use_container_width=True, key="prev_btn"):
            st.session_state.current_idx = (st.session_state.current_idx - 1) % total_count
            st.rerun()

    with b_col3:
        # 숫자를 더 작고 깔끔하게 표시
        st.markdown(f"<p style='text-align: center; font-size: 20px; font-weight: bold; margin: 0;'>{st.session_state.current_idx + 1} / {total_count}</p>", unsafe_allow_html=True)

    with b_col5:
        if st.button("▶️", use_container_width=True, key="next_btn"):
            st.session_state.current_idx = (st.session_state.current_idx + 1) % total_count
            st.rerun()

    # 데이터 로드
    item = df_filtered.loc[filtered_indices[st.session_state.current_idx]]
    
    # [이하 매물 상세 정보 카드 부분은 동일]
    with st.container(border=True):
        st.info(f"📍 **{item['소재지']}**")
        # ... (이전 코드와 동일하게 유지)
