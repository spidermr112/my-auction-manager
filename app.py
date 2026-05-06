# 다중 키워드 교차 검색 엔진 (숫자 비교 기능 추가 버전)
if search_query:
    keywords = search_query.split()
    filtered_df = df.copy()
    
    for kw in keywords:
        # 1. '이상/이하' 패턴 분석 (예: 12평이상, 5000만이하)
        match = re.match(r"(\d+)(.*?)(이상|이하|초과|미만)", kw)
        
        if match:
            val = float(match.group(1)) # 숫자 (12)
            unit = match.group(2)      # 단위 (평)
            op = match.group(3)        # 조건 (이상)
            
            # 면적 컬럼에서 숫자만 추출하여 비교 (평수 기준)
            if '평' in unit or '면적' in kw:
                # 면적 데이터에서 '12.0평' -> 12.0 숫자만 추출
                filtered_df['temp_num'] = filtered_df['area'].str.extract(r'\((\d+\.?\d*)평\)').astype(float)
                if op == "이상": filtered_df = filtered_df[filtered_df['temp_num'] >= val]
                elif op == "이하": filtered_df = filtered_df[filtered_df['temp_num'] <= val]
            
            # 가격(가액) 컬럼 비교 (단위가 없거나 '만'일 때)
            elif '만' in unit or '가액' in kw or '가격' in kw:
                if op == "이상": filtered_df = filtered_df[filtered_df['price'] >= val]
                elif op == "이하": filtered_df = filtered_df[filtered_df['price'] <= val]
        
        else:
            # 2. 일반 키워드 검색 (기존 로직)
            mask = filtered_df.astype(str).apply(lambda x: x.str.contains(kw, case=False, na=False)).any(axis=1)
            filtered_df = filtered_df[mask]
    
    display_df = filtered_df
