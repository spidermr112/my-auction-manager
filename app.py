import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# 1. 한글 변환 함수 정의
def format_korean_price(price_manwon):
    if price_manwon is None or price_manwon == 0:
        return "0원"
    
    eok = price_manwon // 10000
    man = price_manwon % 10000
    
    result = []
    if eok > 0:
        result.append(f"{int(eok)}억")
    if man > 0:
        result.append(f"{int(man)}만원")
    
    return " ".join(result)

# ... (기본 설정 및 DB 로직 생략) ...

with st.sidebar:
    st.subheader("🏠 매물 등록")
    # ... (대분류/소분류 생략) ...

    # 거래가액 입력
    price = st.number_input("거래가액 (단위: 만원)", min_value=0, value=None, step=100, placeholder="숫자만 입력 (예: 1억 -> 10000)")
    
    # [추가된 기능] 숫자를 입력하면 바로 아래에 한글로 표시
    if price:
        st.info(f"💰 확인: **{format_korean_price(price)}**")

    address = st.text_input("소재지 (상세 주소 포함)")
    # ... (이하 동일) ...
