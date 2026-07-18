# Founder Copilot — PRD

## Original Problem Statement
Build "Founder Copilot" — an AI cofounder for early-stage Indian startup founders.
- Neomorphism (soft UI) throughout, dual soft shadows (raised OUT, pressed IN)
- Full light/dark mode with same shadow language in both
- Cinematic intro (logo assembly from soft shapes, ~1.5–2s, skippable, prefers-reduced-motion aware)
- 3 screens: Entry (founder types idea) → Report (4 tool panels) → Chatbot (floating FAB, streaming)
- Indigo/violet accent + muted saffron highlight, everything else monochrome soft
- Persistent "Made with NitroStack" watermark + "Team Forca" credit (Abhiram Mamidi, Joseph Rezin, Ashish Rajesh, Manushka A G)
- 6 backend tools mirrored: validate_idea, check_funding_eligibility, recommend_entity_type, generate_gtm_playbook, get_founder_profile, find_growth_opportunities

## Tech
- Backend: FastAPI + MongoDB (motor). LLM via emergentintegrations LlmChat → Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`) with Emergent Universal LLM Key. SSE streaming for chat.
- Frontend: React 19, Tailwind, framer-motion (available), lucide-react icons, custom neomorphism CSS variables in `/app/frontend/src/index.css`.
- Anonymous session persistence via localStorage `fc_session_id` → MongoDB collections `founder_profiles`, `founder_reports`, `chat_history`.

## User Personas
- **Solo/co-founder in Indian tier-1/2/3 city** — building an early-stage startup, needs quick honest validation, funding scheme matching (DPIIT, SISFS, MeitY TIDE, PMEGP, SIDBI FFS, iCreate, NIDHI), entity recommendation, and a GTM plan.

## Core Requirements (Static)
- Warm, cofounder-tone copy (no corporate jargon)
- Every interactive element has a data-testid, neomorphic press/release feedback
- Responsive: mobile / tablet / desktop
- Real portal URLs (Startup India, TiE, YC Startup School, AWS Activate, etc.)
- No fake funding dates — status is "open" or "closed-next-cycle-TBD"

## What's Been Implemented (2026-01-18)
- ✅ Cinematic intro (soft-shape assembly wordmark, skip on click, reduced-motion aware)
- ✅ Entry screen with idea textarea + soft-chip selectors for business model, stage, funding goal, DPIIT
- ✅ POST /api/founder/analyze runs all 4 report tools + growth, persists profile + report
- ✅ Report screen with validation gauges, top-priority callout, funding cards with fit-scores + honest status badges, entity recommendation with checklist chips, GTM numbered playbook, growth opportunities grid
- ✅ Floating chat FAB → SSE streaming Claude Sonnet 4.5, grounded in stored profile, can invoke the 6 tools via `[TOOL: name {json}]` first-line convention
- ✅ Full light/dark theme toggle with distinct shadow palettes in each
- ✅ "Made with NitroStack" watermark + "Team Forca" pill opening About modal
- ✅ 100% backend + frontend test pass (11/11 pytest + full Playwright E2E)

## Backlog / P1
- Real MCP server wiring (currently mock 6 tools with realistic Indian data)
- Per-user rate-limiting on /api/founder/chat
- Export report to PDF / share link
- Email digest of new schemes matching the founder profile

## P2
- Multi-language UI (Hindi first)
- Cap-table & vesting calculator
- Founder network / matchmaking

## Next Action Items
- Optional: wire the real MCP server endpoints when the user shares them (replace `founder_tools.py` implementations while keeping the same function signatures).
