import streamlit as st
import pandas as pd
from datetime import datetime
import re
import gspread
from google.oauth2.service_account import Credentials

# --- [1. 구글 시트 연결 설정] ---
# 본인의 구글 스프레드시트 ID
SPREADSHEET_ID = "1Ix8kepf4TPK3LXGtkeA_1WzjzJu9DCNwer7bIsStC2g"

# 서비스 계정 JSON 정보
# [수정 포인트] private_key 문자열 앞에 r을 붙여 원시 문자열로 만들거나, 
# 실제 개행 문자가 처리될 수 있도록 구성해야 합니다.
SERVICE_ACCOUNT_INFO = {
    "type": "service_account",
    "project_id": "my-property-manager-495705",
    "private_key_id": "1ce144cc70bc1c9d23c60ed17cc4dde9a446fada",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDAMMAUKuug/XKV\nNL+BGXN+jBTrpBqoPTLu3pPQvFYBrpLRdSJzAv+lcCixuKUi0j2CNxOI8EWJ70tZ\nEzKk28/6J9q+fMllx/kxLVw8LwELvuEdPB7kGfa/veJ93pX55tKKkT5AzAWXEZDv\nqbt58OvY5wPYgf3Ovx5ZzVDUZDDOPccGL9x78Zz+IbV3xmjMlKsWwcxNDvdItRW0\njtY6EocwinJKCdHEf2OWwrqOnHoUI4AXNW5AapgcIuzJVVlnEGMSq+Box7elvKWR\nz/bydkz1lOk4C6WoV1Vxmxl1VjxouSR9b1GkiuVujgpzwIbtwx4qw37OB+GNyxfK\n/wIm9Sr3AgMBAAECggEAXHb36pwNumpFtvBmVGvUy6UEqaxN4PR0rUTrs+jwriV5\n4Iks9k2ShltUUNDnrj2dNyldXixPIII+64+XdYaF5LJJBQ2PbccMpnLO5eutYqPG\ntaSHrjGpq+1k6y7sVAuP7vfbDhy6cciTRSMRniThq3zVtlQwMshzhzwHL/A2JPrv\nhvXQ9sRa5jSYqnaWE/j10qT0ZYCoFl4pbDOpzFiPbHx/etHbAkBNZDeLyImlXo5X\nJE1ztTYcC1xTMqkx8vMTUBUdtqOOtjReSlNDXAnEGhNOxjQiceZ1zvFCGUaEUity\nTRaHOHtxX+1NLfB1t4dQpC+WCbxcRo8odFkTcDmNmQKBgQD9yPfjJpgxl00VVEjo\nXTo9AS+4hIc2B6W6yDflNZux/kF7401bQ3knV0thSfhhShHmIZMcQSkR1TJ0XdGJ\nS0dKRZzibxQxHNUdxVZ5Pz5tMLaO1EhgQw2BR4V2pdzmJtUKxBB0EIF1vbU+gcf1\njUMWXA6WAGcQRmemIpmjbtRryQKBgQDB3ilGYATwT6zECGUJ17AOUon2PgN5LjSS\nJHhw47Vv6f89u7yS64lexTBMWp67GNnYhS72tmRyZMQYSBRxKIUqhhX43cw2grV4\n2IXd+3gk2QmGD/dPNAnfbB7wrkDuv83kD3u+JR7FPCUtK3QGp1n0WZct7UTs2Awi\nh138xZLAvwKBgQCwC/cZVa6ByCkqwJsKxZEevHH0F8sLyeZHWZicocFtiai3XghN\nZNLoXX/m7z8jjhQ4hdXc5b6tpi0n1+UAzn2Xog6gbNme8BdOXZQM67hMWlxpXA0Q\n6bK2mXyVv50q8okavMOFH+YOXRkbUT/6sJF3M0jS+ViFS7Ge56WYX8tvMQKBgQCq\ncHeXIHmXEGUSX1L9CTwGC3ixHSoOkpmzVg7xKLBtuKomivOpsxutTu08Y3sjgCCd\no9F7IzVCAOcJde1K4tXYYdPVXKHZ1qZWnP1sAFZLBujBjS3e2yBG5ZZ6AKijfcs0\nUox2ycm4mz0P7iDubJjAIzevL+cl1ncssBfoT4bKnwKBgFvmqH+DXEhR3SHpVey9\n7hp/iw3GtW25t/dGgEdirh1y7tnMBip0IVbTXA/3fHWrDnrRRU+z+7HW0lAtRYov\nvXynS6M8T/5v/Q6xx+JymAjuXTtViac8tP1VdIwliVkUffgFjtv8UNr73xi6Q93h\buVjgUSsRWoHnmcSNudcdCFF\n-----END PRIVATE KEY-----\n",
    "client_email": "sheet-manager@my-property-manager-495705.iam.gserviceaccount.com",
    "token_uri": "https://oauth2.googleapis.com/token",
}

@st.cache_resource
def get_gsheet_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    # [중요] private_key 내부의 \n 문자열이 실제 개행 문자로 인식되도록 .replace 처리
    info = SERVICE_ACCOUNT_INFO.copy()
    info["private_key"] = info["private_key"].replace("\\n", "\n")
    
    creds = Credentials.from_service_account_info(info, scopes=scope)
    return gspread.authorize(creds)

def load_data():
    try:
        client = get_gsheet_client()
        sheet = client.open_by_key(SPREADSHEET_ID).get_worksheet(0)
        data = sheet.get_all_records()
        if not data: # 데이터가 아예 없을 경우 빈 프레임 반환
            return pd.DataFrame(columns=["접수일", "고객명", "연락처", "대분류", "소분류", "면적", "가액", "월세", "상태", "소재지", "특약사항"])
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"구글 시트 데이터를 불러오는데 실패했습니다: {e}")
        return pd.DataFrame(columns=["접수일", "고객명", "연락처", "대분류", "소분류", "면적", "가액", "월세", "상태", "소재지", "특약사항"])

def save_to_sheet(new_data):
    client = get_gsheet_client()
    sheet = client.open_by_key(SPREADSHEET_ID).get_worksheet(0)
    # 모든 데이터를 문자열로 변환하여 전송
    row_to_save = new_data.iloc[0].astype(str).tolist()
    sheet.append_row(row_to_save)

# --- [2. 앱 UI 구성] ---
st.set_page_config(page_title="부동산 매물 관리 시스템", page_icon="🏢", layout="wide")
st.title("🏢 부동산 매물 등록 시스템")

# 세션 상태에 데이터 로드
if 'df_list' not in st.session_state:
    st.session_state.df_list = load_data()

# 도우미 함수
def get_dynamic_template(sub_cat, deal_type):
    return f"[{sub_cat} {deal_type} 상세]\n- 비밀번호: \n- 로열층/방향: \n- 관리비: \n- 입주일: "

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

# --- [3. 매물 등록 섹션] ---
with st.expander("➕ 새 매물 등록하기", expanded=True):
    col1, col2, col3 = st.columns([1, 1, 1.2])
    with col1:
        reg_date = st.date_input("접수일", datetime.today())
        client_name = st.text_input("고객명")
        client_phone = st.text_input("연락처")
        main_cat = st.radio("물건 대분류", list(category_map.keys()), horizontal=True)
    with col2:
        sub_cat = st.selectbox("물건 소분류", category_map[main_cat])
        deal_type = st.radio("구분", ["매매", "전세", "월세"], horizontal=True)
        addr = st.text_input("소재지 상세")
        price = st.number_input("가액 (만원)", step=100)
        rent = st.number_input("월세 (만원)", step=10) if deal_type == "월세" else 0
    with col3:
        area_text = st.text_input("면적 입력 (예: 84 또는 25평)")
        _, py_display = process_area(area_text)
        dynamic_tmpl = get_dynamic_template(sub_cat, deal_type)
        memo = st.text_area("특약내용", value=dynamic_tmpl, height=200)

    if st.button("🏠 데이터베이스 저장", use_container_width=True):
        if not addr or not client_name:
            st.warning("고객명과 소재지를 입력해 주세요.")
        else:
            new_row = pd.DataFrame([{
                "접수일": reg_date.strftime("%Y-%m-%d"), 
                "고객명": client_name, 
                "연락처": client_phone, 
                "대분류": main_cat, 
                "소분류": sub_cat, 
                "면적": py_display, 
                "가액": price, 
                "월세": rent, 
                "상태": "진행중", 
                "소재지": addr, 
                "특약사항": memo
            }])
            
            try:
                save_to_sheet(new_row)
                st.success("✅ 성공적으로 저장되었습니다!")
                # 데이터 즉시 갱신
                st.session_state.df_list = load_data() 
                st.rerun()
            except Exception as e:
                st.error(f"저장 중 오류 발생: {e}")

st.divider()

# --- [4. 필터 및 목록 섹션] ---
with st.expander("🔍 매물 필터링 / 검색", expanded=False):
    f_col1, f_col2, f_col3 = st.columns([1, 1, 1])
    with f_col1: status_list = st.multiselect("상태 선택", ["진행중", "완료", "보류", "삭제"], default=["진행중", "보류"])
    with f_col2: filter_cat = st.multiselect("대분류 선택", list(category_map.keys()), default=list(category_map.keys()))
    with f_col3: search_q = st.text_input("소재지 검색")

df_filtered = st.session_state.df_list.copy()

if not df_filtered.empty:
    # 필터링 적용
    if status_list:
        df_filtered = df_filtered[df_filtered['상태'].isin(status_list)]
    if filter_cat:
        df_filtered = df_filtered[df_filtered['대분류'].isin(filter_cat)]
    if search_q:
        df_filtered = df_filtered[df_filtered['소재지'].astype(str).str.contains(search_q, na=False)]

st.subheader(f"📋 매물 목록 (조회: {len(df_filtered)}건)")

if not df_filtered.empty:
    # 매물 선택 드롭다운
    select_options = {i: f"{row['소재지']} ({row['고객명']})" for i, row in df_filtered.iterrows()}
    target_idx = st.selectbox("🎯 상세 정보를 보려면 매물을 선택하세요", 
                             options=list(select_options.keys()), 
                             format_func=lambda x: select_options[x])

    # 데이터 테이블 표시
    st.data_editor(
        df_filtered,
        use_container_width=True,
        hide_index=True,
        column_config={
            "상태": st.column_config.SelectboxColumn("상태", options=["진행중", "완료", "보류", "삭제"]),
            "소재지": st.column_config.TextColumn("📍 소재지 상세", width="large"),
        }
    )

    # 하단 상세 정보 섹션
    item = df_filtered.loc[target_idx]
    st.markdown("---")
    with st.container(border=True):
        st.markdown(f"### 🔍 [{item['소재지']}] 상세 정보")
        c1, c2 = st.columns([1, 2])
        with c1:
            st.info(f"📍 **{item['소재지']}**")
            st.write(f"🏷️ **분류:** {item['소분류']} ({item['상태']})")
            st.write(f"📞 **고객:** {item['고객명']} ({item['연락처']})")
            st.success(f"💰 **가액:** {item['가액']} / **월세:** {item['월세']}")
        with c2:
            st.markdown("**📜 상세 특약 및 메모**")
            st.text_area("상세내용", value=str(item.get('특약사항', "")), height=250, label_visibility="collapsed")
else:
    st.info("조회된 매물이 없습니다.")
