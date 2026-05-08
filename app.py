import streamlit as st
import pandas as pd
from datetime import datetime
import re
from google.oauth2.service_account import Credentials
import gspread

# --- [설정 및 연결] ---
st.set_page_config(page_title="파크부동산", page_icon="🏘️", layout="wide")

# 구글 시트 ID를 입력하세요 (URL 중간의 긴 문자열)
SPREADSHEET_ID = "여기에_구글_시트_ID를_넣으세요"

# 제공하신 JSON 정보를 활용한 인증
SERVICE_ACCOUNT_INFO = {
    "type": "service_account",
    "project_id": "my-property-manager-495705",
    "private_key_id": "1ce144cc70bc1c9d23c60ed17cc4dde9a446fada",
    "private_key": st.secrets.get("private_key", "JSON에있던_PRIVATE_KEY_전체_복사"), # 또는 아래 주석 참고
    "client_email": "sheet-manager@my-property-manager-495705.iam.gserviceaccount.com",
    "token_uri": "https://oauth2.googleapis.com/token",
}

# 💡 팁: 실제 배포 시에는 st.secrets를 사용하는 것이 보안상 안전합니다.

def get_gsheet_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=scope)
    return gspread.authorize(creds)

def load_data():
    client = get_gsheet_client()
    sheet = client.open_by_key(SPREADSHEET_ID).get_worksheet(0)
    data = sheet.get_all_records()
    return pd.DataFrame(data)

def save_to_sheet(new_data_row):
    client = get_gsheet_client()
    sheet = client.open_by_key(SPREADSHEET_ID).get_worksheet(0)
    sheet.append_row(new_data_row.values.flatten().tolist())

# --- [기존 로직 및 UI] ---
st.title("🏘️ 파크부동산 매물 등록 시스템")

# 데이터 불러오기 (session_state 대신 구글 시트에서 로드)
if 'df_list' not in st.session_state:
    try:
        st.session_state.df_list = load_data()
    except:
        st.error("구글 시트 연결 실패! 시트 ID와 공유 설정을 확인하세요.")
        st.session_state.df_list = pd.DataFrame(columns=["접수일", "고객명", "연락처", "대분류", "소분류", "면적", "가액", "월세", "상태", "소재지", "특약사항"])

# [기존 도우미 함수들]
def get_dynamic_template(sub_cat, deal_type):
    check_items = ["현 시설 상태", "입주시기 협의"]
    res_cats = ["아파트", "연립/다세대", "단독/다가구", "전원주택", "오피스텔(주거)"]
    if sub_cat in res_cats: check_items += ["장기수선충당금", "발코니 확장", "수리 여부"]
    tmpl = f"[{sub_cat} {deal_type} 상세]\n- 비밀번호: \n- 로열층/방향: \n- 관리비: \n- 입주일: "
    return check_items, tmpl

def process_area(input_str):
    if not input_str or input_str.strip() == "": return 0, "-" 
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", input_str)
    if not nums: return 0, "-"
    val = float(nums[0])
    p = int(val) if "평" in input_str else int(round(val * 0.3025))
    return p, f"{p}평"

category_map = {"주거용": ["아파트", "연립/다세대", "단독/다가구", "전원주택", "오피스텔(주거)"], "비주거용": ["상가/사무실", "빌딩/건물", "공장/창고", "지식산업센터", "숙박시설"], "토지": ["대지", "전/답/과수원", "임야", "잡종지", "기타토지", "복수토지"]}

# 2. 매물 등록하기
with st.expander("➕ 매물 등록하기", expanded=False):
    col1, col2, col3 = st.columns([1, 1, 1.2])
    with col1:
        reg_date = st.date_input("접수일", datetime.today())
        client_name = st.text_input("고객명", key="reg_name")
        client_phone = st.text_input("연락처", key="reg_phone")
        main_cat = st.radio("물건 대분류", list(category_map.keys()), horizontal=True)
    with col2:
        sub_cat = st.selectbox("물건 소분류", category_map[main_cat])
        deal_type = st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        addr = st.text_input("소재지 상세", key="reg_addr")
        price = st.number_input("가액 (만원)", step=0)
        rent = st.number_input("월세 (만원)", step=0) if deal_type == "월세" else 0
    with col3:
        area_text = st.text_input("면적 입력", key="reg_area")
        _, py_display = process_area(area_text)
        _, dynamic_tmpl = get_dynamic_template(sub_cat, deal_type)
        memo = st.text_area("특약내용", value=dynamic_tmpl, height=200)

    if st.button("🏠 데이터베이스 저장", use_container_width=True):
        new_row = pd.DataFrame([{"접수일": str(reg_date), "고객명": client_name, "연락처": client_phone, "대분류": main_cat, "소분류": sub_cat, "면적": py_display, "가액": price, "월세": rent, "상태": "진행중", "소재지": addr, "특약사항": memo}])
        # 구글 시트에 저장
        save_to_sheet(new_row)
        st.success("데이터가 구글 시트에 안전하게 저장되었습니다!")
        st.session_state.df_list = load_data() # 새로고침
        st.rerun()

st.divider()

# 3. 매물 필터링 / 목록 (기존 코드와 동일)
with st.expander("🔍 매물 필터링 / 검색", expanded=False):
    f_col1, f_col2, f_col3 = st.columns([1, 1, 1])
    with f_col1: status_list = st.multiselect("상태 선택", ["진행중", "완료", "보류", "삭제"], default=["진행중", "보류"])
    with f_col2: filter_cat = st.multiselect("대분류 선택", list(category_map.keys()), default=list(category_map.keys()))
    with f_col3: search_q = st.text_input("소재지 검색")

df_filtered = st.session_state.df_list.copy()
if not df_filtered.empty:
    df_filtered = df_filtered[df_filtered['상태'].isin(status_list)]
    df_filtered = df_filtered[df_filtered['대분류'].isin(filter_cat)]
    if search_q: df_filtered = df_filtered[df_filtered['소재지'].astype(str).str.contains(search_q, na=False)]

st.subheader(f"📋 매물 목록 (조회: {len(df_filtered)}건)")

if not df_filtered.empty:
    select_list = {i: f"{row['소재지']} ({row['고객명']})" for i, row in df_filtered.iterrows()}
    target_idx = st.selectbox("🎯 상세 정보를 보려면 매물을 선택하세요", options=list(select_list.keys()), format_func=lambda x: select_list[x])

    st.data_editor(df_filtered, use_container_width=True, hide_index=True)

    # 4. 하단 상세 정보창
    item = df_filtered.loc[target_idx]
    st.markdown("---")
    with st.container(border=True):
        st.markdown(f"### 🔍 [{item['소재지']}] 상세 특약")
        st.text_area("상세내용", value=item.get('특약사항', ""), height=300)
else:
    st.info("조회된 매물이 없습니다.")
