import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os

st.set_page_config(
    page_title="⚽ 월드컵 스코어 맞추기",
    page_icon="⚽",
    layout="centered",   # wide 제거 → 모바일 중앙 정렬
    initial_sidebar_state="collapsed",  # 사이드바 기본 접힘
)

KST = pytz.timezone("Asia/Seoul")
CSV_PATH = "votes.csv"

MATCHES = [
    {"id":"g1","title":"한국 vs 체코","sub":"1차전","date":datetime(2026,6,12,11,0,tzinfo=KST),"venue":"에스타디오 아크론","home":"🇰🇷 한국","away":"🇨🇿 체코"},
    {"id":"g2","title":"한국 vs 멕시코","sub":"2차전","date":datetime(2026,6,19,10,0,tzinfo=KST),"venue":"에스타디오 아크론","home":"🇰🇷 한국","away":"🇲🇽 멕시코"},
    {"id":"g3","title":"한국 vs 남아공","sub":"3차전","date":datetime(2026,6,25,10,0,tzinfo=KST),"venue":"구아달로페","home":"🇰🇷 한국","away":"🇿🇦 남아공"},
]

# ── CSV ──────────────────────────────────────────────────────
def load_votes_from_csv():
    votes = {m["id"]: [] for m in MATCHES}
    if not os.path.exists(CSV_PATH):
        return votes
    try:
        df = pd.read_csv(CSV_PATH, dtype=str)
        for _, row in df.iterrows():
            gid = row["game_id"]
            if gid not in votes:
                continue
            votes[gid].append({
                "emp_id": row["emp_id"],
                "name":   row["name"],
                "home":   int(row["home"]),
                "away":   int(row["away"]),
                "ts":     row["ts"],
            })
    except Exception as e:
        st.warning(f"CSV 불러오기 실패: {e}")
    return votes

def save_votes_to_csv():
    rows = []
    for m in MATCHES:
        for v in st.session_state.votes[m["id"]]:
            rows.append({"game_id":m["id"],"game_title":m["title"],
                         "emp_id":v["emp_id"],"name":v["name"],
                         "home":v["home"],"away":v["away"],"ts":v["ts"]})
    pd.DataFrame(rows, columns=["game_id","game_title","emp_id","name","home","away","ts"])\
      .to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

def all_votes_to_df():
    rows = []
    for m in MATCHES:
        for v in st.session_state.votes[m["id"]]:
            rows.append({"경기":m["title"],"사번":v["emp_id"],"이름":v["name"],
                         "예측":f"{v['home']}:{v['away']}","등록":v["ts"]})
    return pd.DataFrame(rows)

# ── 세션 초기화 ───────────────────────────────────────────────
if "votes"      not in st.session_state: st.session_state.votes      = load_votes_from_csv()
if "logged_in"  not in st.session_state: st.session_state.logged_in  = False
if "emp_id"     not in st.session_state: st.session_state.emp_id     = ""
if "emp_name"   not in st.session_state: st.session_state.emp_name   = ""
if "admin_mode" not in st.session_state: st.session_state.admin_mode = False
# 경기별 선택된 스코어 (None = 미선택)
for m in MATCHES:
    if f"sel_{m['id']}" not in st.session_state:
        st.session_state[f"sel_{m['id']}"] = None

# ── 헬퍼 ─────────────────────────────────────────────────────
def is_closed(m):
    return datetime.now(KST) >= m["date"]

def my_vote(game_id):
    for v in st.session_state.votes[game_id]:
        if v["emp_id"] == st.session_state.emp_id:
            return v
    return None

def upsert_vote(game_id, home_score, away_score):
    lst = st.session_state.votes[game_id]
    ts  = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    for i, v in enumerate(lst):
        if v["emp_id"] == st.session_state.emp_id:
            lst[i] = {**v, "home": home_score, "away": away_score, "ts": ts}
            save_votes_to_csv()
            return
    lst.append({"emp_id":st.session_state.emp_id,"name":st.session_state.emp_name,
                "home":home_score,"away":away_score,"ts":ts})
    save_votes_to_csv()

def vote_chips(game_id):
    lst = st.session_state.votes[game_id]
    if not lst:
        return {}
    counts = {}
    for v in lst:
        k = f"{v['home']}:{v['away']}"
        counts[k] = counts.get(k, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: -x[1]))

# ── CSS (모바일 최적화) ────────────────────────────────────────
st.markdown("""
<style>
/* 전체 폰트 & 여백 */
.stApp { font-family: 'Noto Sans KR', sans-serif; }
.block-container { padding: 1rem 1rem 4rem !important; max-width: 480px !important; }

/* 히어로 */
.hero {
    background: linear-gradient(135deg, #1a3c8f, #0f2460);
    border-radius: 16px; padding: 20px 20px 16px;
    margin-bottom: 20px; color: white; text-align: center;
}
.hero h1 { font-size: 20px; margin: 0 0 4px; }
.hero p  { font-size: 12px; opacity: 0.8; margin: 0; }

/* 로그인 카드 */
.login-card {
    background: #f8f9ff; border: 1px solid #e0e4f0;
    border-radius: 16px; padding: 20px; margin-bottom: 20px;
    text-align: center;
}
.login-card p { font-size: 14px; color: #555; margin: 0 0 12px; }

/* 경기 카드 */
.match-card {
    background: white; border: 1px solid #e8eaf0;
    border-radius: 16px; padding: 16px;
    margin-bottom: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.match-sub  { font-size: 11px; color: #888; margin: 0 0 2px; }
.match-title{ font-size: 17px; font-weight: 700; color: #1a1a2e; margin: 0 0 4px; }
.match-meta { font-size: 12px; color: #999; margin: 0 0 14px; }

/* 배지 */
.badge-open   { display:inline-block; background:#dcfce7; color:#166534; font-size:11px; padding:2px 9px; border-radius:20px; margin-left:6px; }
.badge-closed { display:inline-block; background:#fee2e2; color:#991b1b; font-size:11px; padding:2px 9px; border-radius:20px; margin-left:6px; }
.badge-done   { display:inline-block; background:#dbeafe; color:#1e40af; font-size:11px; padding:2px 9px; border-radius:20px; margin-left:6px; }

/* 스코어 선택 그리드 */
.score-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    margin: 12px 0 4px;
}
.score-btn {
    background: #f1f3f9; border: 2px solid #e0e4f0;
    border-radius: 12px; padding: 12px 4px;
    font-size: 16px; font-weight: 700; color: #333;
    text-align: center; cursor: pointer;
    transition: all 0.15s;
}
.score-btn:active { transform: scale(0.95); }
.score-btn-selected {
    background: #1a3c8f; border-color: #1a3c8f;
    color: white;
}
.score-btn-mine {
    background: #dbeafe; border-color: #3b82f6;
    color: #1e40af;
}
.teams-header {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 8px;
}
.team-label { font-size: 14px; font-weight: 700; color: #1a1a2e; }
.selected-score {
    font-size: 28px; font-weight: 800; color: #1a3c8f;
    text-align: center; padding: 4px 0 8px;
}

/* 버튼 공통 */
.stButton > button {
    border-radius: 12px !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    height: 48px !important;
    min-height: 48px !important;
}

/* 투표 칩 */
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

/* 내 예측 표시줄 */
.my-vote-bar {
    background: #eff6ff; border: 1px solid #bfdbfe;
    border-radius: 10px; padding: 8px 12px;
    font-size: 13px; color: #1e40af; margin-bottom: 10px;
    text-align: center;
}

/* 관리자 테이블 스크롤 */
.stDataFrame { font-size: 12px !important; }

/* 탭 글씨 크게 */
.stTabs [data-baseweb="tab"] { font-size: 15px !important; padding: 10px 20px !important; }
</style>
""", unsafe_allow_html=True)

# ── 히어로 배너 ───────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>⚽ 월드컵 스코어 맞추기</h1>
  <p>2026 북중미 월드컵 · 맞추면 커피 한 잔! ☕</p>
</div>
""", unsafe_allow_html=True)

# ── 로그인 (메인 화면, 사이드바 아님) ────────────────────────
if not st.session_state.logged_in:
    st.markdown('<div class="login-card"><p>사번과 이름을 입력하고 참여하세요 👇</p></div>', unsafe_allow_html=True)
    with st.form("login_form"):
        emp_id   = st.text_input("사번", placeholder="예: 202401234")
        emp_name = st.text_input("이름", placeholder="홍길동")
        if st.form_submit_button("✅ 참여하기", use_container_width=True, type="primary"):
            if emp_id.strip() and emp_name.strip():
                st.session_state.emp_id   = emp_id.strip()
                st.session_state.emp_name = emp_name.strip()
                st.session_state.logged_in = True
                # 기존 투표값으로 선택 초기화
                for m in MATCHES:
                    mv = my_vote(m["id"])
                    if mv:
                        st.session_state[f"sel_{m['id']}"] = f"{mv['home']}:{mv['away']}"
                st.rerun()
            else:
                st.error("사번과 이름을 모두 입력해주세요.")
    st.stop()

# ── 로그인 상태 헤더 ─────────────────────────────────────────
col_user, col_logout = st.columns([3, 1])
with col_user:
    st.caption(f"👤 {st.session_state.emp_name} ({st.session_state.emp_id})")
with col_logout:
    if st.button("로그아웃", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.emp_id = st.session_state.emp_name = ""
        st.rerun()

st.divider()

# ── 탭 ────────────────────────────────────────────────────────
tab_vote, tab_result, tab_admin = st.tabs(["📋 예측", "📊 현황", "🔒 관리자"])

# ──────────────────────────────────────────────────────────────
# 탭 1: 경기 예측
# ──────────────────────────────────────────────────────────────
with tab_vote:
    for m in MATCHES:
        closed = is_closed(m)
        mv     = my_vote(m["id"])

        # 배지
        if closed:
            badge = '<span class="badge-closed">⛔ 마감</span>'
        elif mv:
            badge = '<span class="badge-done">✏ 수정 가능</span>'
        else:
            badge = '<span class="badge-open">✅ 예측 가능</span>'

        date_str = m["date"].strftime("%m/%d %p %I:%M").replace("AM","오전").replace("PM","오후")

        st.markdown(f"""
        <div class="match-card">
          <div class="match-sub">{m["sub"]} · {date_str} · {m["venue"]}</div>
          <div class="match-title">{m["title"]}{badge}</div>
        </div>
        """, unsafe_allow_html=True)

        # 내 기존 예측 표시
        if mv:
            st.markdown(f'<div class="my-vote-bar">내 예측: {mv["home"]} : {mv["away"]}</div>', unsafe_allow_html=True)

        if not closed:
            sel_key = f"sel_{m['id']}"
            sel     = st.session_state[sel_key]

            # 자주 나오는 스코어 조합 (한국 기준 승/무/패 섞어서)
            SCORE_OPTIONS = [
                "1:0","2:0","2:1","3:0",
                "3:1","3:2","4:0","4:1",
                "0:0","1:1","2:2","3:3",
                "0:1","0:2","1:2","0:3",
            ]

            # 팀 헤더
            st.markdown(f"""
            <div class="teams-header">
              <span class="team-label">{m["home"]}</span>
              <span style="font-size:12px;color:#aaa">스코어 선택</span>
              <span class="team-label">{m["away"]}</span>
            </div>
            """, unsafe_allow_html=True)

            # 현재 선택 표시
            if sel:
                h, a = sel.split(":")
                st.markdown(f'<div class="selected-score">{h} : {a}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="selected-score" style="color:#ccc">? : ?</div>', unsafe_allow_html=True)

            # 스코어 버튼 그리드 (4열)
            cols_per_row = 4
            for row_i in range(0, len(SCORE_OPTIONS), cols_per_row):
                row_opts = SCORE_OPTIONS[row_i:row_i+cols_per_row]
                btn_cols = st.columns(cols_per_row)
                for col, score in zip(btn_cols, row_opts):
                    h, a = score.split(":")
                    is_sel  = (sel == score)
                    is_prev = (mv and f"{mv['home']}:{mv['away']}" == score and not is_sel)
                    label   = f"{'✓ ' if is_sel else ''}{h}:{a}"
                    btn_type = "primary" if is_sel else "secondary"
                    with col:
                        if st.button(label, key=f"sb_{m['id']}_{score}", use_container_width=True, type=btn_type):
                            st.session_state[sel_key] = score
                            st.rerun()

            # 등록 버튼
            st.markdown("<br>", unsafe_allow_html=True)
            if sel:
                h, a = sel.split(":")
                btn_label = f"✏ {h} : {a} 로 수정" if mv else f"⚽ {h} : {a} 예측 등록"
                if st.button(btn_label, key=f"submit_{m['id']}", use_container_width=True, type="primary"):
                    upsert_vote(m["id"], int(h), int(a))
                    st.toast(f"등록 완료! {h} : {a} 🎉")
                    st.rerun()
            else:
                st.button("위에서 스코어를 선택하세요", key=f"submit_{m['id']}", use_container_width=True, disabled=True)

        else:
            st.warning("예측이 마감됐어요.")

        # 투표 현황 칩
        chips = vote_chips(m["id"])
        total = sum(chips.values())
        if chips:
            st.caption(f"총 {total}명 참여")
            chips_html = '<div class="chips-wrap">'
            my_key = f"{mv['home']}:{mv['away']}" if mv else None
            for score, cnt in chips.items():
                is_mine = (score == my_key)
                cls = "chip chip-mine" if is_mine else "chip"
                chips_html += f'<div class="{cls}">{score.replace(":"," : ")} <span class="chip-cnt">{cnt}명{"✓" if is_mine else ""}</span></div>'
            chips_html += '</div>'
            st.markdown(chips_html, unsafe_allow_html=True)
        else:
            st.caption("아직 예측이 없어요. 첫 번째로 등록해보세요!")

        st.markdown("<br>", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# 탭 2: 전체 현황
# ──────────────────────────────────────────────────────────────
with tab_result:
    for m in MATCHES:
        lst = st.session_state.votes[m["id"]]
        st.markdown(f"**{m['title']}** ({m['sub']})")
        if not lst:
            st.caption("아직 예측이 없어요.")
        else:
            rows = [{
                "이름": v["name"][0] + "*" * (len(v["name"]) - 1),
                "예측": f"{v['home']} : {v['away']}",
                "시각": v["ts"][5:16],  # MM-DD HH:MM
            } for v in lst]
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        st.divider()

# ──────────────────────────────────────────────────────────────
# 탭 3: 관리자
# ──────────────────────────────────────────────────────────────
with tab_admin:
    if not st.session_state.admin_mode:
        with st.form("admin_form"):
            pw = st.text_input("관리자 비밀번호", type="password")
            if st.form_submit_button("확인", use_container_width=True, type="primary"):
                if pw == "worldcup2026":
                    st.session_state.admin_mode = True
                    st.rerun()
                else:
                    st.error("비밀번호 오류")
    else:
        st.success("관리자 모드")

        if st.button("🔄 데이터 새로고침", use_container_width=True):
            st.session_state.votes = load_votes_from_csv()
            st.rerun()

        df_dl = all_votes_to_df()
        if not df_dl.empty:
            st.download_button(
                label="⬇ 전체 데이터 다운로드 (CSV)",
                data=df_dl.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                file_name=f"worldcup_{datetime.now(KST).strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        st.divider()
        for m in MATCHES:
            lst = st.session_state.votes[m["id"]]
            st.markdown(f"**{m['title']}**")
            if not lst:
                st.caption("없음")
            else:
                rows = [{"사번":v["emp_id"],"이름":v["name"],
                         "예측":f"{v['home']}:{v['away']}","시각":v["ts"][5:16]} for v in lst]
                st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
            st.divider()

        if st.button("로그아웃", key="admin_logout"):
            st.session_state.admin_mode = False
            st.rerun()
