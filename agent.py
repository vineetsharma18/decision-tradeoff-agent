import requests

BASE_URL = "http://localhost:3000"

def query_knowledge(query):
    return requests.post(f"{BASE_URL}/query_knowledge", json={"query": query}).json()

def get_insights(scenario):
    return requests.post(f"{BASE_URL}/get_insights", json={"scenario": scenario, "tier": "free"}).json()


def decision_agent():
    print("🤖 Decision Tradeoff Agent\n")

    user_query = input("Enter your decision (e.g., AI vs Web Dev): ")

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

    print("📘 Knowledge Summary:")
    print(knowledge.get("summary", "No summary available"))

    print("\n💡 Insights:")
    print(insights.get("summary", "No insights available"))

    print("\n⚖️ Tradeoff Analysis:")

    if priority == "1":
        print("- Focus on high-paying opportunities.")
    elif priority == "2":
        print("- Choose based on your interest and long-term satisfaction.")
    else:
        print("- Consider stable and consistent career paths.")

    print("\n🎯 Final Recommendation:")
    print("Choose the option that balances your priority with long-term growth.")

    print("\n📌 Sources:")
    print("- query_knowledge")
    print("- get_insights")


if __name__ == "__main__":
    decision_agent()
