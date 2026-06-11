import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

st.set_page_config(page_title="⚽ 월드컵 스코어 맞추기", page_icon="⚽", layout="wide")

KST = pytz.timezone("Asia/Seoul")

MATCHES = [
    {
        "id": "g1",
        "title": "한국 vs 체코 (1차전)",
        "date": datetime(2026, 6, 12, 11, 0, tzinfo=KST),
        "venue": "에스타디오 아크론",
        "home": "🇰🇷 한국",
        "away": "🇨🇿 체코",
    },
    {
        "id": "g2",
        "title": "한국 vs 멕시코 (2차전)",
        "date": datetime(2026, 6, 19, 10, 0, tzinfo=KST),
        "venue": "에스타디오 아크론",
        "home": "🇰🇷 한국",
        "away": "🇲🇽 멕시코",
    },
    {
        "id": "g3",
        "title": "한국 vs 남아공 (3차전)",
        "date": datetime(2026, 6, 25, 10, 0, tzinfo=KST),
        "venue": "구아달로페",
        "home": "🇰🇷 한국",
        "away": "🇿🇦 남아공",
    },
]

# ── 세션 상태 초기화 ──────────────────────────────────────────
if "votes" not in st.session_state:
    # votes: { game_id: [ {"emp_id":…,"name":…,"home":…,"away":…,"ts":…}, … ] }
    st.session_state.votes = {m["id"]: [] for m in MATCHES}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "emp_id" not in st.session_state:
    st.session_state.emp_id = ""

if "emp_name" not in st.session_state:
    st.session_state.emp_name = ""

if "admin_mode" not in st.session_state:
    st.session_state.admin_mode = False


# ── 헬퍼 ─────────────────────────────────────────────────────
def is_closed(match):
    now = datetime.now(KST)
    cutoff = match["date"].replace(tzinfo=KST) if match["date"].tzinfo is None else match["date"]
    return now >= cutoff  # 경기 시작 시각 이후 마감 (필요시 timedelta(minutes=-5) 조정)


def my_vote(game_id):
    for v in st.session_state.votes[game_id]:
        if v["emp_id"] == st.session_state.emp_id:
            return v
    return None


def upsert_vote(game_id, home_score, away_score):
    lst = st.session_state.votes[game_id]
    ts = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    for i, v in enumerate(lst):
        if v["emp_id"] == st.session_state.emp_id:
            lst[i] = {**v, "home": home_score, "away": away_score, "ts": ts}
            return
    lst.append({
        "emp_id": st.session_state.emp_id,
        "name": st.session_state.emp_name,
        "home": home_score,
        "away": away_score,
        "ts": ts,
    })


def vote_summary(game_id):
    """스코어별 투표 수 집계 → DataFrame"""
    lst = st.session_state.votes[game_id]
    if not lst:
        return pd.DataFrame(columns=["스코어", "투표수"])
    counts = {}
    for v in lst:
        key = f"{v['home']} : {v['away']}"
        counts[key] = counts.get(key, 0) + 1
    df = pd.DataFrame(sorted(counts.items(), key=lambda x: -x[1]), columns=["스코어", "투표수"])
    return df


# ── CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { font-family: 'Noto Sans KR', sans-serif; }
    .hero-banner {
        background: linear-gradient(135deg, #1a3c8f 0%, #0f2460 100%);
        border-radius: 14px;
        padding: 24px 32px;
        margin-bottom: 28px;
        color: white;
    }
    .hero-banner h1 { font-size: 26px; margin: 0 0 4px; }
    .hero-banner p  { font-size: 14px; opacity: 0.8; margin: 0; }
    .match-header-label {
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .closed-badge {
        display: inline-block;
        background: #fee2e2;
        color: #991b1b;
        font-size: 12px;
        padding: 2px 10px;
        border-radius: 20px;
        margin-left: 8px;
    }
    .open-badge {
        display: inline-block;
        background: #dcfce7;
        color: #166534;
        font-size: 12px;
        padding: 2px 10px;
        border-radius: 20px;
        margin-left: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ── 히어로 배너 ───────────────────────────────────────────────
st.markdown("""
<div class="hero-banner">
  <h1>⚽ 2026 월드컵 스코어 맞추기</h1>
  <p>🏆 경기 시작 전까지 예측 등록/수정 가능 &nbsp;·&nbsp; 🎉 맞추면 커피 한 잔!</p>
</div>
""", unsafe_allow_html=True)


# ── 로그인 사이드바 ───────────────────────────────────────────
with st.sidebar:
    st.header("👤 내 정보")

    if not st.session_state.logged_in:
        with st.form("login_form"):
            emp_id = st.text_input("사번", placeholder="예: 202401234")
            emp_name = st.text_input("이름", placeholder="홍길동")
            submitted = st.form_submit_button("로그인", use_container_width=True)
            if submitted:
                if emp_id.strip() and emp_name.strip():
                    st.session_state.emp_id = emp_id.strip()
                    st.session_state.emp_name = emp_name.strip()
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("사번과 이름을 모두 입력해주세요.")
    else:
        st.success(f"**{st.session_state.emp_name}** ({st.session_state.emp_id})")
        if st.button("로그아웃", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.emp_id = ""
            st.session_state.emp_name = ""
            st.rerun()

    st.divider()

    # 관리자 패널
    with st.expander("🔒 관리자"):
        pw = st.text_input("관리자 비밀번호", type="password", key="admin_pw")
        if st.button("확인"):
            if pw == "worldcup2026":   # ← 비밀번호 변경
                st.session_state.admin_mode = True
                st.success("관리자 모드 활성화")
            else:
                st.error("비밀번호 오류")


# ── 탭 구성 ──────────────────────────────────────────────────
tab_matches, tab_results = st.tabs(["📋 경기 예측", "📊 전체 현황"])


# ──────────────────────────────────────────────────────────────
# 탭 1 : 경기 예측
# ──────────────────────────────────────────────────────────────
with tab_matches:
    if not st.session_state.logged_in:
        st.info("왼쪽 사이드바에서 사번과 이름을 입력하면 예측에 참여할 수 있어요!")

    for m in MATCHES:
        closed = is_closed(m)
        mv = my_vote(m["id"]) if st.session_state.logged_in else None
        badge = '<span class="closed-badge">⛔ 마감</span>' if closed else '<span class="open-badge">✅ 예측 가능</span>'

        st.markdown(f"""
        <div class="match-header-label">
            {m["title"]} {badge}
        </div>
        <p style="color:#666;font-size:13px;margin-top:0">
            🕐 {m["date"].strftime("%Y. %m. %d. (%a) %p %I:%M").replace("AM","오전").replace("PM","오후")}
            &nbsp;·&nbsp; 📍 {m["venue"]}
        </p>
        """, unsafe_allow_html=True)

        col_form, col_dist = st.columns([1, 1], gap="large")

        # 왼쪽: 스코어 입력
        with col_form:
            if st.session_state.logged_in and not closed:
                with st.form(key=f"form_{m['id']}"):
                    c1, c2, c3 = st.columns([2, 1, 2])
                    with c1:
                        st.markdown(f"**{m['home']}**")
                        home_score = st.number_input(
                            "득점", min_value=0, max_value=20,
                            value=mv["home"] if mv else 2,
                            key=f"h_{m['id']}", label_visibility="collapsed"
                        )
                    with c2:
                        st.markdown("<div style='text-align:center;padding-top:32px;font-size:20px;color:#888'>vs</div>", unsafe_allow_html=True)
                    with c3:
                        st.markdown(f"**{m['away']}**")
                        away_score = st.number_input(
                            "득점", min_value=0, max_value=20,
                            value=mv["away"] if mv else 1,
                            key=f"a_{m['id']}", label_visibility="collapsed"
                        )

                    if mv:
                        st.caption(f"내 예측: **{mv['home']} : {mv['away']}** ({mv['ts']} 등록)")

                    btn_label = "✏ 수정하기" if mv else "⚽ 예측 등록"
                    if st.form_submit_button(btn_label, use_container_width=True, type="primary"):
                        upsert_vote(m["id"], int(home_score), int(away_score))
                        st.toast(f"예측 완료! {int(home_score)} : {int(away_score)} 🎉")
                        st.rerun()

            elif closed:
                st.warning("이 경기는 예측이 마감됐어요.")
                if mv:
                    st.info(f"내 예측: **{mv['home']} : {mv['away']}**")
            else:
                st.info("로그인 후 예측할 수 있어요.")

        # 오른쪽: 투표 분포
        with col_dist:
            df = vote_summary(m["id"])
            total = len(st.session_state.votes[m["id"]])
            st.caption(f"총 {total}명 투표")
            if df.empty:
                st.caption("아직 예측이 없어요.")
            else:
                st.dataframe(
                    df,
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "스코어": st.column_config.TextColumn("스코어", width="small"),
                        "투표수": st.column_config.ProgressColumn(
                            "투표수", min_value=0, max_value=total, format="%d명"
                        ),
                    }
                )

        st.divider()


# ──────────────────────────────────────────────────────────────
# 탭 2 : 전체 현황 (관리자 or 전체 공개)
# ──────────────────────────────────────────────────────────────
with tab_results:
    st.subheader("전체 예측 현황")

    for m in MATCHES:
        lst = st.session_state.votes[m["id"]]
        st.markdown(f"#### {m['title']}")
        if not lst:
            st.caption("아직 예측이 없어요.")
        else:
            rows = []
            for v in lst:
                rows.append({
                    "사번": v["emp_id"] if st.session_state.admin_mode else v["emp_id"][:4] + "***",
                    "이름": v["name"] if st.session_state.admin_mode else v["name"][0] + "*" * (len(v["name"]) - 1),
                    "예측 스코어": f"{v['home']} : {v['away']}",
                    "등록 시각": v["ts"],
                })
            df_all = pd.DataFrame(rows)
            st.dataframe(df_all, hide_index=True, use_container_width=True)

        st.divider()

    if not st.session_state.admin_mode:
        st.caption("💡 사번/이름 전체 열람은 관리자 모드에서 가능합니다.")
