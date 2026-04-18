import requests
import sys
import time

BASE_URL = "http://localhost:3000"

# ---------------------------
# LPI TOOL CALLS (REAL)
# ---------------------------

def query_knowledge(query: str, retries: int = 2) -> dict:
    """
    Query the LPI knowledge base.
    Retries on transient failures. Returns a dict with 'result' key on success,
    or 'error' key on failure.
    """
    for attempt in range(1, retries + 2):
        try:
            res = requests.post(
                f"{BASE_URL}/query_knowledge",
                json={"query": query},
                timeout=10
            )
            res.raise_for_status()
            data = res.json()

            if not data:
                return {"error": "query_knowledge returned an empty response."}
            return {"result": data}

        except requests.exceptions.ConnectionError:
            return {"error": "Cannot connect to LPI server. Is it running on localhost:3000?"}
        except requests.exceptions.Timeout:
            if attempt <= retries:
                print(f"  ⏳ Timeout on attempt {attempt}, retrying...")
                time.sleep(1)
                continue
            return {"error": "query_knowledge timed out after multiple attempts."}
        except requests.exceptions.HTTPError as e:
            return {"error": f"query_knowledge HTTP error: {e.response.status_code} - {e.response.text}"}
        except ValueError:
            return {"error": "query_knowledge returned invalid JSON."}
        except Exception as e:
            return {"error": f"query_knowledge unexpected error: {str(e)}"}

    return {"error": "query_knowledge failed after all retries."}


def get_insights(scenario: str, retries: int = 2) -> dict:
    """
    Fetch insights from LPI for a given scenario.
    Retries on transient failures. Returns a dict with 'result' key on success,
    or 'error' key on failure.
    """
    for attempt in range(1, retries + 2):
        try:
            res = requests.post(
                f"{BASE_URL}/get_insights",
                json={"scenario": scenario, "tier": "free"},
                timeout=10
            )
            res.raise_for_status()
            data = res.json()

            if not data:
                return {"error": "get_insights returned an empty response."}
            return {"result": data}

        except requests.exceptions.ConnectionError:
            return {"error": "Cannot connect to LPI server. Is it running on localhost:3000?"}
        except requests.exceptions.Timeout:
            if attempt <= retries:
                print(f"  ⏳ Timeout on attempt {attempt}, retrying...")
                time.sleep(1)
                continue
            return {"error": "get_insights timed out after multiple attempts."}
        except requests.exceptions.HTTPError as e:
            return {"error": f"get_insights HTTP error: {e.response.status_code} - {e.response.text}"}
        except ValueError:
            return {"error": "get_insights returned invalid JSON."}
        except Exception as e:
            return {"error": f"get_insights unexpected error: {str(e)}"}

    return {"error": "get_insights failed after all retries."}


# ---------------------------
# INPUT PARSING
# ---------------------------

def parse_options(user_input: str) -> tuple:
    """
    Splits 'X vs Y' into (X, Y). Returns (input, None) if no 'vs' found.
    """
    lower = user_input.lower()
    if " vs " in lower:
        idx = lower.index(" vs ")
        option1 = user_input[:idx].strip()
        option2 = user_input[idx + 4:].strip()
        if option1 and option2:
            return option1, option2
    return user_input.strip(), None


# ---------------------------
# EXTRACT USABLE FIELDS FROM LPI RESPONSES
# ---------------------------

def extract_summary(data, label: str) -> str:
    """
    Tries to pull a human-readable string from LPI response dicts.
    Handles common shapes: {summary:...}, {text:...}, {answer:...}, plain string, etc.
    Falls back to the raw dict if nothing recognizable is found.
    """
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        for key in ("summary", "text", "answer", "content", "description", "message"):
            if key in data and isinstance(data[key], str):
                return data[key]
        return str(data)
    if isinstance(data, list):
        parts = [extract_summary(item, label) for item in data[:3]]
        return "\n  • " + "\n  • ".join(parts)
    return f"(Unrecognized response format from {label})"


def extract_tradeoff_signals(knowledge_result: dict, insights_result: dict, option1: str, option2) -> dict:
    """
    Derives actual signal data from tool responses to drive recommendations.
    Returns a signals dict used in decision logic.
    """
    signals = {
        "salary_lean": None,
        "stability_lean": None,
        "interest_neutral": True,
    }

    combined_text = (
        str(knowledge_result.get("result", "")) +
        str(insights_result.get("result", ""))
    ).lower()

    high_salary_keywords = ["high salary", "high pay", "lucrative", "well-paid", "compensation", "six figure"]
    if option2:
        for kw in high_salary_keywords:
            if kw in combined_text:
                idx = combined_text.find(kw)
                context = combined_text[max(0, idx - 100): idx + 100]
                if option1.lower() in context:
                    signals["salary_lean"] = "option1"
                elif option2.lower() in context:
                    signals["salary_lean"] = "option2"

    stability_keywords = ["stable", "stability", "recession-proof", "consistent demand", "job security"]
    for kw in stability_keywords:
        if kw in combined_text:
            idx = combined_text.find(kw)
            context = combined_text[max(0, idx - 100): idx + 100]
            if option2 and option2.lower() in context:
                signals["stability_lean"] = "option2"
            elif option1.lower() in context:
                signals["stability_lean"] = "option1"

    return signals


# ---------------------------
# MAIN AGENT
# ---------------------------

def decision_agent():
    print("🤖 Decision Tradeoff Agent\n")

    user_query = input("Enter your decision (e.g., AI vs Web Dev): ").strip()
    if not user_query:
        print("❌ Please enter a valid decision.")
        return

    if len(user_query) > 200:
        print("❌ Input too long. Please keep it under 200 characters.")
        return

    option1, option2 = parse_options(user_query)

    print("\nWhat matters most to you?")
    print("1. Salary")
    print("2. Interest")
    print("3. Stability")

    priority_input = input("Choose (1/2/3): ").strip()
    priority_map = {"1": "salary", "2": "interest", "3": "stability"}

    if priority_input not in priority_map:
        print("⚠️  Invalid choice. Defaulting to Interest.")
        priority = "interest"
    else:
        priority = priority_map[priority_input]

    # -------- ACTUAL TOOL CALLS --------
    print("\n🔍 Querying LPI knowledge base...")
    knowledge = query_knowledge(user_query)

    print("💡 Fetching LPI insights...")
    insights = get_insights(user_query)

    knowledge_ok = "result" in knowledge
    insights_ok = "result" in insights

    if not knowledge_ok and not insights_ok:
        print("\n⚠️  Both LPI tools failed. Cannot provide a data-driven recommendation.")
        print(f"   Knowledge error : {knowledge.get('error')}")
        print(f"   Insights error  : {insights.get('error')}")
        print("\nPlease verify the LPI server is running and try again.")
        return

    # -------- DISPLAY RAW TOOL OUTPUT --------
    print("\n📊 Decision Analysis\n")
    print("─" * 50)

    print("📘 Knowledge (from LPI):")
    if not knowledge_ok:
        print(f"  ⚠️  {knowledge['error']}")
    else:
        print(f"  {extract_summary(knowledge['result'], 'query_knowledge')}")

    print("\n💡 Insights (from LPI):")
    if not insights_ok:
        print(f"  ⚠️  {insights['error']}")
    else:
        print(f"  {extract_summary(insights['result'], 'get_insights')}")

    print("─" * 50)

    # -------- DERIVE SIGNALS FROM REAL DATA --------
    signals = extract_tradeoff_signals(knowledge, insights, option1, option2)

    # -------- TRADEOFF COMPARISON --------
    if option2:
        print(f"\n⚖️  Tradeoff: {option1}  vs  {option2}")

        knowledge_text = extract_summary(knowledge.get("result", {}), "knowledge") if knowledge_ok else ""
        insights_text = extract_summary(insights.get("result", {}), "insights") if insights_ok else ""

        def option_mentions(opt: str) -> str:
            sentences = (knowledge_text + " " + insights_text).replace("\n", " ").split(". ")
            relevant = [s.strip() for s in sentences if opt.lower() in s.lower() and len(s.strip()) > 10]
            if relevant:
                return "\n    → " + "\n    → ".join(relevant[:3])
            return "\n    → No specific data retrieved for this option."

        print(f"\n  🔹 {option1}:{option_mentions(option1)}")
        print(f"\n  🔹 {option2}:{option_mentions(option2)}")

    # -------- PRIORITY-DRIVEN RECOMMENDATION (DATA-GROUNDED) --------
    print(f"\n🎯 Recommendation based on your priority: {priority.upper()}")

    if priority == "salary":
        if signals["salary_lean"] == "option1":
            print(f"  → LPI data suggests {option1} has stronger salary signals.")
        elif signals["salary_lean"] == "option2" and option2:
            print(f"  → LPI data suggests {option2} has stronger salary signals.")
        else:
            print("  → LPI data did not return a clear salary signal for either option.")
            print("    Consider cross-referencing with salary aggregators (levels.fyi, Glassdoor).")

    elif priority == "interest":
        print("  → Interest is personal and LPI cannot measure it directly.")
        print("    Use the knowledge and insights above to see which field aligns with problems you enjoy solving.")

    elif priority == "stability":
        if signals["stability_lean"] == "option1":
            print(f"  → LPI data suggests {option1} has stronger stability signals.")
        elif signals["stability_lean"] == "option2" and option2:
            print(f"  → LPI data suggests {option2} has stronger stability signals.")
        else:
            print("  → LPI data did not return a clear stability signal.")
            print("    Look for consistent hiring trends and low automation-risk scores as proxies.")

    # -------- FINAL RECOMMENDATION --------
    print("\n✅ Final Recommendation:")
    if knowledge_ok or insights_ok:
        print("  Use the LPI data above — not just this summary — to validate your decision.")
    print("  Align your choice with your stated priority and revisit as market conditions evolve.")

    print("\n📌 Sources:")
    print(f"  - query_knowledge (LPI) — {'✅ succeeded' if knowledge_ok else '❌ failed'}")
    print(f"  - get_insights    (LPI) — {'✅ succeeded' if insights_ok else '❌ failed'}")
    print()


# ---------------------------
# RUN
# ---------------------------

if __name__ == "__main__":
    try:
        decision_agent()
    except KeyboardInterrupt:
        print("\n\n👋 Exiting agent. Goodbye!")
        sys.exit(0)
