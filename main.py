from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from vector import retriever

from restaurant_tools import (
    find_restaurants,
    get_location_coordinates
)

# ==========================================
# MODEL
# ==========================================

model = ChatOllama(
    model="smollm2:1.7b",
    temperature=0
)


# ==========================================
# EXISTING RAG CHAIN
# ==========================================

template = """
You are a restaurant review assistant.

Answer the user's question ONLY using the provided restaurant reviews.
Do not invent information that is not present in the reviews.

Relevant reviews:
{reviews}

Question:
{question}

Give a concise answer and explain which review evidence supports it.

If the reviews do not contain enough information to answer the question,
say that clearly.
"""

prompt = ChatPromptTemplate.from_template(template)

rag_chain = prompt | model


# ==========================================
# LIVE RESTAURANT TOOL
# ==========================================

tools = [
    get_location_coordinates,
    find_restaurants
]
model_with_tools = model.bind_tools(tools)


# ==========================================
# MAIN LOOP
# ==========================================

print("\nAI Dining Assistant")
print("Type 'q' to quit.\n")

question = input("You: ")


while question.lower() != "q":

    # Ask the model whether it wants to use a tool
    response = model_with_tools.invoke(question)

    # ======================================
    # LIVE TOOL PATH
    # ======================================

    if response.tool_calls:

        for tool_call in response.tool_calls:

            print(f"\nCalling tool: {tool_call['name']}")
            print(f"Arguments: {tool_call['args']}")

            if tool_call["name"] == "find_restaurants":

                restaurants = find_restaurants.invoke(
                    tool_call["args"]
                )

                print(f"\nFound {len(restaurants)} live restaurants.")

                # Convert results into readable context for the LLM
                restaurant_context = "\n".join(
                    [
                        f"""
    Name: {r.get('name')}
    Cuisine: {r.get('cuisine')}
    Opening Hours: {r.get('opening_hours')}
    Phone: {r.get('phone')}
    Website: {r.get('website')}
    """
                        for r in restaurants
                    ]
                )

                # Ask the model to reason over the LIVE results
                final_prompt = f"""
    You are an AI dining assistant.

    The user asked:
    {question}

    Below are live restaurant results retrieved from OpenStreetMap:

    {restaurant_context}

    Answer the user's question using ONLY these results.

    Rules:
    - Do not invent ratings, prices, reviews, or other information.
    - Recommend only restaurants present in the results.
    - Explain briefly why each recommendation matches the request.
    - If the available data is insufficient, clearly say so.
    - Keep the answer concise.
    """

                final_response = model.invoke(final_prompt)

                print("\n========== AI ANSWER ==========")
                print(final_response.content)
                print("================================\n")


    question = input("\nYou: ")