import asyncio
import warnings
warnings.filterwarnings("ignore")  # suppress deprecation warnings

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

model = ChatOllama(model="llama3.1:8b")

system_prompt = (
    "You are an expert assistant for a pizza restaurant.\n"
    "You help customers and staff by answering questions based on real customer reviews.\n\n"
    "You have access to four tools:\n"
    "- review_retriever_tool: searches reviews semantically — use this for most questions\n"
    "- rating_filter_tool: filters reviews by star rating — use for 'best'/'worst' type questions\n"
    "- review_stats_tool: gives overall stats — use for 'how is the restaurant overall' questions\n"
    "- review_trend_tool: analyses trends over time — use for improving/declining questions\n\n"
    "Always use at least one tool before answering. Base your answers on the review evidence.\n"
    "If a question requires multiple angles, use multiple tools. Think step by step."
)

async def main():
    # Connect once, keep the connection alive for all questions
    client = MultiServerMCPClient(
        {
            "restaurant-reviews": {
                "url": "http://127.0.0.1:8000/sse",
                "transport": "sse",
            }
        }
    )

    tools = await client.get_tools()

    agent = create_react_agent(
        model=model,
        tools=tools,
        prompt=system_prompt
    )

    print("=" * 50)
    print("  Pizza Restaurant Review Agent (MCP)")
    print("  Powered by LLaMA 3.1 + LangGraph + MCP")
    print("=" * 50)
    print("Ask anything about the restaurant. Type 'q' to quit.\n")
    print("Make sure server.py is running in another terminal!\n")

    # Single event loop, single client, single agent — all questions reuse them
    while True:
        print("\n" + "-" * 50)
        question = input("Your question: ").strip()
        print()

        if question.lower() == "q":
            print("Goodbye!")
            break

        if not question:
            continue

        try:
            print("Thinking...\n")
            response = await agent.ainvoke(
                {"messages": [HumanMessage(content=question)]},
                config={"recursion_limit": 10}
            )
            print(f"Agent: {response['messages'][-1].content}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())