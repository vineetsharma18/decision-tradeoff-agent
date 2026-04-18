import requests

BASE_URL = "http://localhost:3000"

# ---------------------------
# EVALUATION DIMENSIONS
# ---------------------------
DIMENSIONS = {
    "salary":    {"label": "💰 Salary / Compensation",  "weight": 0},
    "growth":    {"label": "📈 Career Growth",           "weight": 0},
    "interest":  {"label": "❤️  Personal Interest",      "weight": 0},
    "stability": {"label": "🏛️  Job Stability",          "weight": 0},
    "future":    {"label": "🚀 Future Demand / Trends",  "weight": 0},
}

PRIORITY_WEIGHTS = {
    "1": {"salary": 0.40, "growth": 0.25, "interest": 0.15, "stability": 0.10, "future": 0.10},
    "2": {"salary": 0.10, "growth": 0.20, "interest": 0.40, "stability": 0.15, "future": 0.15},
    "3": {"salary": 0.15, "growth": 0.15, "interest": 0.15, "stability": 0.40, "future": 0.15},
}

# Heuristic scores per domain keyword (fallback when LPI is unavailable)
HEURISTIC_DB = {
    "ai": {
        "salary": 9, "growth": 10, "interest": 8, "stability": 7, "future": 10,
        "pros": ["Highest paying ML/AI roles", "Explosive industry growth", "Cutting-edge research"],
        "cons": ["Steep learning curve", "Requires math/stats depth", "Fast-changing landscape"],
    },
    "web dev": {
        "salary": 7, "growth": 7, "interest": 7, "stability": 8, "future": 7,
        "pros": ["Large talent demand", "Visible, tangible outputs", "Freelance flexibility"],
        "cons": ["Commoditising market", "Framework churn", "Lower ceiling vs. AI/ML"],
    },
    "data science": {
        "salary": 8, "growth": 8, "interest": 7, "stability": 7, "future": 9,
        "pros": ["Cross-industry demand", "Analytical depth", "Good remote opportunities"],
        "cons": ["Heavy data-cleaning work", "Often needs domain expertise", "Tooling fragmentation"],
    },
    "cybersecurity": {
        "salary": 8, "growth": 9, "interest": 8, "stability": 9, "future": 9,
        "pros": ["Critical shortage of talent", "High job security", "Constantly evolving challenges"],
        "cons": ["On-call stress", "Requires constant upskilling", "High responsibility"],
    },
}

# ---------------------------
# LPI TOOL CALLS
# ---------------------------
def query_knowledge(query: str) -> dict:
    try:
        res = requests.post(f"{BASE_URL}/query_knowledge", json={"query": query}, timeout=5)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.ConnectionError:
        return {"error": "LPI server not reachable. Running in offline mode."}
    except requests.exceptions.Timeout:
        return {"error": "LPI request timed out."}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP error from LPI: {e.response.status_code}"}
    except Exception as e:
        return {"error": f"Unexpected error in query_knowledge: {str(e)}"}


def get_insights(scenario: str) -> dict:
    try:
        res = requests.post(
            f"{BASE_URL}/get_insights",
            json={"scenario": scenario, "tier": "free"},
            timeout=5
        )
        res.raise_for_status()
        return res.json()
    except requests.exceptions.ConnectionError:
        return {"error": "LPI server not reachable. Running in offline mode."}
    except requests.exceptions.Timeout:
        return {"error": "LPI request timed out."}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP error from LPI: {e.response.status_code}"}
    except Exception as e:
        return {"error": f"Unexpected error in get_insights: {str(e)}"}


# ---------------------------
# INPUT PARSING
# ---------------------------
def parse_options(user_input: str):
    separators = [" vs ", " versus ", " or "]
    for sep in separators:
        if sep in user_input.lower():
            idx = user_input.lower().index(sep)
            opt1 = user_input[:idx].strip().lower()
            opt2 = user_input[idx + len(sep):].strip().lower()
            return opt1, opt2
    return user_input.strip().lower(), None


# ---------------------------
# SCORING ENGINE
# ---------------------------
def get_heuristic_scores(option: str) -> dict | None:
    """Fuzzy-match option label to heuristic DB."""
    for key, data in HEURISTIC_DB.items():
        if key in option:
            return data
    return None


def score_option(option: str, weights: dict, lpi_knowledge: dict, lpi_insights: dict) -> dict:
    """
    Build a multi-dimensional score for one option.
    Merges LPI data (if available) with heuristic fallback scores.
    Returns a dict with per-dimension scores and a weighted total.
    """
    heuristic = get_heuristic_scores(option) or {}

    # Try to extract numeric signals from LPI response
    lpi_boost = {}
    for source in [lpi_knowledge, lpi_insights]:
        if "error" not in source and isinstance(source, dict):
            for dim in DIMENSIONS:
                if dim in str(source).lower():  # crude signal detection
                    lpi_boost[dim] = lpi_boost.get(dim, 0) + 0.5  # small boost for LPI mention

    scores = {}
    for dim in DIMENSIONS:
        base = heuristic.get(dim, 5)           # fallback = neutral 5/10
        boost = min(lpi_boost.get(dim, 0), 1)  # cap LPI boost at +1
        scores[dim] = min(round(base + boost, 1), 10)

    weighted_total = sum(scores[dim] * weights[dim] for dim in DIMENSIONS)
    return {
        "scores": scores,
        "weighted_total": round(weighted_total, 2),
        "pros": heuristic.get("pros", ["Consult LPI for detailed pros"]),
        "cons": heuristic.get("cons", ["Consult LPI for detailed cons"]),
    }


# ---------------------------
# DISPLAY HELPERS
# ---------------------------
def bar(score: float, max_score: float = 10, width: int = 20) -> str:
    filled = int((score / max_score) * width)
    return "█" * filled + "░" * (width - filled)


def print_option_card(option: str, result: dict):
    print(f"\n  ┌─ {option.upper()} {'─' * max(0, 40 - len(option))}")
    for dim, meta in DIMENSIONS.items():
        s = result["scores"][dim]
        print(f"  │  {meta['label']:<30} {bar(s)}  {s}/10")
    print(f"  │")
    print(f"  │  ✅ Pros:")
    for p in result["pros"]:
        print(f"  │     • {p}")
    print(f"  │  ⚠️  Cons:")
    for c in result["cons"]:
        print(f"  │     • {c}")
    print(f"  │")
    print(f"  └─ 🎯 Weighted Score: {result['weighted_total']}/10")


def print_lpi_summary(label: str, data: dict):
    print(f"\n  [{label}]")
    if "error" in data:
        print(f"  ⚠️  {data['error']}")
    elif isinstance(data, dict):
        for k, v in data.items():
            print(f"  • {k}: {v}")
    else:
        print(f"  {data}")


# ---------------------------
# MAIN AGENT
# ---------------------------
def decision_agent():
    print("\n" + "═" * 55)
    print("  🤖  Decision Tradeoff Agent  (Multi-Dimensional)")
    print("═" * 55)

    # ── Input ──────────────────────────────────────────────
    user_query = input("\nEnter your decision (e.g., AI vs Web Dev): ").strip()
    if not user_query:
        print("❌ Please enter a valid decision.")
        return

    option1, option2 = parse_options(user_query)

    # ── Priority ───────────────────────────────────────────
    print("\nWhat matters MOST to you?")
    print("  1. 💰 Salary & Compensation")
    print("  2. ❤️  Personal Interest & Passion")
    print("  3. 🏛️  Stability & Predictability")
    priority = input("Choose (1/2/3): ").strip()

    if priority not in PRIORITY_WEIGHTS:
        print("⚠️  Invalid choice — defaulting to Interest (2).")
        priority = "2"

    weights = PRIORITY_WEIGHTS[priority]

    # ── LPI Tool Calls ─────────────────────────────────────
    print("\n" + "─" * 55)
    print("🔍 Querying LPI knowledge base...")
    knowledge1 = query_knowledge(option1)
    knowledge2 = query_knowledge(option2) if option2 else {}

    print("💡 Fetching LPI insights...")
    insights1 = get_insights(option1)
    insights2 = get_insights(option2) if option2 else {}

    # ── LPI Raw Output ─────────────────────────────────────
    print("\n📡 LPI Raw Responses:")
    print_lpi_summary(f"query_knowledge → {option1}", knowledge1)
    if option2:
        print_lpi_summary(f"query_knowledge → {option2}", knowledge2)
    print_lpi_summary(f"get_insights → {option1}", insights1)
    if option2:
        print_lpi_summary(f"get_insights → {option2}", insights2)

    # ── Scoring ────────────────────────────────────────────
    result1 = score_option(option1, weights, knowledge1, insights1)
    result2 = score_option(option2, weights, knowledge2, insights2) if option2 else None

    # ── Report ─────────────────────────────────────────────
    print("\n" + "═" * 55)
    print("  📊  MULTI-DIMENSIONAL EVALUATION REPORT")
    print("═" * 55)

    print_option_card(option1, result1)
    if result2:
        print_option_card(option2, result2)

    # ── Dimension-by-Dimension Comparison ──────────────────
    if result2:
        print("\n" + "─" * 55)
        print("  ⚖️   HEAD-TO-HEAD COMPARISON")
        print("─" * 55)
        print(f"  {'Dimension':<30} {option1.upper()[:12]:<14} {option2.upper()[:12]}")
        print("  " + "─" * 50)
        for dim, meta in DIMENSIONS.items():
            s1 = result1["scores"][dim]
            s2 = result2["scores"][dim]
            winner = "◀" if s1 > s2 else ("▶" if s2 > s1 else "=")
            print(f"  {meta['label']:<30} {s1:<14} {s2}  {winner}")
        print("  " + "─" * 50)
        print(f"  {'🎯 WEIGHTED TOTAL':<30} {result1['weighted_total']:<14} {result2['weighted_total']}")

    # ── Final Recommendation ───────────────────────────────
    print("\n" + "═" * 55)
    print("  ✅  FINAL RECOMMENDATION")
    print("═" * 55)

    priority_labels = {"1": "Salary", "2": "Personal Interest", "3": "Stability"}
    print(f"\n  Your top priority: {priority_labels[priority]}")

    if result2:
        winner = option1 if result1["weighted_total"] >= result2["weighted_total"] else option2
        loser  = option2 if winner == option1 else option1
        margin = abs(result1["weighted_total"] - result2["weighted_total"])
        print(f"\n  🏆 Recommended: {winner.upper()}")
        if margin < 0.5:
            print(f"  ⚠️  Margin is tight ({margin}/10) — both paths are viable.")
            print(f"      Consider piloting {loser} as a side project before committing.")
        else:
            print(f"  📌 {winner.title()} leads by {margin:.1f} points on your priority weighting.")
    else:
        print(f"\n  Evaluating: {option1.upper()}")
        score = result1["weighted_total"]
        verdict = "Strong" if score >= 7 else ("Moderate" if score >= 5 else "Weak")
        print(f"  📌 Overall fit: {verdict} ({score}/10 weighted score)")

    print("\n  📌 Sources: query_knowledge (LPI) · get_insights (LPI) · heuristic DB")
    print("═" * 55 + "\n")


# ---------------------------
# ENTRY POINT
# ---------------------------
if __name__ == "__main__":
    try:
        decision_agent()
    except KeyboardInterrupt:
        print("\n\n👋 Exiting agent. Goodbye!")
