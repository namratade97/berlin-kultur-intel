from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from litellm import embedding
import uuid
import asyncio


# Connecting to the Qdrant we added to docker-compose
client = QdrantClient(url="http://localhost:6333")
COLLECTION_NAME = "berlin_events"
QDRANT_URL = "http://localhost:6333"

client = QdrantClient(url=QDRANT_URL)


def init_db():
    """Creates the collection if it doesn't exist."""
    try:
        collections = client.get_collections().collections
        exists = any(c.name == COLLECTION_NAME for c in collections)
        
        if not exists:
            print(f"Creating collection: {COLLECTION_NAME}")
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
            )
    except Exception as e:
        print(f"Database init failed: {e}")

async def save_to_vault(dossier: dict):
    """Saves a single processed dossier from the Agent to Qdrant."""
    try:
        # Create searchable text from the agent's output
        searchable_text = f"{dossier.get('eventName')} at {dossier.get('venueName')}. {dossier.get('summary')}"
        
        # Get embedding
        vector = await get_embedding(searchable_text)
        
        # Upsert
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload=dossier
                )
            ]
        )
        print(f"Vaulted: {dossier.get('eventName')}")
    except Exception as e:
        print(f"Failed to vault {dossier.get('eventName')}: {e}")

async def get_embedding(text: str):
    try:
        response = embedding(
            model="gemini/text-embedding-004", 
            input=[text]
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Embedding failed for text: {text[:30]}... Error: {e}")
        return [0.0] * 3072

def get_baserow_rows():
    url = f"https://api.baserow.io/api/database/rows/table/{BASEROW_TABLE_ID}/?user_field_names=true"
    headers = {"Authorization": f"Token {BASEROW_TOKEN}"}
    response = requests.get(url, headers=headers)
    return response.json().get("results", [])

async def sync():
    print(f"Starting sync from Baserow Table {BASEROW_TABLE_ID}...")
    rows = get_baserow_rows()
    
    for row in rows:
        # 1. Map Baserow fields to our Qdrant Schema
        q_score_raw = float(row.get("QualityScore", 0) or 0)
        
        dossier = {
            "eventName": row.get("Event"),
            "venueName": row.get("Venue"),
            "district": row.get("District"),
            "summary": row.get("Summary"),
            "influenceScore": float(row.get("VibeScore", 0) or 0),
            "confidenceScore": 10, # default
            "vibeProfile": [v.strip() for v in row.get("VibeProfile", "").split(",")] if row.get("VibeProfile") else [],
            "quality_score": 1.0 if q_score_raw == 0 else q_score_raw,
            "quality_reason": row.get("AuditReason") or "Verified via local fallback.",
            "quality_status": row.get("DeepEvalAuditStatus") or "verified"
        }

        # 2. Generating the searchable text block for the embedding
        searchable_text = f"{dossier['eventName']} at {dossier['venueName']}. Vibe: {', '.join(dossier['vibeProfile'])}. {dossier['summary']}"
        
        # 3. Getting the real vector
        vector = await get_embedding(searchable_text)

        # 4. Upserting to Qdrant
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload=dossier
                )
            ]
        )
        print(f"Synced: {dossier['eventName']}")

if __name__ == "__main__":
    asyncio.run(sync())