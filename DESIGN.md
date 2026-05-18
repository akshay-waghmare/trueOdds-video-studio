# DESIGN.md — TrueOddsML Visual Style Guide

## Brand Identity

**Name**: TrueOddsML  
**Positioning**: Anti-baba. Probability-first. Cricket ML predictions.  
**Tone**: Confident, sharp, slightly edgy — not hype, not safe.

## Legal / Brand Safety

Do not use official IPL, franchise, broadcaster, sponsor, or team logos in v1 unless rights are confirmed. Use text badges only, for example `MI`, `KKR`, `RCB`, or generic team color blocks. The reel should be visually owned by **TrueOddsML**, not dependent on IPL/team marks.

---

## Canvas

| Property | Value |
|----------|-------|
| Dimensions | 1080 × 1920 px (9:16) |
| Duration | 18–22 seconds |
| Frame Rate | 30fps |
| Format | MP4, H.264 |
| Max File Size | 50MB |

---

## Color Palette

| Role | Color | Hex |
|------|-------|-----|
| Background | Near-black | `#0A0A0F` |
| Surface / Card | Dark navy | `#12121E` |
| Border / Divider | Deep blue-grey | `#1E2235` |
| Primary Accent | Electric yellow | `#F5C518` |
| Secondary Accent | Teal | `#00C9A7` |
| Text Primary | White | `#FFFFFF` |
| Text Secondary | Light grey | `#A0A8B8` |
| Danger / Public hype | Muted red | `#FF4C4C` |
| Model pick highlight | Accent yellow | `#F5C518` |

---

## Typography

| Usage | Font | Weight | Size |
|-------|------|--------|------|
| Match name | Bebas Neue / Impact | 700 | 72–88px |
| Section labels | Inter / Poppins | 600 | 28px |
| Body / Reasons | Inter | 400 | 24px |
| Probability number | Bebas Neue | 700 | 96px |
| CTA | Inter | 800 | 32px |
| Watermark | Inter | 400 | 18px |

*Fallback*: system-ui, -apple-system, sans-serif

---

## Layout Zones (top-to-bottom, 1080×1920)

```
┌─────────────────────────────┐  ← 0px
│  HEADER: Match Name         │  (0–280px)
│  "MI vs KKR"                │
├─────────────────────────────┤  ← 280px
│  SPLIT CARD                 │  (280–560px)
│  Public: MI  |  Pick: KKR   │
├─────────────────────────────┤  ← 560px
│  PROBABILITY METER          │  (560–880px)
│  62% — animated arc         │
├─────────────────────────────┤  ← 880px
│  REASON CARD 1              │  (880–1080px)
│  REASON CARD 2              │  (1080–1280px)
│  REASON CARD 3              │  (1280–1480px)
├─────────────────────────────┤  ← 1480px
│  WATERMARK (TrueOddsML)     │  (1480–1560px)
├─────────────────────────────┤  ← 1560px
│  CTA FOOTER                 │  (1560–1920px)
│  "Not baba. Probability."   │
└─────────────────────────────┘  ← 1920px
```

---

## Animation Guide

| Element | Animation | Timing |
|---------|-----------|--------|
| Header | Fade-in + slide up | 0s → 0.8s |
| Split card | Fade-in | 0.8s → 1.5s |
| Probability meter | Arc draws from 0 → value | 1.5s → 4s |
| Probability number | Count-up (0 → value) | 1.5s → 4s |
| Reason Card 1 | Slide in from left | 4.5s |
| Reason Card 2 | Slide in from left | 5.2s |
| Reason Card 3 | Slide in from left | 5.9s |
| Watermark | Fade-in | 6.5s |
| CTA | Bold fade-in + subtle pulse | 15s → 18s |

---

## Copy Rules

- **Match name**: All caps, "TEAM A vs TEAM B"
- **Public vs Model labels**: "PUBLIC PICK" / "MODEL PICK"
- **Probability**: Show as integer + "%" e.g. "62%"
- **Reasons**: Max 60 characters each; start with action verb or data point
- **CTA**: Keep sharp. Default: *"Not baba prediction. Probability."*
- **Watermark**: "TrueOddsML" + optional handle "@trueoddsml"

---

## Anti-Patterns (Do Not Use)

- ❌ Light backgrounds or white/cream themes
- ❌ Pastel colors
- ❌ Generic "sports" stock imagery
- ❌ Hype language ("🔥 guaranteed win")
- ❌ Low-contrast text
- ❌ Clip art or emoji-heavy design
- ❌ Official IPL/team logos or protected marks in v1
