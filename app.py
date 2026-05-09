import streamlit as st
import pandas as pd
from datetime import datetime
import re
import gspread
from google.oauth2.service_account import Credentials
import json  # 추가

# --- [1. 구글 시트 연결 설정] ---
SPREADSHEET_ID = "1Ix8kepf4TPK3LXGtkeA_1WzjzJu9DCNwer7bIsStC2g"

# 서비스 계정 JSON 정보
SERVICE_ACCOUNT_INFO = {
    "type": "service_account",
    "project_id": "my-property-manager-495705",
    "private_key_id": "1ce144cc70bc1c9d23c60ed17cc4dde9a446fada",
    # 여기에 있는 \n은 문자열 "역슬래시+n"입니다.
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDAMMAUKuug/XKV\nNL+BGXN+jBTrpBqoPTLu3pPQvFYBrpLRdSJzAv+lcCixuKUi0j2CNxOI8EWJ70tZ\nEzKk28/6J9q+fMllx/kxLVw8LwELvuEdPB7kGfa/veJ93pX55tKKkT5AzAWXEZDv\nqbt58OvY5wPYgf3Ovx5ZzVDUZDDOPccGL9x78Zz+IbV3xmjMlKsWwcxNDvdItRW0\njtY6EocwinJKCdHEf2OWwrqOnHoUI4AXNW5AapgcIuzJVVlnEGMSq+Box7elvKWR\nz/bydkz1lOk4C6WoV1Vxmxl1VjxouSR9b1GkiuVujgpzwIbtwx4qw37OB+GNyxfK\n/wIm9Sr3AgMBAAECggEAXHb36pwNumpFtvBmVGvUy6UEqaxN4PR0rUTrs+jwriV5\n4Iks9k2ShltUUNDnrj2dNyldXixPIII+64+XdYaF5LJJBQ2PbccMpnLO5eutYqPG\ntaSHrjGpq+1k6y7sVAuP7vfbDhy6cciTRSMRniThq3zVtlQwMshzhzwHL/A2JPrv\nhvXQ9sRa5jSYqnaWE/j10qT0ZYCoFl4pbDOpzFiPbHx/etHbAkBNZDeLyImlXo5X\nJE1ztTYcC1xTMqkx8vMTUBUdtqOOtjReSlNDXAnEGhNOxjQiceZ1zvFCGUaEUity\nTRaHOHtxX+1NLfB1t4dQpC+WCbxcRo8odFkTcDmNmQKBgQD9yPfjJpgxl00VVEjo\nXTo9AS+4hIc2B6W6yDflNZux/kF7401bQ3knV0thSfhhShHmIZMcQSkR1TJ0XdGJ\S0dKRZzibxQxHNUdxVZ5Pz5tMLaO1EhgQw2BR4V2pdzmJtUKxBB0EIF1vbU+gcf1\njUMWXA6WAGcQRmemIpmjbtRryQKBgQDB3ilGYATwT6zECGUJ17AOUon2PgN5LjSS\nJHhw47Vv6f89u7yS64lexTBMWp67GNnYhS72tmRyZMQYSBRxKIUqhhX43cw2grV4\n2IXd+3gk2QmGD/dPNAnfbB7wrkDuv83kD3u+JR7FPCUtK3QGp1n0WZct7UTs2Awi\nh138xZLAvwKBgQCwC/cZVa6ByCkqwJsKxZEevHH0F8sLyeZHWZicocFtiai3XghN\nZNLoXX/m7z8jjhQ4hdXc5b6tpi0n1+UAzn2Xog6gbNme8BdOXZQM67hMWlxpXA0Q\n6bK2mXyVv50q8okavMOFH+YOXRkbUT/6sJF3M0jS+ViFS7Ge56WYX8tvMQKBgQCq\ncHeXIHmXEGUSX1L9CTwGC3ixHSoOkpmzVg7xKLBtuKomivOpsxutTu08Y3sjgCCd\no9F7IzVCAOcJde1K4tXYYdPVXKHZ1qZWnP1sAFZLBujBjS3e2yBG5ZZ6AKijfcs0\nUox2ycm4mz0P7iDubJjAIzevL+cl1ncssBfoT4bKnwKBgFvmqH+DXEhR3SHpVey9\n7hp/iw3GtW25t/dGgEdirh1y7tnMBip0IVbTXA/3fHWrDnrRRU+z+7HW0lAtRYov\nvXynS6M8T/5v/Q6xx+JymAjuXTtViac8tP1VdIwliVkUffgFjtv8UNr73xi6Q93h\buVjgUSsRWoHnmcSNudcdCFF\n-----END PRIVATE KEY-----\n",
    "client_email": "sheet-manager@my-property-manager-495705.iam.gserviceaccount.com",
    "token_uri": "https://oauth2.googleapis.com/token",
}

@st.cache_resource
def get_gsheet_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    # [수정 핵심] dict 객체를 직접 수정하지 않고 복사본을 만들어 처리
    creds_dict = SERVICE_ACCOUNT_INFO.copy()
    
    # 1. 문자열 내의 \\n을 실제 개행문자 \n으로 변경 (매우 중요)
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    
    # 2. 만약 개행문자 처리가 중복되었다면 정리
    if "-----BEGIN PRIVATE KEY-----\n\n" in creds_dict["private_key"]:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\n\n", "\n")

    try:
        # from_service_account_info를 사용하여 인증
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"인증 생성 중 치명적 오류: {e}")
        raise e

# --- 이하 데이터 로드 및 저장 함수 ---
def load_data():
    try:
        client = get_gsheet_client()
        sheet = client.open_by_key(SPREADSHEET_ID).get_worksheet(0)
        data = sheet.get_all_records()
        return pd.DataFrame(data) if data else pd.DataFrame(columns=["접수일", "고객명", "연락처", "대분류", "소분류", "면적", "가액", "월세", "상태", "소재지", "특약사항"])
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return pd.DataFrame(columns=["접수일", "고객명", "연락처", "대분류", "소분류", "면적", "가액", "월세", "상태", "소재지", "특약사항"])

def save_to_sheet(new_row_df):
    try:
        client = get_gsheet_client()
        sheet = client.open_by_key(SPREADSHEET_ID).get_worksheet(0)
        # 데이터를 리스트 형태로 변환
        row_values = new_row_df.iloc[0].astype(str).tolist()
        sheet.append_row(row_values)
        return True
    except Exception as e:
        st.error(f"시트 저장 실패: {e}")
        return False

# --- UI 부분은 이전과 동일 (save_to_sheet 호출 부분만 체크) ---
# (중략 - UI 코드 생략)

# 매물 등록 버튼 클릭 시 호출 부분
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
        
        # 수정된 저장 함수 실행
        success = save_to_sheet(new_row)
        if success:
            st.success("✅ 성공적으로 저장되었습니다!")
            st.session_state.df_list = load_data() 
            st.rerun()
