import requests

BASE_URL = "http://localhost:3000"

def query_knowledge(query):
    return requests.post(f"{BASE_URL}/query_knowledge", json={"query": query}).json()

def get_insights(scenario):
    return requests.post(f"{BASE_URL}/get_insights", json={"scenario": scenario, "tier": "free"}).json()


def parse_options(user_input):
    # simple split like "AI vs Web Dev"
    if "vs" in user_input.lower():
        parts = user_input.lower().split("vs")
        return parts[0].strip(), parts[1].strip()
    return user_input, None


def decision_agent():
    print("🤖 Advanced Decision Tradeoff Agent\n")

    user_query = input("Enter your decision (e.g., AI vs Web Dev): ")

    option1, option2 = parse_options(user_query)

    print("\nWhat matters most to you?")
    print("1. Salary")
    print("2. Interest")
    print("3. Stability")
    priority = input("Choose (1/2/3): ")

    print("\n🔍 Fetching knowledge...")
    knowledge = query_knowledge(user_query)

    print("💡 Getting insights...")
    insights = get_insights(user_query)

    print("\n📊 Decision Analysis\n")

    #Knowledge 
    print("📘 Knowledge Summary:")
    print(knowledge.get("summary", "No knowledge available"))

    #Insights
    print("\n💡 Insights:")
    print(insights.get("summary", "No insights available"))

    #Structured Comparison
    if option2:
        print("\n⚖️ Tradeoff Comparison:")

        print(f"\n🔹 Option 1: {option1}")
        print("- Potential benefits based on knowledge trends")
        print("- Growth depends on consistent effort")

        print(f"\n🔹 Option 2: {option2}")
        print("- May offer different opportunities depending on market demand")
        print("- Learning curve may vary")

    #Priority-based reasoning
    print("\n🎯 Decision Based on Your Priority:")

    if priority == "1":
        print("→ Prioritize the option with higher market demand and compensation potential.")
    elif priority == "2":
        print("→ Choose the option you enjoy more, as long-term consistency matters most.")
    else:
        print("→ Choose the option with stable demand and predictable growth.")

    #Final Recommendation
    print("\n✅ Final Recommendation:")
    print("Make a decision that aligns your priority with long-term growth and adaptability.")

    #Sources
    print("\n📌 Sources:")
    print("- query_knowledge")
    print("- get_insights")


if __name__ == "__main__":
    decision_agent()