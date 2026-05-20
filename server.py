from mcp.server.fastmcp import FastMCP
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from datetime import datetime

# --- Database setup (same as vector.py but self-contained) ---
embeddings = OllamaEmbeddings(model="mxbai-embed-large")

vector_store = Chroma(
    collection_name="restaurant_reviews",
    persist_directory="./chrome_langchain_db",
    embedding_function=embeddings
)

retriever = vector_store.as_retriever(search_kwargs={"k": 5})

# --- MCP Server ---
mcp = FastMCP("restaurant-reviews")  # this is the server name


@mcp.tool()
def review_retriever_tool(query: str) -> str:
    """
    Search the restaurant review database for reviews relevant to a query.
    Use this to find what customers say about specific topics like food quality,
    service, ambience, prices, wait times, or specific menu items.
    Always use this tool first when answering questions about the restaurant.
    """
    docs = retriever.invoke(query)
    
    # Add this block to print what was retrieved
    print("\n--- Retrieved Reviews ---")
    for i, doc in enumerate(docs, 1):
        print(f"Review {i}: {doc.page_content[:100]}...")
    print("------------------------\n")

    if not docs:
        return "No relevant reviews found."

    results = []
    for i, doc in enumerate(docs, 1):
        rating = doc.metadata.get("rating", "N/A")
        date = doc.metadata.get("date", "N/A")
        results.append(
            f"Review {i} (Rating: {rating}/5, Date: {date}):\n{doc.page_content}"
        )
    return "\n\n---\n\n".join(results)


@mcp.tool()
def rating_filter_tool(min_rating: float, max_rating: float = 5.0) -> str:
    """
    Retrieve reviews filtered by a star rating range.
    Use this when the user asks about highly-rated experiences (use min_rating=4),
    negative experiences or complaints (use max_rating=2), or a specific rating range.
    min_rating: minimum star rating (1.0 to 5.0)
    max_rating: maximum star rating (1.0 to 5.0), defaults to 5.0
    """
    all_docs = vector_store.get(include=["documents", "metadatas"])

    filtered = []
    for doc_text, metadata in zip(all_docs["documents"], all_docs["metadatas"]):
        rating = float(metadata.get("rating", 0))
        if min_rating <= rating <= max_rating:
            filtered.append((doc_text, metadata, rating))

    if not filtered:
        return f"No reviews found with ratings between {min_rating} and {max_rating}."

    filtered.sort(key=lambda x: x[2], reverse=(min_rating >= 3))
    top = filtered[:5]

    results = []
    for doc_text, metadata, rating in top:
        date = metadata.get("date", "N/A")
        results.append(f"Rating: {rating}/5 | Date: {date}\n{doc_text}")

    return (
        f"Found {len(filtered)} reviews in range {min_rating}-{max_rating}. Showing top 5:\n\n"
        + "\n\n---\n\n".join(results)
    )


@mcp.tool()
def review_stats_tool() -> str:
    """
    Calculate overall statistics about all restaurant reviews.
    Use this when the user asks about the restaurant's overall rating, how many
    reviews exist, rating distributions, or general performance trends.
    """
    all_docs = vector_store.get(include=["metadatas"])

    if not all_docs["metadatas"]:
        return "No reviews found in the database."

    ratings = [float(m["rating"]) for m in all_docs["metadatas"] if "rating" in m]
    if not ratings:
        return "No rating data available."

    total = len(ratings)
    avg = sum(ratings) / total
    distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for r in ratings:
        bucket = int(round(r))
        if bucket in distribution:
            distribution[bucket] += 1

    dist_str = "\n".join(
        [f"  {stars} stars: {count} reviews ({count/total*100:.1f}%)"
         for stars, count in sorted(distribution.items(), reverse=True)]
    )

    return (
        f"Total reviews: {total}\n"
        f"Average rating: {avg:.2f}/5.0\n"
        f"Highest rating: {max(ratings)}/5\n"
        f"Lowest rating: {min(ratings)}/5\n"
        f"Rating distribution:\n{dist_str}"
    )


@mcp.tool()
def review_trend_tool() -> str:
    """
    Analyse how reviews and ratings have changed over time by looking at dates.
    Use this when asked if quality or service is improving or declining over time,
    or any question involving trends, recent vs old reviews, or time periods.
    """
    all_docs = vector_store.get(include=["metadatas"])

    dated = []
    for m in all_docs["metadatas"]:
        try:
            date = datetime.strptime(m["date"], "%Y-%m-%d")
            dated.append((date, float(m["rating"])))
        except Exception:
            continue

    if not dated:
        return "No valid date data found in reviews."

    dated.sort(key=lambda x: x[0])
    n = len(dated)
    early  = dated[:n//3]
    mid    = dated[n//3:2*n//3]
    recent = dated[2*n//3:]

    def avg(group):
        return sum(r for _, r in group) / len(group) if group else 0

    early_avg  = avg(early)
    mid_avg    = avg(mid)
    recent_avg = avg(recent)
    trend = "improving" if recent_avg > early_avg else "declining"
    diff  = abs(recent_avg - early_avg)

    return (
        f"Total reviews analysed: {n}\n"
        f"Date range: {dated[0][0].date()} to {dated[-1][0].date()}\n\n"
        f"Early reviews  ({dated[0][0].date()} to {dated[n//3][0].date()}): avg {early_avg:.2f}/5\n"
        f"Middle reviews ({dated[n//3][0].date()} to {dated[2*n//3][0].date()}): avg {mid_avg:.2f}/5\n"
        f"Recent reviews ({dated[2*n//3][0].date()} to {dated[-1][0].date()}): avg {recent_avg:.2f}/5\n\n"
        f"Trend: Ratings are {trend} over time (difference of {diff:.2f} stars)"
    )


# Run the server
if __name__ == "__main__":
    mcp.settings.host = "127.0.0.1"
    mcp.settings.port = 8000
    mcp.run(transport="sse")
    print("MCP server running on http://127.0.0.1:8000")