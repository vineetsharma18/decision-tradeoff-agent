import requests

BASE_URL = "http://localhost:3000"


# ---------------------------
# LPI TOOL CALLS (REAL)
# ---------------------------

def query_knowledge(query):
    try:
        res = requests.post(f"{BASE_URL}/query_knowledge", json={"query": query})
        res.raise_for_status()
        return res.json()
    except Exception as e:
        return {"error": f"query_knowledge failed: {str(e)}"}


def get_insights(scenario):
    try:
        res = requests.post(f"{BASE_URL}/get_insights", json={"scenario": scenario, "tier": "free"})
        res.raise_for_status()
        return res.json()
    except Exception as e:
        return {"error": f"get_insights failed: {str(e)}"}


# ---------------------------
# INPUT PARSING
# ---------------------------

def parse_options(user_input):
    if "vs" in user_input.lower():
        parts = user_input.lower().split("vs")
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()
    return user_input.strip(), None


# ---------------------------
# MAIN AGENT
# ---------------------------

def decision_agent():
    print("🤖 Decision Tradeoff Agent\n")

    user_query = input("Enter your decision (e.g., AI vs Web Dev): ").strip()

    # -------- ERROR HANDLING --------
    if not user_query:
        print("❌ Please enter a valid decision.")
        return

    option1, option2 = parse_options(user_query)

    print("\nWhat matters most to you?")
    print("1. Salary")
    print("2. Interest")
    print("3. Stability")

    priority = input("Choose (1/2/3): ").strip()

    if priority not in ["1", "2", "3"]:
        print("❌ Invalid choice. Defaulting to Interest.")
        priority = "2"

    # -------- TOOL CALLS --------
    print("\n🔍 Fetching knowledge from LPI...")
    knowledge = query_knowledge(user_query)

    print("💡 Fetching insights from LPI...")
    insights = get_insights(user_query)

    # -------- OUTPUT --------
    print("\n📊 Decision Analysis\n")

    # Knowledge Output
    print("📘 Knowledge (from LPI):")
    if "error" in knowledge:
        print("⚠️", knowledge["error"])
    else:
        print(knowledge)

    # Insights Output
    print("\n💡 Insights (from LPI):")
    if "error" in insights:
        print("⚠️", insights["error"])
    else:
        print(insights)

    # -------- TRADEOFF LOGIC --------
    if option2:
        print("\n⚖️ Tradeoff Comparison:")

        print(f"\n🔹 Option 1: {option1}")
        print("- Based on retrieved knowledge and trends")

        print(f"\n🔹 Option 2: {option2}")
        print("- Alternative path with different growth dynamics")

    # -------- PRIORITY DECISION --------
    print("\n🎯 Decision Based on Your Priority:")

    if priority == "1":
        print("→ Focus on higher compensation and market demand.")
    elif priority == "2":
        print("→ Choose what you enjoy — long-term consistency matters.")
    else:
        print("→ Prefer stable and predictable career paths.")

    # -------- FINAL RECOMMENDATION --------
    print("\n✅ Final Recommendation:")
    print("Align your choice with your priority while staying adaptable to future changes.")

    # -------- SOURCES --------
    print("\n📌 Sources:")
    print("- query_knowledge (LPI)")
    print("- get_insights (LPI)")


# ---------------------------
# RUN
# ---------------------------

if __name__ == "__main__":
    try:
        decision_agent()
    except KeyboardInterrupt:
        print("\n👋 Exiting agent. Goodbye!")
