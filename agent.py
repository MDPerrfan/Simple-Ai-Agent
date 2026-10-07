import json
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama

from restaurant_tools import (
    get_location_coordinates,
    find_restaurants
)
from config import AGENT_INFO

# ==========================================
# MODEL
# ==========================================

model = ChatOllama(
    model="smollm2:1.7b",
    temperature=0
)


# ==========================================
# STATE
# ==========================================

class AgentState(TypedDict, total=False):
    question: str

    place_name: str
    cuisine: str
    preference: str
    radius: int

    latitude: float
    longitude: float

    restaurants: list

    intent: str

    answer: str


def route_intent(state: AgentState):

    question = state["question"].lower().strip()

    # ------------------------------------------
    # 1. Obvious questions about the assistant
    # ------------------------------------------

    about_patterns = [
        "who are you",
        "what are you",
        "who built you",
        "who made you",
        "who created you",
        "who developed you",
        "your creator",
        "your developer",
        "your purpose",
        "what do you do",
        "how do you work",
        "what data do you use",
        "data source"
    ]

    if any(pattern in question for pattern in about_patterns):
        print("\nIntent: about_agent")
        return {"intent": "about_agent"}

    # ------------------------------------------
    # 2. Obvious restaurant-related questions
    # ------------------------------------------

    restaurant_words = [
        "restaurant",
        "restaurants",
        "food",
        "eat",
        "dining",
        "cuisine",
        "pizza",
        "burger",
        "cafe",
        "coffee",
        "breakfast",
        "lunch",
        "dinner"
    ]

    if any(word in question for word in restaurant_words):
        print("\nIntent: restaurant_search")
        return {"intent": "restaurant_search"}

    # ------------------------------------------
    # 3. Ambiguous request → ask LLM
    # ------------------------------------------

    prompt = f"""
Classify this message.

Message:
{state["question"]}

Choose exactly one:

restaurant_search
about_agent
general

Return ONLY the category.
"""

    response = model.invoke(prompt)

    intent = response.content.strip().lower()

    if intent not in {
        "restaurant_search",
        "about_agent",
        "general"
    }:
        intent = "general"

    print(f"\nIntent: {intent}")

    return {"intent": intent}
# ==========================================
# NODE 1: UNDERSTAND USER REQUEST
# ==========================================

def understand_request(state: AgentState):

    prompt = f"""
Extract restaurant search information from the user's question.

User question:
{state["question"]}

Return ONLY valid JSON.

Format:
{{
    "place_name": "location mentioned by user",
    "cuisine": "requested cuisine or any",
    "preference": "other requirement or none",
    "radius": 1000
}}

Rules:
- Do not explain anything.
- If no cuisine is specified, use "any".
- If no preference is specified, use "none".
- Radius must be in meters.
- If the user does not specify a radius, use 1000.
"""

    response = model.invoke(prompt)

    try:
        data = json.loads(response.content)

    except json.JSONDecodeError:
        raise ValueError(
            f"Model returned invalid JSON:\n{response.content}"
        )

    print("\nUnderstood request:")
    print(data)

    return data

def answer_about_agent(state: AgentState):

    prompt = f"""
You are {AGENT_INFO["name"]}.

Creator: {AGENT_INFO["creator"]}

Purpose:
{AGENT_INFO["purpose"]}

Data source:
{AGENT_INFO["data_source"]}

Limitations:
{AGENT_INFO["limitations"]}

User asked:
{state["question"]}

Answer naturally and concisely.

Use ONLY the information above.
Do not invent information about yourself or your creator.
"""

    response = model.invoke(prompt)

    return {"answer": response.content}

def answer_general(state: AgentState):

    return {
        "answer": (
            "I'm an AI Dining Assistant focused on restaurant "
            "discovery and dining-related questions. Ask me to find "
            "restaurants by location, cuisine, or opening preference."
        )
    }
# ==========================================
# NODE 2: GEOCODE
# ==========================================

def geocode_location(state: AgentState):

    print(f"\nFinding location: {state['place_name']}")

    location = get_location_coordinates.invoke({
        "place_name": state["place_name"]
    })

    if "error" in location:
        raise ValueError(location["error"])

    print(
        f"Coordinates: "
        f"{location['latitude']}, "
        f"{location['longitude']}"
    )

    return {
        "latitude": location["latitude"],
        "longitude": location["longitude"]
    }


# ==========================================
# NODE 3: LIVE RESTAURANT SEARCH
# ==========================================

def search_restaurants(state: AgentState):

    restaurants = find_restaurants.invoke({
        "latitude": state["latitude"],
        "longitude": state["longitude"],
        "radius": state["radius"]
    })

    print(f"\nFound {len(restaurants)} live restaurants.")

    return {
        "restaurants": restaurants
    }

def filter_restaurants(state: AgentState):

    cuisine = state.get("cuisine", "any").lower()
    preference = state.get("preference", "none").lower()

    filtered = []

    for restaurant in state["restaurants"]:

        restaurant_cuisine = restaurant.get(
            "cuisine", "Unknown"
        ).lower()

        hours = restaurant.get(
            "opening_hours", "Unknown"
        )

        # Cuisine filter
        if cuisine != "any":
            if cuisine not in restaurant_cuisine:
                continue

        # Late-night filter
        if "late" in preference:

            # Unknown hours cannot prove it stays open late
            if hours == "Unknown":
                continue

            # Simple first version:
            # keep restaurants containing closing times
            # 22:00 or later
            late_times = [
                "22:00", "22:30", "23:00",
                "23:30", "23:45", "24:00",
                "00:00", "01:00", "02:00"
            ]

            if not any(time in hours for time in late_times):
                continue

        filtered.append(restaurant)

    print(
        f"Filtered {len(state['restaurants'])} → "
        f"{len(filtered)} restaurants."
    )

    return {
        "restaurants": filtered
    }
def recommend_restaurants(state: AgentState):

    restaurants = state["restaurants"]

    if not restaurants:
        return {
            "answer": (
                "I couldn't find any restaurants matching "
                "all of your requirements."
            )
        }

    # Build clean context for the LLM
    context = "\n".join(
        [
            f"- Name: {r.get('name')}, "
            f"Cuisine: {r.get('cuisine')}, "
            f"Opening Hours: {r.get('opening_hours')}, "
            f"Phone: {r.get('phone')}, "
            f"Website: {r.get('website')}"
            for r in restaurants
        ]
    )

    prompt = f"""
You are an AI dining assistant.

User asked:
{state["question"]}

The following restaurants have already been filtered
to match the user's requirements:

{context}

Give the user a concise and useful recommendation.

Rules:
- Use ONLY the information above.
- Never invent ratings, reviews, prices or facts.
- Do not claim one restaurant is "better" unless the data supports it.
- Mention useful differences such as opening hours.
- Recommend 3 to 5 options when possible.
- If information is unknown, do not guess.
"""

    response = model.invoke(prompt)

    return {
        "answer": response.content
    }
# ==========================================
# BUILD GRAPH
# ==========================================

builder = StateGraph(AgentState)
builder.add_node("route_intent", route_intent)
builder.add_node("answer_about_agent", answer_about_agent)
builder.add_node("answer_general", answer_general)

builder.add_node("understand_request", understand_request)
builder.add_node("geocode_location", geocode_location)
builder.add_node("search_restaurants", search_restaurants)
builder.add_node(
    "recommend_restaurants",
    recommend_restaurants
)

builder.add_edge(START, "route_intent")
def choose_path(state: AgentState):

    if state["intent"] == "restaurant_search":
        return "restaurant"

    if state["intent"] == "about_agent":
        return "about"

    return "general"


builder.add_conditional_edges(
    "route_intent",
    choose_path,
    {
        "restaurant": "understand_request",
        "about": "answer_about_agent",
        "general": "answer_general"
    }
)

builder.add_edge("answer_about_agent", END)
builder.add_edge("answer_general", END)
builder.add_edge("understand_request", "geocode_location")

builder.add_node(
    "filter_restaurants",
    filter_restaurants
)

builder.add_edge("geocode_location", "search_restaurants")
builder.add_edge("search_restaurants", "filter_restaurants")
builder.add_edge(
    "filter_restaurants",
    "recommend_restaurants"
)

builder.add_edge(
    "recommend_restaurants",
    END
)
restaurant_graph = builder.compile()

# ==========================================
# TEST
# ==========================================

if __name__ == "__main__":

    question = input("\nAsk: ")

    result = restaurant_graph.invoke({
        "question": question
    })

    print("\n========== AI ANSWER ==========")
    print(result["answer"])
    print("================================")