"""
TrueOddsML Probability Agent

Mines Cricsheet IPL data, applies a blended historical win-rate formula in
Python, then calls the GitHub Copilot SDK (no API key — just `gh auth login`)
to generate the narrative: public favourite, model pick, and 3 short reasons.

Probability model: weighted average of three win-rate signals
  (overall IPL record × 0.35) + (H2H record × 0.35) + (venue H2H × 0.30)
  — NOT the Bradley-Terry pairwise strength model.
  See compute_probability() for full details.

Fallback chain:
  1. GitHub Copilot SDK  (no API key, needs `gh auth login`)
  2. GitHub Models       (free tier, needs GITHUB_TOKEN in .env)

CLI usage:
  python scripts/probability_agent.py "GT vs SRH" --venue "Ahmedabad"

Importable usage (from app.py):
  from scripts.probability_agent import run_agent
  result = run_agent("GT vs SRH", venue="Ahmedabad")

Output schema:
  {
    "match":        "GT vs SRH",
    "model_pick":   "GT",
    "public_team":  "SRH",
    "probability":  63,
    "reasons":      ["...", "...", "..."],
    "explanation":  "one sentence",
    "stats":        { ... raw stats ... },
    "stats_available": true
  }
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import threading
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
load_dotenv(Path(__file__).parent.parent / ".env", override=False)

# ── Paths ─────────────────────────────────────────────────────────────────────

CRICSHEET_PATH = Path(
    os.getenv(
        "CRICSHEET_IPL_PATH",
        r"C:\Users\ADMINS\Documents\projects\machine_learning_bbl_009-odi-mc-predictor\ipl_json",
    )
)

# ── Team mappings ──────────────────────────────────────────────────────────────

FULL_NAMES: dict[str, str] = {
    "MI":   "Mumbai Indians",
    "KKR":  "Kolkata Knight Riders",
    "RCB":  "Royal Challengers Bangalore",
    "CSK":  "Chennai Super Kings",
    "SRH":  "Sunrisers Hyderabad",
    "DC":   "Delhi Capitals",
    "PBKS": "Punjab Kings",
    "RR":   "Rajasthan Royals",
    "GT":   "Gujarat Titans",
    "LSG":  "Lucknow Super Giants",
}
ABBR: dict[str, str] = {v: k for k, v in FULL_NAMES.items()}

# Alternate Cricsheet names → abbreviation (or None for defunct teams)
ALIASES: dict[str, str | None] = {
    "Royal Challengers Bengaluru":  "RCB",
    "Delhi Daredevils":             "DC",
    "Kings XI Punjab":              "PBKS",
    "Deccan Chargers":              "SRH",
    "Rising Pune Supergiants":      None,
    "Rising Pune Supergiant":       None,
    "Pune Warriors":                None,
    "Kochi Tuskers Kerala":         None,
    "Gujarat Lions":                None,
}

# Default home venue keywords per team (used when venue not specified)
HOME_VENUES: dict[str, list[str]] = {
    "GT":   ["Narendra Modi", "Ahmedabad", "Motera"],
    "MI":   ["Wankhede", "Mumbai"],
    "KKR":  ["Eden Gardens", "Kolkata"],
    "RCB":  ["Chinnaswamy", "Bengaluru", "Bangalore"],
    "CSK":  ["Chepauk", "Chennai", "MA Chidambaram"],
    "SRH":  ["Rajiv Gandhi", "Uppal", "Hyderabad"],
    "DC":   ["Feroz Shah Kotla", "Arun Jaitley", "Delhi"],
    "PBKS": ["PCA", "Mohali", "Punjab"],
    "RR":   ["Sawai Mansingh", "Jaipur"],
    "LSG":  ["BRSABV", "Ekana", "Lucknow"],
}

# ── Parsing ────────────────────────────────────────────────────────────────────

def parse_match(match_str: str) -> tuple[str, str] | None:
    """Parse 'GT vs SRH' → ('GT', 'SRH'). Returns None on failure."""
    m = re.match(r"(\w+)\s+vs?\s+(\w+)", match_str.strip(), re.I)
    if not m:
        return None
    t1, t2 = m.group(1).upper(), m.group(2).upper()
    if t1 not in FULL_NAMES or t2 not in FULL_NAMES:
        return None
    return t1, t2

# ── Cricsheet mining ───────────────────────────────────────────────────────────

def mine_cricsheet(abbr1: str, abbr2: str, venue_keywords: list[str]) -> dict:
    """Single-pass mine of Cricsheet IPL JSON for overall, H2H, and venue stats."""
    full1 = FULL_NAMES[abbr1]
    full2 = FULL_NAMES[abbr2]

    t1_played = t1_won = 0
    t2_played = t2_won = 0
    h2h_t1 = h2h_t2 = h2h_total = 0
    venue_t1 = venue_t2 = venue_total = 0

    if not CRICSHEET_PATH.exists():
        return {}

    for fpath in sorted(CRICSHEET_PATH.glob("*.json")):
        try:
            data = json.loads(fpath.read_bytes())
            info = data.get("info", {})
            teams: list[str] = info.get("teams", [])
            winner: str = info.get("outcome", {}).get("winner", "")
            venue: str = info.get("venue", "")

            if len(teams) != 2:
                continue

            t1_in = full1 in teams
            t2_in = full2 in teams

            if t1_in:
                t1_played += 1
                if winner == full1:
                    t1_won += 1

            if t2_in:
                t2_played += 1
                if winner == full2:
                    t2_won += 1

            if t1_in and t2_in:
                h2h_total += 1
                if winner == full1:
                    h2h_t1 += 1
                elif winner == full2:
                    h2h_t2 += 1

                if venue_keywords and any(kw.lower() in venue.lower() for kw in venue_keywords):
                    venue_total += 1
                    if winner == full1:
                        venue_t1 += 1
                    elif winner == full2:
                        venue_t2 += 1

        except Exception:
            continue

    return {
        "overall": {
            "team1_played": t1_played, "team1_wins": t1_won,
            "team2_played": t2_played, "team2_wins": t2_won,
        },
        "h2h":   {"total": h2h_total, "team1_wins": h2h_t1, "team2_wins": h2h_t2},
        "venue": {"keywords": venue_keywords, "total": venue_total,
                  "team1_wins": venue_t1, "team2_wins": venue_t2},
    }

# ── Probability formula (pure Python — no AI needed for the math) ──────────────

def compute_probability(stats: dict) -> tuple[int, str]:
    """
    Blended historical win-rate model.

    Combines three independent win-rate signals, each measured over a different
    scope of matches:

      • overall_wr  — team1's share of wins against ALL IPL teams
                      (large sample, low specificity)
      • h2h_wr      — team1's share of wins specifically against team2
                      (high specificity, smaller sample)
      • venue_wr    — team1's share of H2H wins AT THIS VENUE
                      (most specific, often very small sample)

    Formula (when ≥ 3 venue H2H games exist):
        prob = overall_wr × 0.35 + h2h_wr × 0.35 + venue_wr × 0.30

    When venue data is sparse (< 3 games), venue is dropped and weights rebalance:
        prob = overall_wr × 0.50 + h2h_wr × 0.50

    Result is clamped to [50%, 85%] — we never predict a near-certainty.

    Note: this is NOT the Bradley-Terry pairwise strength model (which fits latent
    strength ratings via MLE across the full match graph). This is a simpler,
    interpretable weighted average that works well for a ~6-game H2H sample size.

    Returns (probability_pct_for_team1, human_readable_method_string).
    """
    ov = stats.get("overall", {})
    h2h = stats.get("h2h", {})
    vn = stats.get("venue", {})

    t1_wins = ov.get("team1_wins", 0)
    t2_wins = ov.get("team2_wins", 0)
    combined_total = t1_wins + t2_wins
    overall_wr = t1_wins / combined_total if combined_total > 0 else 0.5

    h2h_total = h2h.get("total", 0)
    h2h_wr = h2h.get("team1_wins", 0) / h2h_total if h2h_total > 0 else 0.5

    vn_total = vn.get("total", 0)
    venue_wr = vn.get("team1_wins", 0) / vn_total if vn_total > 0 else 0.5

    if vn_total >= 3:
        prob = overall_wr * 0.35 + h2h_wr * 0.35 + venue_wr * 0.30
        method = f"35% overall ({overall_wr:.0%}) + 35% H2H ({h2h_wr:.0%}) + 30% venue ({venue_wr:.0%})"
    else:
        prob = overall_wr * 0.50 + h2h_wr * 0.50
        method = f"50% overall ({overall_wr:.0%}) + 50% H2H ({h2h_wr:.0%}) — venue sparse (<3 games)"

    prob = max(0.50, min(0.85, prob))
    return round(prob * 100), method

# ── Copilot SDK client (minimal, no tools needed) ─────────────────────────────

_SYSTEM = """You are TrueOddsML's IPL narrative analyst.

The probability has already been computed mathematically from real Cricsheet data. Your job is to:
1. Identify the PUBLIC TEAM — the team that casual fans, media, and bookmakers overrate.
   Usually: bigger brand (MI, CSK, RCB, KKR), recent IPL fame, or star-power hype.
2. Confirm MODEL PICK — the team the data supports (given as computed_probability for team1).
3. Write exactly 3 reasons for the model pick. MAX 6 WORDS EACH — these are read aloud
   by a TTS voice; shorter reasons sound cleaner and punch harder. Must cite ACTUAL NUMBERS
   from the statistics provided (wins, games, percentages). NEVER write generic phrases
   like "strong batting lineup" or "star players". Every reason must reference a specific
   stat from the data above. Example of good format: "RR leads H2H five to three."
4. Write one explanation sentence summarising the statistical edge.

Respond with ONLY valid JSON, no markdown:
{
  "model_pick":   "ABBR",
  "public_team":  "ABBR",
  "reasons":      ["reason 1", "reason 2", "reason 3"],
  "explanation":  "One sentence."
}"""


class _CopilotClient:
    """Minimal Copilot SDK wrapper. Mirrors conversational-agent/ai/client.py."""

    def __init__(self, model: str = "claude-haiku-4.5") -> None:
        try:
            import copilot as sdk
            self._sdk = sdk
        except ImportError as exc:
            raise ImportError(
                "GitHub Copilot SDK not installed.\n"
                "Run: pip install \"git+https://github.com/github/copilot-sdk.git"
                "#subdirectory=python\"\n"
                "Then: gh auth login"
            ) from exc

        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._loop.run_forever, daemon=True, name="copilot-prob-loop"
        )
        self._thread.start()
        self._sdk_client = None
        self._session = None
        self._run(self._start(model))

    def _run(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result(timeout=120)

    async def _start(self, model: str) -> None:
        self._sdk_client = self._sdk.CopilotClient()
        await self._sdk_client.start()
        self._session = await self._sdk_client.create_session({"model": model})

    async def _stop(self) -> None:
        for obj in (self._session, self._sdk_client):
            if obj:
                try:
                    await obj.destroy() if hasattr(obj, "destroy") else await obj.stop()
                except Exception:
                    pass

    async def _ask(self, prompt: str) -> str:
        event = await self._session.send_and_wait({"prompt": prompt}, timeout=120.0)
        return getattr(event.data, "content", "") if event else ""

    def generate(self, system: str, user: str) -> str:
        prompt = f"[SYSTEM]: {system}\n\n[USER]: {user}"
        return self._run(self._ask(prompt))

    def stop(self) -> None:
        try:
            self._run(self._stop())
        except Exception:
            pass
        self._loop.call_soon_threadsafe(self._loop.stop)


def _github_models_generate(system: str, user: str) -> str:
    """Fallback: GitHub Models (free tier via GITHUB_TOKEN)."""
    import openai
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("No GITHUB_TOKEN and Copilot SDK unavailable. Run `gh auth login`.")
    client = openai.OpenAI(base_url="https://models.inference.ai.azure.com", api_key=token)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.3,
    )
    return resp.choices[0].message.content


def _call_ai(system: str, user: str) -> str:
    """Try Copilot SDK, fall back to GitHub Models on any failure."""
    try:
        c = _CopilotClient()
        try:
            return c.generate(system, user)
        finally:
            c.stop()
    except Exception as sdk_err:
        print(f"[probability_agent] Copilot SDK unavailable ({sdk_err}), using GitHub Models fallback.", file=sys.stderr)
        return _github_models_generate(system, user)


# ── Crex live scraper ──────────────────────────────────────────────────────────

def scrape_crex_match_details(url: str) -> dict:
    """
    Scrape key pre-match stats from a Crex match-details page.

    Returns a dict with:
      venue_name, bat_first_win_pct, bowl_first_win_pct,
      venue_matches, avg_first_innings, avg_second_innings,
      team1_form, team2_form (list of 'W'/'L', oldest→newest),
      weather_desc, temperature, rain_chance_pct
    Returns empty dict on any failure (non-blocking).
    """
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"[crex] Could not fetch {url}: {e}", file=sys.stderr)
        return {}

    result: dict = {}

    def _find(pattern, default=None):
        m = re.search(pattern, html, re.S | re.I)
        return m.group(1).strip() if m else default

    # Venue name — first instance of a known stadium keyword
    vn = _find(r'((?:Shaheed|Narendra|Wankhede|Eden Gardens|Chepauk|Chinnaswamy|'
               r'Rajiv Gandhi|Feroz Shah|PCA|Sawai|Ekana|BRSABV)[^"<]{0,80})')
    if vn:
        result["venue_name"] = re.sub(r'\s+', ' ', vn).strip(', ')

    # Venue match count: e.g.  7</div><div ...>Matches</div>
    m_matches = re.search(r'(\d+)</div>\s*<div[^>]+>\s*Matches\s*</div>', html, re.S)
    if m_matches:
        result["venue_matches"] = int(m_matches.group(1))

    # Bat/bowl first win %  (value lives in next span after label)
    m_bat = re.search(r'Win Bat first</span><span[^>]+>(\d+)%', html)
    m_bowl = re.search(r'Win Bowl first</span><span[^>]+>(\d+)%', html)
    if m_bat:  result["bat_first_win_pct"]  = int(m_bat.group(1))
    if m_bowl: result["bowl_first_win_pct"] = int(m_bowl.group(1))

    # Avg innings scores
    m_avg1 = re.search(r'Avg 1st Inns</span><span[^>]+>(\d+)', html)
    m_avg2 = re.search(r'Avg 2[ns]t Inns</span><span[^>]+>(\d+)', html)
    if m_avg1: result["avg_first_innings"]  = int(m_avg1.group(1))
    if m_avg2: result["avg_second_innings"] = int(m_avg2.group(1))

    # Team form — find all class="win/loss match" entries, group by proximity
    # Entries within the same team's form block are ~100-150 chars apart;
    # H2H match entries are ~1500+ chars apart.
    form_entries = [
        (m.start(), "W" if "win match" in m.group() else "L")
        for m in re.finditer(r'class="(win|loss) match"', html)
    ]
    form_blocks: list[list[str]] = []
    current_block: list[str] = []
    prev_pos = 0
    for pos, val in form_entries:
        if current_block and pos - prev_pos > 500:
            form_blocks.append(current_block)
            current_block = []
        current_block.append(val)
        prev_pos = pos
    if current_block:
        form_blocks.append(current_block)

    # Keep only genuine form blocks (≥3 entries); lone H2H entries are single-item blocks
    form_blocks = [b for b in form_blocks if len(b) >= 3]

    if len(form_blocks) >= 1: result["team1_form"] = form_blocks[0][:5]
    if len(form_blocks) >= 2: result["team2_form"] = form_blocks[1][:5]

    # Weather
    m_temp = re.search(r'([\d.]+)\s*[˚°]C', html)
    if m_temp: result["temperature"] = float(m_temp.group(1))
    m_rain = re.search(r'(\d+)\s*%\s*Chance', html, re.I)
    if m_rain: result["rain_chance_pct"] = int(m_rain.group(1))
    m_weather = re.search(r'(Mostly sunny|Sunny|Overcast|Cloudy|Partly cloudy|Rain|Drizzle)', html, re.I)
    if m_weather: result["weather_desc"] = m_weather.group(1).strip()

    return result


def _crex_prompt_section(crex: dict, abbr1: str, abbr2: str) -> str:
    """Build the Crex stats block to inject into the AI prompt."""
    if not crex:
        return ""
    lines = ["\n=== LIVE VENUE & FORM DATA (Crex) ==="]

    vn = crex.get("venue_name", "Venue")
    nm = crex.get("venue_matches")
    if nm:
        lines.append(f"Venue: {vn} ({nm} IPL matches on record)")

    bat  = crex.get("bat_first_win_pct")
    bowl = crex.get("bowl_first_win_pct")
    if bat is not None and bowl is not None:
        lines.append(f"Pitch: bat-first wins {bat}%  |  bowl-first (chase) wins {bowl}%")
        if bowl > bat:
            lines.append(f"  → Chase-friendly ground — TOSS IS CRITICAL")
        else:
            lines.append(f"  → Batting-first ground — first innings score matters")

    a1 = crex.get("avg_first_innings")
    a2 = crex.get("avg_second_innings")
    if a1: lines.append(f"Avg 1st innings: {a1}  |  Avg 2nd innings: {a2 or '?'}")

    f1 = crex.get("team1_form")
    f2 = crex.get("team2_form")
    if f1: lines.append(f"{abbr1} last-5 form: {' '.join(f1)}  ({f1.count('W')}W {f1.count('L')}L)")
    if f2: lines.append(f"{abbr2} last-5 form: {' '.join(f2)}  ({f2.count('W')} W {f2.count('L')}L)")

    temp = crex.get("temperature")
    rain = crex.get("rain_chance_pct")
    if temp: lines.append(f"Weather: {crex.get('weather_desc','?')} {temp}°C · Rain {rain}% chance")

    lines.append("\nUse this venue and form data when writing reasons — cite specific numbers.")
    return "\n".join(lines)


# ── Main agent ─────────────────────────────────────────────────────────────────

def run_agent(match_str: str, venue: str | None = None, crex_url: str | None = None) -> dict:
    """
    Full pipeline: parse → mine → compute → AI narrative → return dict.

    Args:
        match_str: e.g. "GT vs SRH"
        venue:     e.g. "Ahmedabad" (optional — inferred from home team if omitted)
        crex_url:  Crex match-details URL for live venue/form data (optional)

    Returns dict with keys: match, model_pick, public_team, probability, reasons,
                            explanation, stats, stats_available, crex
    """
    parsed = parse_match(match_str)
    if not parsed:
        raise ValueError(f"Cannot parse '{match_str}'. Use format 'GT vs SRH'.")

    abbr1, abbr2 = parsed
    full1, full2  = FULL_NAMES[abbr1], FULL_NAMES[abbr2]

    # Venue keywords
    if venue:
        venue_kws = [w.strip() for w in re.split(r"[\s,]+", venue) if len(w.strip()) > 2]
    else:
        venue_kws = HOME_VENUES.get(abbr1, [])

    # Step 0: Scrape Crex live data (non-blocking — failures are silently ignored)
    crex = scrape_crex_match_details(crex_url) if crex_url else {}
    if crex:
        print(f"[crex] Fetched live data: {list(crex.keys())}", file=sys.stderr)

    # Step 1: Mine stats
    stats = mine_cricsheet(abbr1, abbr2, venue_kws)
    stats_available = bool(stats)

    # Step 2: Compute probability (Python, not AI)
    if stats_available:
        prob_pct, method = compute_probability(stats)
        model_pick_from_formula = abbr1 if prob_pct >= 50 else abbr2
        if prob_pct < 50:
            prob_pct = 100 - prob_pct  # flip to winner's perspective

        ov = stats["overall"]
        h = stats["h2h"]
        vn = stats["venue"]

        user_prompt = f"""Match: {full1} ({abbr1}) vs {full2} ({abbr2})
Venue: {', '.join(venue_kws) or 'unknown'}

=== COMPUTED STATISTICS (Cricsheet IPL) ===
Overall IPL win rate:
  {full1}: {ov['team1_wins']}/{ov['team1_played']} games ({ov['team1_wins']/max(ov['team1_played'],1)*100:.1f}%)
  {full2}: {ov['team2_wins']}/{ov['team2_played']} games ({ov['team2_wins']/max(ov['team2_played'],1)*100:.1f}%)

Head-to-head (all venues, {h['total']} games):
  {full1} wins: {h['team1_wins']} | {full2} wins: {h['team2_wins']}

Venue H2H ({', '.join(venue_kws) or 'N/A'}, {vn['total']} games):
  {full1} wins: {vn['team1_wins']} | {full2} wins: {vn['team2_wins']}

=== COMPUTED PROBABILITY ===
Formula: {method}
Result: {full1} = {prob_pct}%  /  {full2} = {100 - prob_pct}%
Model pick (higher probability): {model_pick_from_formula} at {prob_pct}%
{_crex_prompt_section(crex, abbr1, abbr2)}
Now identify the public_team and model_pick, and write 3 short reasons.
Use abbreviations {abbr1} and {abbr2} in your JSON."""
    else:
        prob_pct = 55  # conservative default when no data
        user_prompt = f"""Match: {full1} ({abbr1}) vs {full2} ({abbr2})
Venue: {venue or 'unknown'}

No Cricsheet data available at configured path.
Use your general cricket knowledge of IPL history, brand perception, and recent seasons.
Estimate a probability between 50-70% and choose the statistically stronger team as model_pick.
Use abbreviations {abbr1} and {abbr2}.
{_crex_prompt_section(crex, abbr1, abbr2)}"""

    # Step 3: AI narrative
    raw = _call_ai(_SYSTEM, user_prompt)

    # Extract JSON (handle markdown code fences)
    json_match = re.search(r"\{[\s\S]+?\}", raw)
    if not json_match:
        raise ValueError(f"Agent returned no JSON.\nRaw:\n{raw}")

    ai_result = json.loads(json_match.group())

    for field in ("model_pick", "public_team", "reasons"):
        if field not in ai_result:
            raise ValueError(f"Missing '{field}' in AI response: {ai_result}")

    return {
        "match":           f"{abbr1} vs {abbr2}",
        "model_pick":      ai_result["model_pick"].upper(),
        "public_team":     ai_result["public_team"].upper(),
        "probability":     int(ai_result.get("probability", prob_pct)),
        "reasons":         ai_result["reasons"][:3],
        "explanation":     ai_result.get("explanation", ""),
        "stats":           stats,
        "stats_available": stats_available,
        "crex":            crex,
    }


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TrueOddsML Probability Agent")
    parser.add_argument("match", help="e.g. 'GT vs SRH'")
    parser.add_argument("--venue", default=None, help="Venue name, e.g. 'Ahmedabad'")
    parser.add_argument("--crex", default=None, metavar="URL",
                        help="Crex match-details URL for live venue/form data")
    args = parser.parse_args()

    try:
        result = run_agent(args.match, args.venue, crex_url=args.crex)
        print(json.dumps(result, indent=2))
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)
