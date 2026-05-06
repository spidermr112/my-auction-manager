import streamlit as st
import pandas as pd
from datetime import datetime
import os
import re
import time

# --- 페이지 설정 (Wide 유지) ---
st.set_page_config(page_title="파크부동산 매물관리", layout="wide")

# --- [CSS 추가] 사이드바 폭 고정 및 가독성 향상 ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        min-width: 350px;
        max-width: 350px;
    }
    </style>
    """, unsafe_allow_html=True)

# ... (기존 load_data, save_data, parse_korean_price 함수는 동일) ...

# --- [개선] 매물 등록 파트를 사이드바로 이동 ---
with st.sidebar:
    st.header("📍 매물 등록")
    # 여기에 기존 col_reg 안에 있던 입력 코드들을 모두 넣습니다.
    # 예: reg_date = st.date_input("접수일", ...)
    # ... 

# --- [개선] 메인 화면은 목록에만 집중 ---
st.title("🏘️ 파크부동산 통합 관리")
# 검색 및 필터, 데이터프레임 출력 코드
# ...
