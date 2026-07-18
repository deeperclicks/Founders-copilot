"""
Mock implementations of the 6 Founder Copilot tools with realistic Indian
startup data (DPIIT, Startup India, MSME, SIDBI, MeitY, etc.).
Deterministic scoring based on hashing so demos feel consistent per idea.
"""
from __future__ import annotations
import hashlib
import re
from typing import Any


def _seed(text: str, salt: str = "") -> int:
    h = hashlib.sha256((salt + "::" + (text or "")).encode()).hexdigest()
    return int(h[:8], 16)


def _score(text: str, salt: str, lo: int = 55, hi: int = 92) -> int:
    return lo + (_seed(text, salt) % (hi - lo + 1))


# ---------------- 1. validate_idea ---------------- #
def validate_idea(idea: str, target_market: str = "", business_model: str = "") -> dict[str, Any]:
    text = f"{idea} {target_market} {business_model}".lower()

    market = _score(text, "market", 58, 90)
    feas = _score(text, "feasibility", 55, 88)
    comp = 100 - _score(text, "competition", 30, 78)  # higher = less competition = better

    signals = []
    if any(k in text for k in ["ai", "ml", "llm", "genai", "agent"]):
        signals.append("AI tailwind — hiring pool + investor appetite are both hot in India right now.")
        market = min(95, market + 6)
    if any(k in text for k in ["farmer", "agri", "rural", "bharat", "tier 2", "tier 3", "vernacular"]):
        signals.append("Bharat play — DPIIT / NABARD / Startup India Seed Fund actively backing this.")
        feas = min(92, feas + 4)
    if any(k in text for k in ["b2b", "saas", "enterprise"]):
        signals.append("B2B SaaS — clearer revenue model, ARR benchmarks well-understood by Indian VCs.")
    if any(k in text for k in ["d2c", "consumer", "direct-to-consumer"]):
        signals.append("D2C — margin pressure real, but Meesho/Zepto era has warmed up funders again.")
    if not signals:
        signals.append("Category is broad — a sharper wedge will help both fundraising and GTM.")

    # top priority
    scores = {"Market signal": market, "Feasibility": feas, "Competitive room": comp}
    weakest = min(scores, key=scores.get)
    priorities = {
        "Market signal": "Talk to 15 target users this week. Get 3 who'll pay a deposit before writing any more code.",
        "Feasibility": "Cut scope to a single wedge you can ship in 6 weeks. Everything else is a distraction.",
        "Competitive room": "Name your 3 biggest competitors and write one sentence on why a user leaves them for you. If you can't, you don't have a wedge yet.",
    }

    return {
        "market_signal": market,
        "feasibility": feas,
        "competition": comp,
        "overall": round((market + feas + comp) / 3),
        "signals": signals,
        "top_priority": {
            "area": weakest,
            "action": priorities[weakest],
        },
    }


# ---------------- 2. check_funding_eligibility ---------------- #
_SCHEMES = [
    {
        "name": "Startup India Seed Fund Scheme (SISFS)",
        "amount": "Up to ₹20L grant / ₹50L convertible debenture",
        "run_by": "DPIIT · Ministry of Commerce",
        "url": "https://seedfund.startupindia.gov.in/",
        "stage": ["idea", "prototype", "mvp"],
        "requires_dpiit": True,
        "status": "open",
    },
    {
        "name": "MeitY TIDE 2.0",
        "amount": "Up to ₹25L grant + incubation",
        "run_by": "MeitY · Government of India",
        "url": "https://tide.meity.gov.in/",
        "stage": ["idea", "prototype"],
        "requires_dpiit": False,
        "status": "closed-next-cycle-TBD",
    },
    {
        "name": "BIRAC BIG (Biotech Ignition Grant)",
        "amount": "Up to ₹50L grant",
        "run_by": "BIRAC · DBT",
        "url": "https://birac.nic.in/desc_new.php?id=91",
        "stage": ["idea", "prototype", "mvp"],
        "requires_dpiit": False,
        "status": "open",
        "sector": ["health", "bio", "medtech", "pharma"],
    },
    {
        "name": "NIDHI PRAYAS",
        "amount": "Up to ₹10L prototype grant",
        "run_by": "DST · Government of India",
        "url": "https://www.nidhi-prayas.org/",
        "stage": ["idea", "prototype"],
        "requires_dpiit": False,
        "status": "open",
    },
    {
        "name": "MSME Prime Minister's Employment Generation Programme (PMEGP)",
        "amount": "Up to ₹50L (manufacturing) / ₹20L (service)",
        "run_by": "KVIC · MoMSME",
        "url": "https://www.kviconline.gov.in/pmegpeportal/",
        "stage": ["idea", "prototype", "mvp", "revenue"],
        "requires_dpiit": False,
        "status": "open",
    },
    {
        "name": "SIDBI Fund of Funds for Startups (FFS)",
        "amount": "Deployed via AIF partners (₹1Cr+)",
        "run_by": "SIDBI · DPIIT",
        "url": "https://www.sidbivcf.in/",
        "stage": ["mvp", "revenue", "growth"],
        "requires_dpiit": True,
        "status": "open",
    },
    {
        "name": "iCreate Fellowship",
        "amount": "₹5L–₹25L equity-free grant",
        "run_by": "iCreate · Gujarat",
        "url": "https://www.icreate.org.in/",
        "stage": ["idea", "prototype", "mvp"],
        "requires_dpiit": False,
        "status": "open",
    },
    {
        "name": "Nidhi Seed Support System (NIDHI-SSS)",
        "amount": "Up to ₹1Cr seed support",
        "run_by": "DST · via TBIs",
        "url": "https://www.startupindia.gov.in/content/sih/en/government-schemes.html",
        "stage": ["prototype", "mvp"],
        "requires_dpiit": True,
        "status": "open",
    },
    {
        "name": "State Startup Policy Grants (varies)",
        "amount": "₹2L–₹25L (state-specific)",
        "run_by": "Your state startup mission",
        "url": "https://www.startupindia.gov.in/content/sih/en/state-startup-policies.html",
        "stage": ["idea", "prototype", "mvp", "revenue"],
        "requires_dpiit": False,
        "status": "open",
    },
]


def check_funding_eligibility(
    idea: str = "",
    stage: str = "idea",
    state: str = "",
    dpiit_registered: bool = False,
    founders_count: int = 1,
) -> dict[str, Any]:
    stage = (stage or "idea").lower()
    text = idea.lower()
    matches = []
    for s in _SCHEMES:
        if stage not in s["stage"]:
            continue
        sector_ok = True
        if "sector" in s:
            sector_ok = any(k in text for k in s["sector"])
        if not sector_ok:
            continue
        fit = 70
        if s["requires_dpiit"] and not dpiit_registered:
            fit -= 15
        if s["stage"][0] == stage:
            fit += 8
        fit += _seed(idea, s["name"]) % 12
        fit = max(45, min(96, fit))
        matches.append({
            "name": s["name"],
            "amount": s["amount"],
            "run_by": s["run_by"],
            "url": s["url"],
            "status": s["status"],
            "fit_score": fit,
            "requires_dpiit": s["requires_dpiit"],
            "note": (
                "Register on Startup India → get DPIIT recognition first (free, ~2 weeks). Unlocks this scheme."
                if s["requires_dpiit"] and not dpiit_registered
                else "You look eligible on paper. Read the fine print on the portal before applying."
            ),
        })
    matches.sort(key=lambda x: (-x["fit_score"], x["status"] != "open"))
    return {
        "schemes": matches[:6],
        "dpiit_hint": (
            "You already have DPIIT recognition — good, keep the number handy for applications."
            if dpiit_registered
            else "Register for DPIIT recognition on startupindia.gov.in — it's free, and it unlocks half of these schemes plus tax benefits."
        ),
    }


# ---------------- 3. recommend_entity_type ---------------- #
def recommend_entity_type(founders_count: int = 1, funding_goal: str = "bootstrap", business_model: str = "") -> dict[str, Any]:
    fg = (funding_goal or "").lower()
    bm = (business_model or "").lower()
    wants_vc = any(k in fg for k in ["vc", "venture", "angel", "series", "equity", "raise"])

    if founders_count <= 1 and not wants_vc:
        entity = "One Person Company (OPC)"
        rationale = "Solo founder, no VC ambition right now — OPC gives you a legal shell with limited liability, minimal compliance, and you can convert to Pvt Ltd later when a term sheet lands."
        checklist = [
            "DIN + DSC for the director",
            "Name reservation via SPICe+ (MCA portal)",
            "Nominee director appointment (mandatory for OPC)",
            "PAN + TAN (auto-issued with SPICe+)",
            "Current account (Indian bank, post-incorporation)",
            "GST registration (if turnover > ₹20L / interstate)",
        ]
    elif founders_count >= 2 and not wants_vc and ("service" in bm or "agency" in bm or "consult" in bm):
        entity = "Limited Liability Partnership (LLP)"
        rationale = "Two+ founders, services/agency model, no VC on the horizon — LLP keeps compliance light, taxes partnership-flat, and no minimum capital requirement."
        checklist = [
            "DPIN + DSC for both partners",
            "Name reservation via RUN-LLP",
            "LLP Agreement (stamped, notarised)",
            "Form FiLLiP + PAN + TAN",
            "Current account in LLP name",
            "GST registration (if applicable)",
        ]
    else:
        entity = "Private Limited Company (Pvt Ltd)"
        rationale = (
            "Multiple founders and/or plans to raise external capital — Pvt Ltd is what every Indian VC, angel, "
            "and grant portal expects to see. Higher compliance cost, but ESOPs, priced rounds, and cap tables only work here."
        )
        checklist = [
            "DIN + DSC for all directors",
            "Name reservation via SPICe+ Part A",
            "Draft MoA + AoA",
            "SPICe+ Part B filing (PAN + TAN + EPFO + ESIC bundled)",
            "Certificate of Incorporation from MCA",
            "Founders' Agreement (equity split, vesting, IP assignment)",
            "Current account in company name",
            "DPIIT recognition on Startup India (highly recommended)",
            "GST registration (if turnover > ₹40L / interstate)",
        ]

    return {
        "entity": entity,
        "rationale": rationale,
        "doc_checklist": checklist,
        "typical_setup_cost": "₹8,000 – ₹18,000 (govt fees + CA + stamping)",
        "typical_setup_time": "10 – 21 working days",
    }


# ---------------- 4. generate_gtm_playbook ---------------- #
def generate_gtm_playbook(idea: str = "", target_market: str = "", business_model: str = "") -> dict[str, Any]:
    text = f"{idea} {target_market} {business_model}".lower()
    is_b2b = any(k in text for k in ["b2b", "saas", "enterprise", "business", "smb", "sme"])
    is_b2c = any(k in text for k in ["consumer", "d2c", "b2c", "user", "student", "everyday"])
    is_bharat = any(k in text for k in ["bharat", "tier 2", "tier 3", "rural", "regional", "vernacular", "hindi", "tamil", "telugu"])

    tactics = []
    if is_b2b:
        tactics.extend([
            "Pick 30 named target accounts. Not a segment, actual company names on a spreadsheet.",
            "Founder-led outbound: 10 personalised LinkedIn DMs a day. No templates, no automations for the first 100 conversations.",
            "Free audit / teardown offer — trade a 30-min report for a 15-min call. Converts cold to warm faster than a demo request form.",
            "Publish one sharp POV per week on LinkedIn. Not thought leadership — pick a fight with an assumption in your category.",
            "Join 2 industry WhatsApp/Slack groups where your ICP already hangs out. Answer questions for 3 weeks before you pitch.",
        ])
    elif is_b2c:
        tactics.extend([
            "Build a 500-person waitlist before you build the product. Landing page + 1 short Loom + Instagram reels demo.",
            "Do the first 50 signups manually (WhatsApp onboarding). You're buying insight, not scale.",
            "Instagram + YouTube Shorts is your top-of-funnel — post 3x/week, one format, iterate for 4 weeks before judging.",
            "Referral loop from day 1 — one existing user should be able to invite a friend in <30 seconds. Track K-factor weekly.",
            "College / society ambassador program if your audience is 18–24. Ten campuses beat one Instagram ad.",
        ])
    else:
        tactics.extend([
            "Write a one-page 'who this is for' doc. If you can't finish the sentence 'This is for X who wants to do Y and today does Z', you're not ready to sell.",
            "Do 20 discovery calls before you spend a rupee on paid.",
            "Land 3 design-partner customers at 50% off in exchange for weekly feedback + a testimonial.",
            "Ship a public changelog. Trust compounds when people see you shipping every week.",
            "Pick one channel and go deep for 6 weeks. Multi-channel is a distraction pre-PMF.",
        ])
    if is_bharat:
        tactics.append("Field visits > Zoom calls. Book a train, go to 3 cities in your target region in the next 30 days.")
        tactics.append("Regional language content — even a landing page in Hindi/Tamil/Telugu doubles conversion for Bharat plays.")

    first_100 = (
        "Land your first 100 users this way: 40 from personal network + WhatsApp + LinkedIn, "
        "30 from community/forum contribution, 20 from cold outbound, 10 from one PR-worthy content piece."
    )

    return {
        "tactics": tactics,
        "first_100_users_plan": first_100,
        "north_star_metric": (
            "Weekly Active Paying Accounts" if is_b2b else
            "Weekly Retained Users (W4)" if is_b2c else
            "Weekly Retention Cohort"
        ),
        "cadence": "Ship weekly. Talk to 5 users weekly. Review metrics weekly. That's the whole loop.",
    }


# ---------------- 5. get_founder_profile ---------------- #
def get_founder_profile(profile: dict[str, Any] | None) -> dict[str, Any]:
    if not profile:
        return {
            "known": False,
            "summary": "No profile yet — share your idea on the entry screen and I'll remember everything.",
        }
    idea = profile.get("idea", "")
    return {
        "known": True,
        "summary": (
            f"Founder building: {idea[:140]}{'...' if len(idea) > 140 else ''}. "
            f"Stage: {profile.get('stage', 'idea')}. "
            f"State: {profile.get('state', 'unspecified')}. "
            f"Founders: {profile.get('founders_count', 1)}. "
            f"DPIIT: {'yes' if profile.get('dpiit_registered') else 'no'}."
        ),
        "profile": profile,
    }


# ---------------- 6. find_growth_opportunities ---------------- #
_OPPORTUNITIES = [
    {
        "name": "Startup Mahakumbh",
        "type": "event",
        "when": "Annual · Delhi",
        "why": "India's largest founder gathering — DPIIT-backed, investor + govt access in one place.",
        "url": "https://www.startupmahakumbh.org/",
    },
    {
        "name": "Startup India Yatra",
        "type": "roadshow",
        "when": "Rolling · state-wise",
        "why": "Free mentorship + pitch days in tier-2/3 cities. Good if you're not in a metro.",
        "url": "https://www.startupindia.gov.in/",
    },
    {
        "name": "TiE Global Summit",
        "type": "event",
        "when": "Annual · Bengaluru",
        "why": "Diaspora angels + Indian founders in one room. Genuinely useful for seed conversations.",
        "url": "https://tie.org/",
    },
    {
        "name": "Smart India Hackathon",
        "type": "hackathon",
        "when": "Annual · nationwide",
        "why": "Government problem statements — if you win, MeitY / ministries actually deploy your solution.",
        "url": "https://www.sih.gov.in/",
    },
    {
        "name": "HackWithInfy / TechGig Code Gladiators",
        "type": "hackathon",
        "when": "Multiple cycles/year",
        "why": "Not for grants, but great for hiring your first engineers cheaply.",
        "url": "https://www.techgig.com/",
    },
    {
        "name": "Y Combinator Startup School (India cohort)",
        "type": "program",
        "when": "Rolling · online",
        "why": "Free. The curriculum alone is worth more than most paid accelerators.",
        "url": "https://www.startupschool.org/",
    },
    {
        "name": "Sequoia Surge",
        "type": "accelerator",
        "when": "2 cohorts/year",
        "why": "Best pre-seed / seed accelerator in South Asia. Selective, worth applying even for the feedback.",
        "url": "https://www.peakxv.com/surge/",
    },
    {
        "name": "AWS Activate / Google for Startups / Azure Founders Hub",
        "type": "credits",
        "when": "Rolling",
        "why": "Up to $100k in cloud credits. Apply to all three; you'll get at least one.",
        "url": "https://aws.amazon.com/activate/",
    },
    {
        "name": "NASSCOM 10,000 Startups",
        "type": "program",
        "when": "Rolling",
        "why": "Corporate connects, product-market fit help, some grants for deep tech.",
        "url": "https://10000startups.com/",
    },
    {
        "name": "Zoho for Startups",
        "type": "credits",
        "when": "Rolling",
        "why": "Free Zoho suite for 1 year if you're DPIIT-recognised. Saves ₹1L+ easily.",
        "url": "https://www.zoho.com/startups/",
    },
]


def find_growth_opportunities(idea: str = "", stage: str = "idea") -> dict[str, Any]:
    text = idea.lower()
    ranked = []
    for o in _OPPORTUNITIES:
        score = 70 + _seed(text, o["name"]) % 25
        if o["type"] == "hackathon" and any(k in text for k in ["ai", "tech", "software", "app"]):
            score += 5
        if o["type"] == "credits":
            score += 3  # always useful
        ranked.append({**o, "fit_score": min(97, score)})
    ranked.sort(key=lambda x: -x["fit_score"])
    return {"opportunities": ranked[:8]}


# ---------------- Tool registry for chatbot ---------------- #
TOOL_REGISTRY = {
    "validate_idea": validate_idea,
    "check_funding_eligibility": check_funding_eligibility,
    "recommend_entity_type": recommend_entity_type,
    "generate_gtm_playbook": generate_gtm_playbook,
    "get_founder_profile": get_founder_profile,
    "find_growth_opportunities": find_growth_opportunities,
}
