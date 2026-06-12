import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(
    page_title="⚽ 공감수학 월드컵 스코어 맞추기",
    page_icon="⚽",
    layout="centered",
    initial_sidebar_state="collapsed",
)

KST = pytz.timezone("Asia/Seoul")

MATCHES = [
    {"id":"g1","title":"한국 vs 체코","sub":"1차전","date":datetime(2026,6,12,11,0,tzinfo=KST),"venue":"에스타디오 아크론","home":"🇰🇷 한국","away":"🇨🇿 체코"},
    {"id":"g2","title":"한국 vs 멕시코","sub":"2차전","date":datetime(2026,6,19,10,0,tzinfo=KST),"venue":"에스타디오 아크론","home":"🇰🇷 한국","away":"🇲🇽 멕시코"},
    {"id":"g3","title":"한국 vs 남아공","sub":"3차전","date":datetime(2026,6,25,10,0,tzinfo=KST),"venue":"구아달로페","home":"🇰🇷 한국","away":"🇿🇦 남아공"},
]

SCHOOLS  = ["선택하세요", "연성초", "연성중", "시흥고", "목감고"]  # ← 학교명 수정
GRADES   = ["선택하세요", "1학년", "2학년", "3학년", "4학년", "5학년", "6학년"]


# ── Google Sheets 연결 ────────────────────────────────────────
@st.cache_resource
def get_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    return gspread.authorize(creds)


def get_worksheet(game_id):
    """워크시트 반환. 없으면 헤더 포함해서 생성."""
    gc = get_client()
    sh = gc.open_by_key("1ZEJvRAwUHgPXiegY4SDTo-ym4pE-52MG4HJib8dHQfs")
    existing = [w.title for w in sh.worksheets()]
    if game_id not in existing:
        ws = sh.add_worksheet(title=game_id, rows=500, cols=10)
        ws.append_row(["game_id","game_title","school","grade","name","home","away","ts"])
        return ws
    return sh.worksheet(game_id)


def load_votes():
    """Google Sheets → session_state.votes"""
    votes = {m["id"]: [] for m in MATCHES}
    try:
        for m in MATCHES:
            ws   = get_worksheet(m["id"])
            rows = ws.get_all_records()
            for row in rows:
                try:
                    votes[m["id"]].append({
                        "school": str(row["school"]),
                        "grade":  str(row["grade"]),
                        "name":   str(row["name"]),
                        "home":   int(row["home"]),
                        "away":   int(row["away"]),
                        "ts":     str(row["ts"]),
                    })
                except Exception:
                    continue
    except Exception as e:
        st.warning(f"데이터 불러오기 실패: {e}")
    return votes


def user_key():
    return f"{st.session_state.school}|{st.session_state.grade}|{st.session_state.uname}"


def save_vote(game_id, home_score, away_score):
    """Google Sheets에 투표 저장 (upsert)"""
    try:
        ws  = get_worksheet(game_id)
        ts  = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
        rows = ws.get_all_records()
        uk   = user_key()
        for i, row in enumerate(rows, start=2):  # 헤더=1행, 데이터=2행부터
            if f"{row['school']}|{row['grade']}|{row['name']}" == uk:
                # 기존 행 업데이트 (F=home, G=away, H=ts)
                ws.update(range_name=f"F{i}:H{i}", values=[[home_score, away_score, ts]])
                return
        # 신규 행 추가
        m_title = next(m["title"] for m in MATCHES if m["id"] == game_id)
        ws.append_row([game_id, m_title,
                       st.session_state.school, st.session_state.grade,
                       st.session_state.uname, home_score, away_score, ts])
    except Exception as e:
        st.error(f"저장 실패: {e}")


def my_vote(game_id):
    uk = user_key()
    for v in st.session_state.votes[game_id]:
        if f"{v['school']}|{v['grade']}|{v['name']}" == uk:
            return v
    return None


def vote_chips(game_id):
    counts = {}
    for v in st.session_state.votes[game_id]:
        k = f"{v['home']}:{v['away']}"
        counts[k] = counts.get(k, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: -x[1]))


# ── 세션 초기화 ───────────────────────────────────────────────
if "votes"      not in st.session_state: st.session_state.votes      = {}
if "logged_in"  not in st.session_state: st.session_state.logged_in  = False
if "school"     not in st.session_state: st.session_state.school     = ""
if "grade"      not in st.session_state: st.session_state.grade      = ""
if "uname"      not in st.session_state: st.session_state.uname      = ""
if "admin_mode" not in st.session_state: st.session_state.admin_mode = False


def is_closed(m):
    return datetime.now(KST) >= m["date"]


# ── CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
.stApp { font-family: 'Noto Sans KR', sans-serif; }
.block-container { padding: 1rem 1rem 4rem !important; max-width: 480px !important; }

.hero {
    background: linear-gradient(135deg, #1a3c8f, #0f2460);
    border-radius: 16px; padding: 20px; margin-bottom: 20px;
    color: white; text-align: center;
}
.hero h1 { font-size: 20px; margin: 0 0 4px; }
.hero p  { font-size: 12px; opacity: 0.8; margin: 0; }

.match-card {
    background: white; border: 1px solid #e8eaf0;
    border-radius: 16px; padding: 16px;
    margin-bottom: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.match-sub   { font-size: 11px; color: #888; margin: 0 0 2px; }
.match-title { font-size: 17px; font-weight: 700; color: #1a1a2e; margin: 0 0 4px; }

.badge-open   { display:inline-block; background:#dcfce7; color:#166534; font-size:11px; padding:2px 9px; border-radius:20px; margin-left:6px; }
.badge-closed { display:inline-block; background:#fee2e2; color:#991b1b; font-size:11px; padding:2px 9px; border-radius:20px; margin-left:6px; }
.badge-done   { display:inline-block; background:#dbeafe; color:#1e40af; font-size:11px; padding:2px 9px; border-radius:20px; margin-left:6px; }

.my-vote-bar {
    background: #eff6ff; border: 1px solid #bfdbfe;
    border-radius: 10px; padding: 8px 12px;
    font-size: 13px; color: #1e40af; margin-bottom: 10px;
    text-align: center;
}
.chips-wrap { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
.chip {
    background: #f1f3f9; border: 1px solid #e0e4f0;
    border-radius: 20px; padding: 6px 14px;
    font-size: 13px; font-weight: 600; color: #333;
    display: flex; align-items: center; gap: 6px;
}
.chip-mine { background: #dbeafe; border-color: #93c5fd; color: #1e40af; }
.chip-cnt  { font-size: 11px; font-weight: 400; color: #888; }
.chip-mine .chip-cnt { color: #60a5fa; }

.stSelectbox > div > div { font-size: 26px !important; font-weight: 800 !important; text-align: center !important; height: 56px !important; color: #1a3c8f !important; }
.stButton > button { border-radius: 12px !important; font-size: 15px !important; font-weight: 600 !important; height: 48px !important; min-height: 48px !important; }
.stTabs [data-baseweb="tab"] { font-size: 15px !important; padding: 10px 16px !important; }
</style>
""", unsafe_allow_html=True)

# ── 히어로 ───────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>⚽ 공감수학 월드컵 스코어 맞추기</h1>
  <p>2026 북중미 월드컵 · 맞추면 음료 한 잔! ☕</p>
</div>
""", unsafe_allow_html=True)

# ── 로그인 ───────────────────────────────────────────────────
if not st.session_state.logged_in:
    st.markdown("#### 참여하기")
    with st.form("login_form"):
        school = st.selectbox("학교", SCHOOLS)
        grade  = st.selectbox("학년", GRADES)
        uname  = st.text_input("이름", placeholder="홍길동")
        if st.form_submit_button("✅ 참여하기", use_container_width=True, type="primary"):
            if school == "선택하세요" or grade == "선택하세요" or not uname.strip():
                st.error("학교, 학년, 이름을 모두 입력해주세요.")
            else:
                st.session_state.school    = school
                st.session_state.grade     = grade
                st.session_state.uname     = uname.strip()
                st.session_state.logged_in = True
                with st.spinner("데이터 불러오는 중..."):
                    st.session_state.votes = load_votes()
                st.rerun()
    st.stop()

# ── 상단 사용자 정보 ──────────────────────────────────────────
cu, cl = st.columns([3, 1])
with cu:
    st.caption(f"👤 {st.session_state.school} {st.session_state.grade} {st.session_state.uname}")
with cl:
    if st.button("로그아웃", use_container_width=True):
        for k in ["logged_in","school","grade","uname","votes","admin_mode"]:
            st.session_state[k] = False if k in ["logged_in","admin_mode"] else ("" if k != "votes" else {})
        st.rerun()

st.divider()

# ── 탭 ───────────────────────────────────────────────────────
tab_vote, tab_result, tab_admin = st.tabs(["📋 예측", "📊 현황", "🔒 관리자"])

# ── 탭1: 예측 ────────────────────────────────────────────────
with tab_vote:
    for m in MATCHES:
        closed = is_closed(m)
        mv     = my_vote(m["id"])

        badge = ('<span class="badge-closed">⛔ 마감</span>' if closed
                 else '<span class="badge-done">✏ 수정 가능</span>' if mv
                 else '<span class="badge-open">✅ 예측 가능</span>')
        date_str = m["date"].strftime("%m/%d %p %I:%M").replace("AM","오전").replace("PM","오후")

        st.markdown(f"""
        <div class="match-card">
          <div class="match-sub">{m["sub"]} · {date_str} · {m["venue"]}</div>
          <div class="match-title">{m["title"]}{badge}</div>
        </div>
        """, unsafe_allow_html=True)

        if mv:
            st.markdown(f'<div class="my-vote-bar">내 예측: {mv["home"]} : {mv["away"]}</div>', unsafe_allow_html=True)

        if not closed:
            prev_h = mv["home"] if mv else 0
            prev_a = mv["away"] if mv else 0
            SCORES = list(range(0, 10))

            c1, c2, c3 = st.columns([5, 1, 5])
            with c1:
                st.markdown(f"<div style='font-size:13px;font-weight:700;margin-bottom:4px'>{m['home']}</div>", unsafe_allow_html=True)
                home_score = st.selectbox("한국", SCORES, index=prev_h,
                                          key=f"h_{m['id']}", label_visibility="collapsed")
            with c2:
                st.markdown("<div style='text-align:center;padding-top:32px;font-size:18px;color:#aaa'>:</div>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<div style='font-size:13px;font-weight:700;margin-bottom:4px'>{m['away']}</div>", unsafe_allow_html=True)
                away_score = st.selectbox("상대", SCORES, index=prev_a,
                                          key=f"a_{m['id']}", label_visibility="collapsed")

            st.markdown("<br>", unsafe_allow_html=True)
            btn_label = f"✏ {home_score} : {away_score} 로 수정" if mv else f"⚽ {home_score} : {away_score} 예측 등록"
            if st.button(btn_label, key=f"submit_{m['id']}", use_container_width=True, type="primary"):
                with st.spinner("저장 중..."):
                    try:
                        save_vote(m["id"], int(home_score), int(away_score))
                        st.session_state.votes = load_votes()
                        st.toast(f"등록 완료! {home_score} : {away_score} 🎉")
                        st.rerun()
                    except Exception as e:
                        st.error(f"오류: {e}")
        else:
            st.warning("예측이 마감됐어요.")

        # 투표 현황 칩
        chips = vote_chips(m["id"])
        total = sum(chips.values())
        if chips:
            st.caption(f"총 {total}명 참여")
            my_key = f"{mv['home']}:{mv['away']}" if mv else None
            chips_html = '<div class="chips-wrap">'
            for score, cnt in chips.items():
                cls = "chip chip-mine" if score == my_key else "chip"
                chips_html += f'<div class="{cls}">{score.replace(":"," : ")} <span class="chip-cnt">{cnt}명{"✓" if score==my_key else ""}</span></div>'
            chips_html += '</div>'
            st.markdown(chips_html, unsafe_allow_html=True)
        else:
            st.caption("아직 예측이 없어요. 첫 번째로 등록해보세요!")

        st.markdown("<br>", unsafe_allow_html=True)

# ── 탭2: 현황 ────────────────────────────────────────────────
with tab_result:
    if st.button("🔄 새로고침", use_container_width=True):
        with st.spinner("불러오는 중..."):
            st.session_state.votes = load_votes()
        st.rerun()

    for m in MATCHES:
        lst = st.session_state.votes.get(m["id"], [])
        st.markdown(f"**{m['title']}** ({m['sub']})")
        if not lst:
            st.caption("아직 예측이 없어요.")
        else:
            rows = [{
                "학교": v["school"],
                "학년": v["grade"],
                "이름": v["name"][0] + "*" * (len(v["name"]) - 1),
                "예측": f"{v['home']} : {v['away']}",
                "시각": v["ts"][5:16],
            } for v in lst]
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        st.divider()

# ── 탭3: 관리자 ──────────────────────────────────────────────
with tab_admin:
    if not st.session_state.admin_mode:
        with st.form("admin_form"):
            pw = st.text_input("관리자 비밀번호", type="password")
            if st.form_submit_button("확인", use_container_width=True, type="primary"):
                if pw == st.secrets.get("ADMIN_PW", "worldcup2026"):
                    st.session_state.admin_mode = True
                    st.rerun()
                else:
                    st.error("비밀번호 오류")
    else:
        st.success("관리자 모드")

        if st.button("🔄 데이터 새로고침", use_container_width=True):
            with st.spinner("불러오는 중..."):
                st.session_state.votes = load_votes()
            st.rerun()

        # 전체 데이터 다운로드
        all_rows = []
        for m in MATCHES:
            for v in st.session_state.votes.get(m["id"], []):
                all_rows.append({
                    "경기": m["title"], "학교": v["school"], "학년": v["grade"],
                    "이름": v["name"], "예측": f"{v['home']}:{v['away']}", "시각": v["ts"],
                })
        if all_rows:
            df_all = pd.DataFrame(all_rows)
            st.download_button(
                "⬇ 전체 데이터 다운로드",
                data=df_all.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                file_name=f"worldcup_{datetime.now(KST).strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        st.divider()
        for m in MATCHES:
            lst = st.session_state.votes.get(m["id"], [])
            st.markdown(f"**{m['title']}**")
            if not lst:
                st.caption("없음")
            else:
                rows = [{"학교":v["school"],"학년":v["grade"],"이름":v["name"],
                         "예측":f"{v['home']}:{v['away']}","시각":v["ts"][5:16]} for v in lst]
                st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
            st.divider()

        if st.button("관리자 로그아웃"):
            st.session_state.admin_mode = False
            st.rerun()
