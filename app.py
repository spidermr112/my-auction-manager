import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import re


# ─────────────────────────────────────────
# 유틸 함수
# ─────────────────────────────────────────

def format_phone(raw: str) -> str:
    if not raw: return ""
    nums = "".join(filter(str.isdigit, raw))
    if len(nums) == 8: nums = "010" + nums
    if len(nums) == 11: return f"{nums[:3]}-{nums[3:7]}-{nums[7:]}"
    if len(nums) == 10: return f"{nums[:3]}-{nums[3:6]}-{nums[6:]}"
    return raw

def parse_area(raw: str) -> str:
    if not raw or not raw.strip(): return "-"
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", raw)
    if not nums: return "-"
    val = float(nums[0])
    pyeong = int(val) if "평" in raw else int(round(val * 0.3025))
    return f"{pyeong}평"

def reset_session():
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()


# ─────────────────────────────────────────
# 상수
# ─────────────────────────────────────────

CATEGORY_MAP = {
    "주거용":   ["아파트", "연립/다세대", "단독/다가구", "전원주택", "오피스텔(주거)"],
    "비주거용": ["상가", "사무실", "공장", "창고", "빌딩/건물", "지식산업센터", "숙박시설"],
    "토지":     ["대지", "전/답/과수원", "임야", "잡종지", "기타토지"],
}
COLUMNS_ORDER = ["상태", "소분류", "소재지", "면적", "가액", "월세", "고객명", "연락처"]


# ─────────────────────────────────────────
# 페이지 설정 & 글로벌 CSS
# ─────────────────────────────────────────

st.set_page_config(page_title="페이지부동산", page_icon="📄", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #f8f9fa; }

/* 탭 */
button[data-baseweb="tab"] {
    font-size: 15px !important;
    font-weight: 700 !important;
    padding: 10px 18px !important;
}

/* ── 네비게이션 행: nav-marker가 있는 columns만 저격 ── */
div[data-testid="stHorizontalBlock"]:has(.nav-marker) {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    justify-content: center !important;
    align-items: center !important;
    gap: 6px !important;
    width: 220px !important;
    min-width: 220px !important;
    margin: 16px auto 8px auto !important;
}

/* 각 열 너비 고정 */
div[data-testid="stHorizontalBlock"]:has(.nav-marker) > div[data-testid="stColumn"] {
    padding: 0 !important;
    margin: 0 !important;
    flex: none !important;
}
div[data-testid="stHorizontalBlock"]:has(.nav-marker) > div[data-testid="stColumn"]:nth-of-type(1),
div[data-testid="stHorizontalBlock"]:has(.nav-marker) > div[data-testid="stColumn"]:nth-of-type(3) {
    width: 54px !important;
    min-width: 54px !important;
    max-width: 54px !important;
}
div[data-testid="stHorizontalBlock"]:has(.nav-marker) > div[data-testid="stColumn"]:nth-of-type(2) {
    width: 100px !important;
    min-width: 100px !important;
    max-width: 100px !important;
}

/* 버튼 스타일 */
div[data-testid="stHorizontalBlock"]:has(.nav-marker) button {
    width: 100% !important;
    height: 40px !important;
    font-size: 16px !important;
    font-weight: 700 !important;
    padding: 0 !important;
    background: white !important;
    border: 1px solid #cbd5e1 !important;
    color: #334155 !important;
    border-radius: 8px !important;
}
div[data-testid="stHorizontalBlock"]:has(.nav-marker) button:hover {
    border-color: #007AFF !important;
    color: #007AFF !important;
}

/* 카운터 */
.nav-counter {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 40px;
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    font-weight: 700;
    font-size: 14px;
    color: #334155;
}

/* 마커 숨김 */
.nav-marker { display: none; }

/* 메모 저장 버튼 */
button[data-testid="stBaseButton-secondary"][key^="save_slide_"] {
    margin-top: 10px !important;
    height: 44px !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    background: white !important;
    border: 1.5px solid #007AFF !important;
    color: #007AFF !important;
}
button[data-testid="stBaseButton-secondary"][key^="save_slide_"]:hover {
    background: #007AFF !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# 구글 시트 연결 & 데이터 로드
# ─────────────────────────────────────────

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data() -> pd.DataFrame:
    try:
        df = conn.read(ttl=0)
        df = df.dropna(how="all").fillna("")
        for col in ["가액", "월세"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
        return df
    except Exception:
        return pd.DataFrame(columns=["접수일", "고객명", "연락처", "대분류", "소분류",
                                     "면적", "가액", "월세", "상태", "소재지", "특약사항"])

df_all = load_data()


# ─────────────────────────────────────────
# 탭 구성
# ─────────────────────────────────────────

st.title("📄 페이지부동산 매물 관리 시스템")
tab_register, tab_list, tab_search = st.tabs(["➕ 신규등록", "📋 전체목록", "🔍 목록검색"])


# ═══════════════════════════════════════════
# TAB 1 — 신규등록
# ═══════════════════════════════════════════

with tab_register:
    st.subheader("➕ 신규 매물 등록")
    with st.container(border=True):
        col_a, col_b, col_c = st.columns([1, 1, 1.2])

        with col_a:
            reg_date    = st.date_input("접수일", datetime.today(), key="reg_date")
            client_name = st.text_input("고객명", key="reg_name")
            raw_phone   = st.text_input("연락처", placeholder="숫자만 입력해도 됩니다", key="reg_phone")
            if raw_phone: st.caption(f"저장 포맷: `{format_phone(raw_phone)}`")
            main_cat = st.radio("물건 대분류", list(CATEGORY_MAP.keys()), horizontal=True, key="reg_main")

        with col_b:
            sub_cat   = st.selectbox("물건 소분류", CATEGORY_MAP[main_cat], key="reg_sub")
            deal_type = st.radio("거래 구분", ["매매", "전세", "월세"], horizontal=True, key="reg_deal")
            addr      = st.text_input("소재지 상세", key="reg_addr")
            price     = st.number_input("가액 (만원)", min_value=0, step=100, key="reg_price")
            rent      = st.number_input("월세 (만원)", min_value=0, step=10,  key="reg_rent")

        with col_c:
            area_text    = st.text_input("면적 (예: 84㎡ 또는 25평)", key="reg_area")
            default_memo = (f"[{sub_cat} {deal_type} 상세정보]\n"
                            "- 비밀번호: \n- 로열층/방향: \n- 관리비: \n- 입주일: ")
            memo = st.text_area("특약 내용",
                                value=st.session_state.get("reg_memo", default_memo),
                                height=200, key="reg_memo")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🏠 매물 저장", use_container_width=True):
            if not client_name or not addr:
                st.warning("고객명과 소재지 상세는 필수 입력 항목입니다.")
            else:
                new_row = pd.DataFrame([{
                    "접수일": reg_date.strftime("%Y-%m-%d"), "고객명": client_name,
                    "연락처": format_phone(raw_phone),       "대분류": main_cat,
                    "소분류": sub_cat,                        "면적":   parse_area(area_text),
                    "가액":   price,                          "월세":   rent,
                    "상태":   "진행중",                       "소재지": addr,
                    "특약사항": memo,
                }])
                conn.update(data=pd.concat([new_row, df_all], ignore_index=True))
                st.success("새로운 매물이 저장되었습니다!")
                st.rerun()


# ═══════════════════════════════════════════
# TAB 2 — 전체목록
# ═══════════════════════════════════════════

with tab_list:
    st.subheader(f"📋 등록 매물 전체 목록 ({len(df_all)}건)")
    st.data_editor(
        df_all,
        use_container_width=True,
        hide_index=False,
        column_config={
            "상태":     st.column_config.SelectboxColumn("상태", options=["진행중", "완료", "보류", "삭제"]),
            "특약사항": None,
        },
        column_order=COLUMNS_ORDER,
    )


# ═══════════════════════════════════════════
# TAB 3 — 목록검색
# ═══════════════════════════════════════════

with tab_search:

    # ── 필터 ──
    st.subheader("🔍 통합 검색 필터")
    with st.container(border=True):
        f1, f2, f3, f4 = st.columns([1.5, 1, 1, 1])
        with f1: search_q = st.text_input("📍 검색어", placeholder="주소, 고객명…", key="f_search")
        with f2: f_main   = st.multiselect("🏗️ 종류", list(CATEGORY_MAP.keys()), default=list(CATEGORY_MAP.keys()), key="f_main")
        with f3: f_deal   = st.multiselect("💰 거래", ["매매", "전세", "월세"],   default=["매매", "전세", "월세"],  key="f_deal")
        with f4: f_status = st.multiselect("🚦 상태", ["진행중", "완료", "보류", "삭제"], default=["진행중", "보류"], key="f_status")
        if st.button("🔄 검색 조건 초기화", use_container_width=True, key="btn_reset"):
            reset_session()

    # ── 필터 적용 ──
    df_filtered = df_all.copy()
    if not df_filtered.empty:
        df_filtered = df_filtered[df_filtered["상태"].isin(f_status)]
        if "대분류" in df_filtered.columns:
            df_filtered = df_filtered[df_filtered["대분류"].isin(f_main)]
        if search_q:
            df_filtered = df_filtered[
                df_filtered["소재지"].str.contains(search_q, na=False) |
                df_filtered["고객명"].str.contains(search_q, na=False)
            ]

    if df_filtered.empty:
        st.warning("검색 조건에 맞는 매물이 없습니다. 필터를 조정해 주세요.")
        st.stop()

    # ── 상세 브리핑 ──
    st.subheader(f"📋 매물 상세 브리핑 (총 {len(df_filtered)}건)")

    if "current_idx" not in st.session_state: st.session_state.current_idx = 0
    indices     = df_filtered.index.tolist()
    total_count = len(indices)
    if st.session_state.current_idx >= total_count: st.session_state.current_idx = 0
    cur  = st.session_state.current_idx
    item = df_filtered.loc[indices[cur]]

    # 매물 요약 카드
    st.markdown(f"""
    <div style="background:white; border:1px solid #e2e8f0; border-radius:12px;
                padding:20px; margin-bottom:12px;">
        <div style="font-size:16px; font-weight:700; color:#1e293b; margin-bottom:16px;">
            📍 {item['소재지']}
        </div>
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px,1fr));
                    gap:12px; font-size:14px; color:#475569;
                    border-top:1px solid #f1f5f9; padding-top:14px;">
            <div>🏠 <b>물건종류:</b> {item['소분류']} ({item['상태']})</div>
            <div>📏 <b>공급면적:</b> {item['면적']}</div>
            <div>💰 <b>거래가액:</b> <span style="color:#ef4444;font-weight:700;">{item['가액']}만</span> / 월세 {item['월세']}만</div>
            <div>👤 <b>고객/연락처:</b> {item['고객명']} ({item['연락처']})</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 메모 + 네비게이션
    with st.container(border=True):
        st.markdown("**📜 상세 메모**")
        new_memo = st.text_area("내용 수정", value=item["특약사항"], height=200,
                                key=f"memo_slide_{item.name}", label_visibility="collapsed")

        # 네비게이션: nav-marker CSS 저격으로 모바일 가로 고정
        nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])
        with nav_col1:
            st.markdown("<span class='nav-marker'></span>", unsafe_allow_html=True)
            if st.button("◀", key="btn_nav_prev", use_container_width=True):
                st.session_state.current_idx = (cur - 1) % total_count
                st.rerun()
        with nav_col2:
            st.markdown(f"<div class='nav-counter'>{cur + 1} / {total_count}</div>",
                        unsafe_allow_html=True)
        with nav_col3:
            if st.button("▶", key="btn_nav_next", use_container_width=True):
                st.session_state.current_idx = (cur + 1) % total_count
                st.rerun()

        if st.button("💾 메모 저장하기", key=f"save_slide_{item.name}", use_container_width=True):
            df_all.at[item.name, "특약사항"] = new_memo
            conn.update(data=df_all)
            st.toast("저장 완료!")
            st.rerun()
