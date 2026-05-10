import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import re

# 1. 페이지 설정
st.set_page_config(page_title="페이지부동산", page_icon="📄", layout="wide")
st.title("📄 페이지부동산 매물 관리 시스템")

# --- [연결] 구글 스프레드시트 연결 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        data = conn.read(ttl=0)
        data = data.dropna(how='all').fillna("")
        num_cols = ["가액", "월세"]
        for col in num_cols:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0).astype(int)
        return data
    except Exception:
        return pd.DataFrame(columns=["접수일", "고객명", "연락처", "대분류", "소분류", "면적", "가액", "월세", "상태", "소재지", "특약사항"])

df_list = load_data()

# 면적 계산 함수
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
with st.expander("➕ 새 매물 등록", expanded=False):
    col1, col2, col3 = st.columns([1, 1, 1.2])
    with col1:
        reg_date = st.date_input("접수일", datetime.today())
        # 각 입력창에 고유한 key를 부여합니다.
        client_name = st.text_input("고객명", key="reg_name")
        client_phone = st.text_input("연락처", key="reg_phone")
        main_cat = st.radio("물건 대분류", list(category_map.keys()), horizontal=True)
    with col2:
        sub_cat = st.selectbox("물건 소분류", category_map[main_cat])
        deal_type = st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        addr = st.text_input("소재지 상세", key="reg_addr")
        price = st.number_input("가액 (만원)", step=0, key="reg_price")
        rent = st.number_input("월세 (만원)", step=0, key="reg_rent") if deal_type == "월세" else 0
    with col3:
        area_text = st.text_input("면적 입력", key="reg_area")
        _, py_display = process_area(area_text)
        
        # 특약내용 템플릿
        dynamic_tmpl = f"[{sub_cat} {deal_type} 상세]\n- 비밀번호: \n- 로열층/방향: \n- 관리비: \n- 입주일: "
        memo = st.text_area("특약내용", value=dynamic_tmpl, height=200, key="reg_memo")

    # [저장 버튼 로직]
    if st.button("🏠 구글 시트에 저장", use_container_width=True):
        if client_name and addr:
            new_entry = pd.DataFrame([{
                "접수일": reg_date.strftime("%Y-%m-%d"), 
                "고객명": client_name, "연락처": client_phone, 
                "대분류": main_cat, "소분류": sub_cat, "면적": py_display, 
                "가액": price, "월세": rent, "상태": "진행중", 
                "소재지": addr, "특약사항": memo
            }])
            
            # 1. 데이터 전송
            updated_df = pd.concat([new_entry, df_list], ignore_index=True)
            conn.update(data=updated_df)
            
            # 2. [가장 중요] 입력값 초기화
            # 세션에 저장된 입력값들을 삭제하여 초기 상태로 만듭니다.
            for key in ["reg_name", "reg_phone", "reg_addr", "reg_area", "reg_price", "reg_rent", "reg_memo"]:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.success("성공적으로 저장되었습니다!")
            # 3. 화면 새로고침 (빈 칸으로 보이기 위해)
            st.rerun()
        else:
            st.error("고객명과 소재지는 꼭 입력해주세요!")

st.divider()

# --- 이하 목록 및 상세정보 (생략하지만 원본 유지 필요) ---
# (이전 코드와 동일한 목록 보기 로직을 그대로 사용하시면 됩니다)
