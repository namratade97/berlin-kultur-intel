import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from qdrant_client import QdrantClient
from google import genai
from google.genai import types
from typing import List, Optional
import traceback
from sqlalchemy import create_engine, text
import litellm
import os
from fastapi.middleware.cors import CORSMiddleware


client_qdrant = QdrantClient(url="http://localhost:6333")
COLLECTION_NAME = "berlin_events"

# We keep the native Gemini client for embeddings
client_gemini_embed = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Model Fallback Chain
MODEL_LIST = [
    {"model": "gemini/gemini-2.0-flash-lite", "api_key": os.getenv("GOOGLE_API_KEY")},
    {"model": "groq/llama-3.3-70b-versatile", "api_key": os.getenv("GROQ_API_KEY")},
    {"model": "openrouter/meta-llama/llama-3.1-8b-instruct", "api_key": os.getenv("OPENROUTER_API_KEY")},
    {"model": "cerebras/llama3.1-8b", "api_key": os.getenv("CEREBRAS_API_KEY")},
    {"model": "sambanova/Meta-Llama-3.1-8B-Instruct", "api_key": os.getenv("SAMBANOVA_API_KEY")}
]

engine = create_engine("sqlite:///./berlin_history.db")

def sync_qdrant_to_sql():
    print("Syncing Qdrant vault to SQL archive...")
    points, _ = client_qdrant.scroll(collection_name=COLLECTION_NAME, limit=100, with_payload=True)
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS historical_events"))
        conn.execute(text("""
            CREATE TABLE historical_events (
                id INTEGER PRIMARY KEY,
                eventName TEXT, district TEXT, venueName TEXT, collection TEXT, url TEXT, quality_status TEXT
            )
        """))
        for p in points:
            pay = p.payload
            conn.execute(text("""
                INSERT INTO historical_events (eventName, district, venueName, collection, url, quality_status)
                VALUES (:eventName, :district, :venueName, :collection, :url, :quality_status)
            """), {
                "eventName": pay.get("eventName"), "district": pay.get("district"),
                "venueName": pay.get("venueName"), "collection": pay.get("Collection"),
                "url": pay.get("URL"), "quality_status": pay.get("quality_status")
            })
        conn.commit()

sync_qdrant_to_sql()

# DATA MODELS
@strawberry.type
class Event:
    eventName: str
    venueName: str
    district: str
    summary: str
    lat: float
    lng: float
    vibeProfile: List[str]
    qualityStatus: str
    url: Optional[str]
    collection: Optional[str]

@strawberry.type
class AgentResponse:
    answer: str
    matches: List[Event]

# HELPER FUNCTIONS

def get_llm_completion(prompt: str, system_instruction: str = "You are a helpful assistant."):
    """Tries models in order. If one fails, it logs and moves to the next."""
    for model_cfg in MODEL_LIST:
        if not model_cfg["api_key"]: continue
        try:
            response = litellm.completion(
                model=model_cfg["model"],
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                api_key=model_cfg["api_key"],
                timeout=10 # Not hanging the UI
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Model {model_cfg['model']} failed. Moving to next...")
            continue
    # If we reach here, every single provider failed
    raise Exception("All LLM providers exhausted or rate-limited.")

def get_qdrant_matches(query_text: str, limit: int = 5) -> List[Event]:
    embedding_result = client_gemini_embed.models.embed_content(
        model="gemini-embedding-001",
        contents=query_text,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
    )
    query_vector = embedding_result.embeddings[0].values
    search_results = client_qdrant.query_points(
        collection_name=COLLECTION_NAME, query=query_vector, limit=limit, with_payload=True
    ).points

    events = []
    for hit in search_results:
        pay = hit.payload
        # print(f"DEBUG: Qdrant Payload for {pay.get('eventName')}: {pay.keys()}")

        events.append(Event(
            eventName=pay.get("eventName") or pay.get("EventName") or "Unknown Event",
            venueName=pay.get("venueName") or pay.get("VenueName") or "",
            district=pay.get("district") or pay.get("District") or "",
            summary=pay.get("summary") or pay.get("Summary") or "",
            lat=float(pay.get("lat", 0.0)),
            lng=float(pay.get("lng", 0.0)),
            vibeProfile=pay.get("vibeProfile", []),
            qualityStatus=pay.get("quality_status", "unverified"),
            url=pay.get("URL") or pay.get("url"),
            collection=pay.get("Collection") or pay.get("collection")
        ))
    return events

# GRAPHQL QUERY LOGIC

@strawberry.type
class Query:
    @strawberry.field
    def search_events(self, query_text: str) -> List[Event]:
        return get_qdrant_matches(query_text)

    @strawberry.field
    def ask_agent(self, question: str) -> AgentResponse:
        # Step 1: Always trying to get matches first (Reliable Embedding Quota)
        try:
            matched_events = get_qdrant_matches(question, limit=3)
        except Exception as e:
            print(f"Embedding error: {e}")
            matched_events = []

        # Step 2: Routing & Generation inside a Safety Exception Block
        try:
            analytical_triggers = ["how many", "count", "total", "average", "history"]
            is_analytical = any(t in question.lower() for t in analytical_triggers)

            if is_analytical:
                # SQL PATH
                schema_info = """
                Table: historical_events
                Columns: eventName, district, venueName, collection, url, quality_status
                Note: The 'collection' column contains strings like 'FebruaryEvents' or 'MarchEvents', the type of event can be found here also, like 'FestivalEvents' or 'ExhibitionEvents'.
                """
                sql_prompt = f"Given {schema_info}, write a SQLite query for: {question}. Output raw SQL only."
                sql_query = get_llm_completion(sql_prompt, "You are a SQL expert.")
                
                # Clean the SQL
                sql_query = sql_query.strip().replace("```sql", "").replace("```", "")
                
                with engine.connect() as conn:
                    db_res = conn.execute(text(sql_query)).fetchall()
                    summary_prompt = f"User asked: {question}. Data: {str(db_res)}. Summarize shortly."
                    answer_text = get_llm_completion(summary_prompt, "You are a data assistant.")
            else:
                # RAG PATH
                context = "\n".join([f"- {e.eventName}: {e.summary}" for e in matched_events])
                prompt = f"Context:\n{context}\n\nQuestion: {question}"
                answer_text = get_llm_completion(prompt, "You are a witty Berlin guide.")

        except Exception as e:
            print(f"CRITICAL AGENT ERROR: {traceback.format_exc()}")
            answer_text = "Sorry, at this moment my analytical brain is offline (all LLMs rate-limited), but I've pulled these locations for you!"

        return AgentResponse(answer=answer_text, matches=matched_events)

# FASTAPI SETUP
schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)
app = FastAPI(title="Berlin Kultur Intel")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React's address
    allow_credentials=True,
    allow_methods=["*"],                      # allowing OPTIONS, POST, etc.
    allow_headers=["*"],
)
app.include_router(graphql_app, prefix="/graphql")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)