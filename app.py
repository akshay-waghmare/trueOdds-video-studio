"""TrueOddsML Video Studio — Streamlit UI"""
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import streamlit as st

# Load .env into os.environ before anything else
_ENV_FILE = Path(__file__).parent / ".env"
if _ENV_FILE.exists():
    for _line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

# Allow `from probability_agent import run_agent` without installing as a package
_SCRIPTS = Path(__file__).parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

ROOT            = Path(__file__).parent
INPUT_PATH      = ROOT / "inputs" / "match_prediction.json"
MATCH_DAY_INPUT_PATH = ROOT / "inputs" / "match_day_pack.json"
RENDER_PATH     = ROOT / "renders" / "prematch_prediction.mp4"
SCREENSHOTS_DIR = ROOT / "renders" / "screenshots"
INTELLIGENCE_DIR = ROOT / "data" / "intelligence"
CARDS_DIR       = ROOT / "inputs" / "cards"

TEAMS = ["MI", "KKR", "RCB", "CSK", "SRH", "DC", "PBKS", "RR", "GT", "LSG"]
CITY  = {
    "MI": "Mumbai",    "KKR": "Kolkata",   "RCB": "Bangalore",
    "CSK": "Chennai",  "SRH": "Hyderabad", "DC": "Delhi",
    "PBKS": "Punjab",  "RR": "Rajasthan",  "GT": "Gujarat",
    "LSG": "Lucknow",
}
FULL_NAMES = {
    "MI":   "Mumbai Indians",              "KKR":  "Kolkata Knight Riders",
    "RCB":  "Royal Challengers Bangalore", "CSK":  "Chennai Super Kings",
    "SRH":  "Sunrisers Hyderabad",         "DC":   "Delhi Capitals",
    "PBKS": "Punjab Kings",                "RR":   "Rajasthan Royals",
    "GT":   "Gujarat Titans",              "LSG":  "Lucknow Super Giants",
}
TEAM_HASHTAGS = {
    "MI":   "#MI #MumbaiIndians",                      "KKR":  "#KKR #KolkataKnightRiders",
    "RCB":  "#RCB #RoyalChallengersBangalore",         "CSK":  "#CSK #ChennaiSuperKings",
    "SRH":  "#SRH #SunrisersHyderabad",                "DC":   "#DC #DelhiCapitals",
    "PBKS": "#PBKS #PunjabKings",                      "RR":   "#RR #RajasthanRoyals",
    "GT":   "#GT #GujaratTitans",                      "LSG":  "#LSG #LucknowSuperGiants",
}
TEAM_RE = re.compile(r'\b(MI|KKR|RCB|CSK|SRH|DC|PBKS|RR|GT|LSG)\b')

# ── Helpers ────────────────────────────────────────────────────────────────────
ONES = ['zero','one','two','three','four','five','six','seven','eight','nine',
        'ten','eleven','twelve','thirteen','fourteen','fifteen','sixteen',
        'seventeen','eighteen','nineteen']
TENS = ['','','twenty','thirty','forty','fifty','sixty','seventy','eighty','ninety']

def build_instagram_post(match, pub, pick, prob, reasons, cta):
    pub_full  = FULL_NAMES.get(pub, pub)
    pick_full = FULL_NAMES.get(pick, pick)
    reasons_block = '\n'.join(f"→ {r.strip()}" for r in reasons if r.strip())
    cta_clean = cta.strip().rstrip('.')

    caption = (
        f"The market backs {pub_full}. The data backs {pick_full}. 🧮\n\n"
        f"{pick_full} win probability: {prob}%\n"
        f"{reasons_block}\n\n"
        f"This isn't a prediction. It's probability.\n\n"
        f"🔔 Follow TrueOddsML — model drops before every match.\n"
        f"📲 Telegram for early drops → t.me/trueoddsML"
    )

    match_tag  = '#' + match.strip().replace(' ', '')          # e.g. #GTvsSRH
    team_tags  = f"{TEAM_HASHTAGS.get(pub, '')} {TEAM_HASHTAGS.get(pick, '')}".strip()
    hashtags   = (
        f"{match_tag} {team_tags}\n"
        "#IPL2026 #IPLPrediction #CricketAnalytics #CricketStats\n"
        "#TrueOddsML #DataDrivenCricket #AntiTipster #AntiTipsters\n"
        "#IPLToday #CricketReels #IPLMatch #T20Cricket\n"
        "#WinProbability #MLCricket #CricketML\n\n"
        "📲 Early drops on Telegram → t.me/trueoddsML"
    )

    return caption, hashtags


def build_telegram_post(match, pub, pick, prob, reasons):
    """Same source of truth as the video — guarantees consistent team pick."""
    pick_full = FULL_NAMES.get(pick, pick)
    p = int(prob)
    if p >= 70:
        confidence = "High"
    elif p >= 60:
        confidence = "Medium"
    else:
        confidence = "Low"

    # Primary reason is the first stat-backed reason
    why = reasons[0].strip() if reasons else "Model edge before toss."

    return (
        f"🏏 IPL Pre-match Signal\n\n"
        f"Match: {match}\n"
        f"Phase: Before toss\n"
        f"Model favourite: {pick_full}\n"
        f"Confidence: {confidence} ({p}%)\n\n"
        f"Why: {why}\n\n"
        f"⚠️ Caveat: Toss, confirmed XI, and venue conditions can still move this.\n\n"
        f"Full breakdown → Instagram @trueoddsml"
    )


def num_to_words(n):
    n = int(round(n))
    if n == 100: return "one hundred"
    if n < 20:   return ONES[n]
    if n % 10 == 0: return TENS[n // 10]
    return f"{TENS[n // 10]}-{ONES[n % 10]}"

def sub_teams(text):
    return TEAM_RE.sub(lambda m: CITY.get(m.group(), m.group()), text)

def build_preview(match, pub, pick, prob, reasons, cta):
    match_tts  = sub_teams(re.sub(r'\bvs\b', 'versus', match, flags=re.I))
    reasons_tts = '. '.join(sub_teams(r.strip()) for r in reasons if r.strip())
    sentences  = [s.strip() for s in cta.split('.') if s.strip()]
    cta_line   = '. '.join(sentences[-2:]) + '.' if sentences else ''
    return '\n\n'.join([
        f"The public is backing {CITY.get(pub, pub)}. Our model disagrees.",
        f"{match_tts}. Market makes {CITY.get(pub, pub)} the favourite.",
        f"TrueOddsML picks {CITY.get(pick, pick)}. {num_to_words(prob)} percent probability.",
        f"{reasons_tts}.",
        cta_line,
    ])

def load_json():
    if INPUT_PATH.exists():
        return json.loads(INPUT_PATH.read_text(encoding='utf-8'))
    return {}

def load_json_path(path):
    path = Path(path)
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    return {}

def build_match_day_pack_payload(match, public_team, model_pick, probability, reasons, venue, cta_mode, languages):
    return {
        "schema_version": "1.0.0",
        "match": match.strip(),
        "venue": venue.strip(),
        "public_team": public_team,
        "model_pick": model_pick,
        "probability": int(probability),
        "reasons": [r.strip() for r in reasons if r.strip()],
        "cta_mode": cta_mode,
        "languages": languages,
    }

def team_index(abbr):
    try:    return TEAMS.index(abbr)
    except ValueError: return 0

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="TrueOddsML Studio", page_icon="🏏", layout="wide")
st.title("🏏 TrueOddsML Video Studio")
st.caption("Fill in the match prediction → click Generate → get your 20s reel")

saved = load_json()
reasons_saved = saved.get("reasons", ["", "", ""])

# ── AI Analyse ─────────────────────────────────────────────────────────────────
st.subheader("🤖 AI Match Analyser", anchor=False)
ai_col1, ai_col2, ai_col3 = st.columns([2, 2, 1])

with ai_col1:
    ai_match = st.text_input("Match", value=saved.get("match", "GT vs SRH"),
                             placeholder="e.g. GT vs SRH", key="ai_match_input",
                             label_visibility="collapsed")
with ai_col2:
    ai_venue = st.text_input("Venue (optional)", placeholder="e.g. Ahmedabad",
                             key="ai_venue_input", label_visibility="collapsed")
with ai_col3:
    analyse_clicked = st.button("🤖 Analyse Match", use_container_width=True, type="secondary")

ai_crex = st.text_input(
    "🔗 Crex match-details URL (optional — adds live venue stats & team form)",
    placeholder="https://crex.com/cricket-live-score/.../match-details",
    key="ai_crex_input",
)

if analyse_clicked and ai_match.strip():
    with st.spinner("Mining Cricsheet data + calling AI…"):
        try:
            from probability_agent import run_agent
            result = run_agent(
                ai_match.strip(),
                ai_venue.strip() or None,
                crex_url=ai_crex.strip() or None,
            )
            st.session_state["ai_prefill"] = result
            crex_badge = ""
            if result.get("crex"):
                c = result["crex"]
                bowl_pct = c.get("bowl_first_win_pct")
                crex_badge = f" · 🏟️ Raipur chase wins {bowl_pct}%" if bowl_pct else " · 🏟️ Crex data loaded"
            st.success(
                f"✅ **{result['model_pick']}** wins at **{result['probability']}%** "
                f"· Public backs **{result['public_team']}** · "
                f"{'📊 Cricsheet data' if result['stats_available'] else '🧠 AI-only (no local data)'}"
                f"{crex_badge}"
            )
            if result.get("explanation"):
                st.caption(result["explanation"])
        except Exception as exc:
            st.error(f"Agent error: {exc}")

prefill = st.session_state.get("ai_prefill", {})
if prefill:
    with st.expander("📊 Agent Analysis Details", expanded=False):
        pf_col1, pf_col2 = st.columns(2)
        with pf_col1:
            st.json({
                "model_pick":   prefill.get("model_pick"),
                "public_team":  prefill.get("public_team"),
                "probability":  prefill.get("probability"),
                "reasons":      prefill.get("reasons"),
                "stats_available": prefill.get("stats_available"),
            })
        with pf_col2:
            if prefill.get("stats_available") and prefill.get("stats"):
                st.json(prefill["stats"])
            else:
                st.caption("No Cricsheet stats (AI-only mode)")
            if prefill.get("crex"):
                st.markdown("**🏟️ Crex live data**")
                st.json(prefill["crex"])
    st.info("ℹ️ Form pre-filled from agent analysis. Review and click Generate when ready.")

st.divider()

# ── IPL Intelligence Products ──────────────────────────────────────────────────
st.subheader("📊 IPL Intelligence Products", anchor=False)
st.caption("Build venue/player intelligence, generate a match card, and record the prediction tracker. Fantasy engine is excluded.")

intel_col1, intel_col2, intel_col3 = st.columns([2, 2, 1])
with intel_col1:
    intel_match = st.text_input(
        "Intelligence match",
        value=st.session_state.get("intel_match", ai_match if ai_match else saved.get("match", "GT vs SRH")),
        key="intel_match_input",
    )
with intel_col2:
    intel_venue = st.text_input(
        "Intelligence venue",
        value=st.session_state.get("intel_venue", ai_venue if ai_venue else ""),
        placeholder="e.g. Ahmedabad",
        key="intel_venue_input",
    )
with intel_col3:
    st.write("")
    st.write("")
    build_intel_clicked = st.button("Build data", use_container_width=True)

card_col1, card_col2, card_col3 = st.columns(3)
with card_col1:
    card_clicked = st.button("Generate match card", use_container_width=True, type="secondary")
with card_col2:
    record_clicked = st.button("Record prediction", use_container_width=True)
with card_col3:
    tracker_path = INTELLIGENCE_DIR / "prediction_tracker.json"
    st.caption(f"Tracker: {'ready' if tracker_path.exists() else 'not created'}")

try:
    from ipl_intelligence import build_intelligence, generate_match_card, record_prediction, write_intelligence_artifacts
except Exception as exc:
    build_intelligence = generate_match_card = record_prediction = write_intelligence_artifacts = None
    st.error(f"IPL intelligence module unavailable: {exc}")

if build_intel_clicked:
    if not build_intelligence or not write_intelligence_artifacts:
        st.stop()
    with st.spinner("Building venue and player intelligence from data/ipl_json..."):
        artifacts = build_intelligence()
        written = write_intelligence_artifacts(artifacts)
    st.success("Intelligence artifacts generated.")
    st.json({name: str(path.relative_to(ROOT)) for name, path in written.items()})

if card_clicked:
    if not generate_match_card:
        st.stop()
    if not intel_match.strip():
        st.error("Match is required for match card generation.")
    else:
        with st.spinner("Generating match intelligence card..."):
            card, card_path = generate_match_card(intel_match.strip(), intel_venue.strip() or None)
        st.session_state["last_intelligence_card"] = str(card_path)
        st.success(f"Card generated: {card_path.relative_to(ROOT)}")

last_card_path = Path(st.session_state.get("last_intelligence_card", ""))
if not last_card_path.is_file():
    cards = sorted(CARDS_DIR.glob("match_intelligence_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    last_card_path = cards[0] if cards else Path()

if last_card_path.is_file():
    card = load_json_path(last_card_path)
    with st.expander("Latest Match Intelligence Card", expanded=True):
        summary_cols = st.columns(4)
        summary_cols[0].metric("Pick", card.get("prediction", {}).get("model_pick", "—"))
        summary_cols[1].metric("Probability", f"{card.get('prediction', {}).get('probability', '—')}%")
        summary_cols[2].metric("Expected score", card.get("expected_score", {}).get("first_innings_average", "—"))
        summary_cols[3].metric("Venue", card.get("venue", {}).get("canonical") or "—")
        st.markdown(f"**Venue behaviour:** {card.get('venue_behaviour', '—')}")
        st.markdown(f"**Toss impact:** chase win rate `{card.get('toss_impact', {}).get('historical_second_innings_win_rate')}` · confidence `{card.get('toss_impact', {}).get('confidence')}`")

        player_cols = st.columns(4)
        player_sections = [
            ("Safe", card.get("safe_players", [])),
            ("Risky", card.get("risky_players", [])),
            ("Trump", [card["trump_pick"]] if card.get("trump_pick") else []),
            ("Avoid", [card["avoid_pick"]] if card.get("avoid_pick") else []),
        ]
        for col, (label, players) in zip(player_cols, player_sections):
            with col:
                st.markdown(f"**{label}**")
                if not players:
                    st.caption("No confident signal")
                for player in players:
                    st.caption(f"{player['display_name']} ({player['team']}) — {player['confidence']}")
                    st.write(player.get("reason", ""))
        st.download_button(
            "Download match card JSON",
            json.dumps(card, indent=2).encode("utf-8"),
            file_name=last_card_path.name,
            mime="application/json",
            use_container_width=True,
        )

if record_clicked:
    if not record_prediction:
        st.stop()
    if not last_card_path.is_file():
        st.error("Generate a match card before recording a prediction.")
    else:
        entry, saved_tracker = record_prediction(card_path=last_card_path)
        st.success(f"Prediction recorded: {entry['match_id']}")
        st.caption(str(saved_tracker.relative_to(ROOT)))

tracker = load_json_path(INTELLIGENCE_DIR / "prediction_tracker.json")
pending = [row for row in tracker.get("predictions", []) if row.get("result", {}).get("status") == "pending"]
if pending:
    with st.expander("Prediction Tracker — pending reconciliation", expanded=False):
        for row in pending[-5:]:
            st.write(f"**{row['match_id']}** · pick {row['prediction']['model_pick']} at {row['prediction']['probability']}%")

st.divider()

# ── Form ───────────────────────────────────────────────────────────────────────
# `prefill` from AI agent takes precedence; fall back to saved JSON then hardcoded defaults
_pf_reasons = prefill.get("reasons", reasons_saved)

with st.form("prediction_form"):
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Match")
        match = st.text_input("Match string",
                              value=prefill.get("match", saved.get("match", "MI vs KKR")),
                              placeholder="e.g. MI vs KKR")
        c1, c2 = st.columns(2)
        with c1:
            public_team = st.selectbox("Public favourite", TEAMS,
                                       index=team_index(prefill.get("public_team",
                                                        saved.get("public_team", "MI"))))
        with c2:
            model_pick = st.selectbox("Model pick", TEAMS,
                                      index=team_index(prefill.get("model_pick",
                                                       saved.get("model_pick", "KKR"))))
        probability = st.slider("Win probability (%)", 50, 95,
                                value=int(prefill.get("probability",
                                          saved.get("probability", 62))))

    with col_right:
        st.subheader("Reasons & CTA")
        r1 = st.text_input("Reason 1", value=_pf_reasons[0] if len(_pf_reasons) > 0 else "")
        r2 = st.text_input("Reason 2", value=_pf_reasons[1] if len(_pf_reasons) > 1 else "")
        r3 = st.text_input("Reason 3", value=_pf_reasons[2] if len(_pf_reasons) > 2 else "")
        cta = st.text_area("CTA", value=saved.get("cta", ""), height=90)

    submitted = st.form_submit_button("🎬 Generate Video", type="primary",
                                      use_container_width=True)

# ── Script preview ─────────────────────────────────────────────────────────────
reasons = [r for r in [r1, r2, r3] if r.strip()]
script  = build_preview(match, public_team, model_pick, probability, reasons, cta)
words   = len(script.split())
est_s   = words / 2.3

st.divider()
st.subheader("📝 Voiceover Script Preview")
st.code(script, language=None)
fit = est_s <= 20.5
st.markdown(
    f"**{words} words** · Est. ~{est_s:.1f}s &nbsp; "
    f"{'✅ fits 20s' if fit else '⚠️ may exceed 20s — shorten reasons or CTA'}"
)

# ── Pipeline ───────────────────────────────────────────────────────────────────
if submitted:
    if not match.strip():
        st.error("Match string is required.")
        st.stop()
    if not reasons:
        st.error("At least one reason is required.")
        st.stop()
    if public_team == model_pick:
        st.error("Public favourite and model pick must be different teams.")
        st.stop()

    prediction = {
        "template":    "prematch_prediction",
        "match":       match.strip(),
        "public_team": public_team,
        "model_pick":  model_pick,
        "probability": probability,
        "reasons":     reasons,
        "cta":         cta.strip(),
    }
    INPUT_PATH.write_text(json.dumps(prediction, indent=2), encoding='utf-8')

    st.subheader("⚙️ Pipeline")
    log_box   = st.empty()
    log_lines = []

    with st.spinner("Running pipeline (TTS + render ~60s)…"):
        proc = subprocess.Popen(
            ["node", "scripts/render-prematch.js"],
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        for line in proc.stdout:
            line = line.rstrip()
            if line:
                log_lines.append(line)
                log_box.code('\n'.join(log_lines[-35:]), language=None)
        proc.wait()

    if proc.returncode == 0:
        st.success("✅ Video generated!")

        # Save rendered prediction for Instagram post section
        st.session_state["last_rendered"] = {
            "match": match, "public_team": public_team, "model_pick": model_pick,
            "probability": probability, "reasons": reasons, "cta": cta,
        }

        col_vid, col_shots = st.columns([1, 2])

        with col_vid:
            st.subheader("📹 Video")
            if RENDER_PATH.exists():
                st.video(str(RENDER_PATH))
                size_mb = RENDER_PATH.stat().st_size / 1_048_576
                st.caption(f"{size_mb:.1f} MB · 1080×1920 · H.264")

            thumbnail_path = ROOT / "renders" / "thumbnail.jpg"
            if thumbnail_path.exists():
                st.subheader("🖼️ Thumbnail")
                st.image(str(thumbnail_path), use_container_width=True)
                with open(str(thumbnail_path), "rb") as f:
                    st.download_button("⬇️ Download thumbnail", f, file_name="thumbnail.jpg",
                                       mime="image/jpeg", use_container_width=True)

        with col_shots:
            st.subheader("🖼️ Screenshots")
            shots = sorted(SCREENSHOTS_DIR.glob("*.jpg"))
            if shots:
                cols = st.columns(4)
                for i, shot in enumerate(shots[:8]):
                    with cols[i % 4]:
                        st.image(str(shot), caption=shot.stem.replace("_", " "),
                                 use_container_width=True)
    else:
        st.error(f"❌ Pipeline failed (exit {proc.returncode}) — see log above")

# ── Instagram Post ─────────────────────────────────────────────────────────────
st.divider()
st.subheader("📲 Instagram Post")

# Load from last render if available, else fall back to saved JSON
if "last_rendered" in st.session_state:
    _p = st.session_state["last_rendered"]
else:
    _p = load_json()

_match    = _p.get("match", "")
_pub      = _p.get("public_team", "")
_pick     = _p.get("model_pick", "")
_prob     = _p.get("probability", 0)
_reasons  = _p.get("reasons", [])
_cta      = _p.get("cta", "")

if _match and _pick:
    ig_caption, ig_hashtags = build_instagram_post(_match, _pub, _pick, _prob, _reasons, _cta)

    col_cap, col_hash = st.columns([3, 2])

    with col_cap:
        st.markdown("**📋 Caption** — paste this as your Reel description")
        st.code(ig_caption, language=None)
        st.download_button(
            "⬇️ Download caption.txt", ig_caption.encode(),
            file_name="caption.txt", mime="text/plain", use_container_width=True
        )

    with col_hash:
        st.markdown("**#️⃣ Hashtags** — paste as your first comment")
        st.code(ig_hashtags, language=None)
        st.download_button(
            "⬇️ Download hashtags.txt", ig_hashtags.encode(),
            file_name="hashtags.txt", mime="text/plain", use_container_width=True
        )

        thumbnail_path = ROOT / "renders" / "thumbnail.jpg"
        if thumbnail_path.exists():
            st.markdown("**🖼️ Cover image** — set as Reel cover on upload")
            st.image(str(thumbnail_path), use_container_width=True)
            with open(str(thumbnail_path), "rb") as _f:
                st.download_button(
                    "⬇️ Download cover image", _f, file_name="thumbnail.jpg",
                    mime="image/jpeg", use_container_width=True
                )

    st.markdown("**📌 Posting checklist**")
    st.markdown(
        "1. Upload `prematch_prediction.mp4` as a **Reel** (not a post)\n"
        "2. The cover will auto-load from embedded art — confirm it shows the match card\n"
        "3. Paste the **Caption** above as your Reel description\n"
        "4. After posting, add the **Hashtags** as your **first comment** (keeps caption clean)\n"
        "5. Post **1–2 hours before toss** for max reach (~5:30 PM IST for 7:30 PM matches)\n"
        "6. Pin a comment: *'Get early drops on Telegram → t.me/trueoddsML'*\n"
        "7. After the match: reply to top comments with the actual result 🏆"
    )
else:
    st.info("Fill in the match form above and click **Generate Video** to build your Instagram post.")

# ── Telegram Post ───────────────────────────────────────────────────────────────
st.divider()
st.subheader("✈️ Telegram Signal")
st.caption("Same model source as the video — post this to t.me/trueoddsML before the Reel goes live.")

if _match and _pick:
    tg_post = build_telegram_post(_match, _pub, _pick, _prob, _reasons)

    st.code(tg_post, language=None)

    col_tg1, col_tg2 = st.columns(2)
    with col_tg1:
        st.download_button(
            "⬇️ Download signal.txt", tg_post.encode(),
            file_name="signal.txt", mime="text/plain", use_container_width=True
        )
    with col_tg2:
        st.link_button("📲 Open Telegram channel", "https://t.me/trueoddsML",
                       use_container_width=True)

    st.info(
        f"⚠️ **Consistency check** — both posts use the same pick:\n\n"
        f"Video → **{_pick}** at **{_prob}%** · "
        f"Telegram → **{_pick}** at **{_prob}%**"
    )
else:
    st.info("Run the AI Analyser above to generate the signal.")

# ── Traffic Content Pack ───────────────────────────────────────────────────────
st.divider()
st.subheader("📦 Traffic Content Pack")
st.caption("Scaffold a multi-stage content pack from the current prediction, then add turning-point or proof blocks into the JSON as needed.")

pack_languages = st.multiselect(
    "Languages",
    ["english", "hinglish"],
    default=["english", "hinglish"],
    key="pack_languages",
)
pack_cta_mode = st.selectbox(
    "Single CTA mode",
    ["join_telegram", "follow", "comment_match", "check_live_score"],
    index=0,
    key="pack_cta_mode",
)

pack_col1, pack_col2 = st.columns(2)
with pack_col1:
    if st.button("Scaffold pack JSON", use_container_width=True):
        if not _match or not _pick:
            st.error("Generate or load a prediction first so the pack has a valid match, teams, and probability.")
        else:
            pack_payload = build_match_day_pack_payload(
                _match,
                _pub,
                _pick,
                _prob,
                _reasons,
                intel_venue if 'intel_venue' in locals() else "",
                pack_cta_mode,
                pack_languages or ["english"],
            )
            MATCH_DAY_INPUT_PATH.write_text(json.dumps(pack_payload, indent=2), encoding="utf-8")
            st.success(f"Scaffolded {MATCH_DAY_INPUT_PATH.name}. Add live or proof blocks there when needed.")

with pack_col2:
    if st.button("Build content pack", use_container_width=True, type="secondary"):
        if not MATCH_DAY_INPUT_PATH.exists():
            st.error("Scaffold or create inputs/match_day_pack.json first.")
        else:
            proc = subprocess.run(
                [sys.executable, "scripts/build_match_day_pack.py", "--input", str(MATCH_DAY_INPUT_PATH)],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if proc.returncode != 0:
                st.error(proc.stdout or proc.stderr or "Content pack build failed.")
            else:
                manifest = json.loads(proc.stdout)
                st.session_state["last_pack_manifest"] = manifest
                st.success("Content pack built.")

if MATCH_DAY_INPUT_PATH.exists():
    with st.expander("Current match_day_pack.json", expanded=False):
        st.json(load_json_path(MATCH_DAY_INPUT_PATH))

pack_manifest = st.session_state.get("last_pack_manifest")
if pack_manifest:
    st.markdown("**Pack manifest**")
    st.json(pack_manifest)
    assets = pack_manifest.get("assets", [])
    if assets:
        first_asset = load_json_path(assets[0]["path"])
        if first_asset:
            st.markdown("**First asset preview**")
            st.code(first_asset.get("voiceover", ""), language=None)
            st.code(first_asset.get("caption", ""), language=None)
