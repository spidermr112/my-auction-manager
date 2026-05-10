# ... (상단 설정 및 load_data 함수는 이전과 동일) ...

# 앱 시작 시 데이터 불러오기
if 'df_list' not in st.session_state:
    df = load_data()
    # 만약 불러온 데이터가 비어있다면 빈 데이터프레임 구조 강제 생성
    if df is None or df.empty:
        st.session_state.df_list = pd.DataFrame(columns=EXPECTED_COLUMNS)
    else:
        st.session_state.df_list = df

# ... (중간 매물 등록 로직 생략) ...

# 3. 매물 목록 출력 (이 부분이 핵심입니다)
st.subheader(f"📋 매물 목록 (조회: {len(df_filtered)}건)")

if not df_filtered.empty:
    try:
        # 데이터가 있을 때만 상세 선택창과 에디터를 표시
        select_options = df_filtered.index.tolist()
        # NaN 값이 있을 경우를 대비해 fillna("") 처리
        format_func = lambda x: f"{df_filtered.loc[x, '소재지'] if pd.notnull(df_filtered.loc[x, '소재지']) else '주소없음'} ({df_filtered.loc[x, '고객명'] if pd.notnull(df_filtered.loc[x, '고객명']) else '무명'})"
        
        target_idx = st.selectbox("🎯 상세 정보를 보려면 매물을 선택하세요", 
                                 options=select_options, 
                                 format_func=format_func)

        edited_data = st.data_editor(
            df_filtered,
            use_container_width=True,
            hide_index=True,
            column_config={
                "상태": st.column_config.SelectboxColumn("상태", options=["진행중", "완료", "보류", "삭제"]),
                "소재지": st.column_config.TextColumn("📍 소재지 상세", width="large"),
            },
            column_order=["상태", "소재지", "소분류", "가액", "월세", "면적", "고객명", "연락처"]
        )

        if st.button("💾 목록 변경 사항 저장", use_container_width=True):
            st.session_state.df_list.update(edited_data)
            conn.update(data=st.session_state.df_list)
            st.toast("변경사항이 구글 시트에 저장되었습니다.")
            st.rerun()
            
    except Exception as e:
        st.error("데이터를 표시하는 중 오류가 발생했습니다. 매물을 새로 등록해 보세요.")
else:
    # 데이터가 아예 없을 때는 이 메시지만 보여줌
    st.info("현재 등록된 매물이 없습니다. 상단의 '매물 등록하기'를 통해 첫 매물을 등록해 주세요!")
