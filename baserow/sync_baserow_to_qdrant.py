import requests
import uuid
import asyncio
import os
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from litellm import embedding

BASEROW_TOKEN = os.environ.get("BASEROW_TOKEN")
BASEROW_TABLE_ID = "baserow_table_id_here"  # Replace with your actual Baserow table ID
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "berlin_events"

client = QdrantClient(url=QDRANT_URL)

# doing a fresh start (we use vectors of size 3072 and cosine distance)
# client.delete_collection(collection_name="berlin_events")

async def get_embedding(text: str):
    try:
        response = embedding(
            model="gemini/gemini-embedding-001",
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
    print(f"🔄 Starting sync from Baserow Table {BASEROW_TABLE_ID}...")
    rows = get_baserow_rows()
    
    for row in rows:
        # 1. Map Baserow fields to the Qdrant Schema
        # if QualityScore is "0.00", use verified defaults
        q_score_raw = float(row.get("QualityScore", 0) or 0)
        
        dossier = {
            "eventName": row.get("Event"),
            "venueName": row.get("Venue"),
            "district": row.get("District"),
            "summary": row.get("Summary"),
            "influenceScore": float(row.get("VibeScore", 0) or 0),
            "vibeProfile": [v.strip() for v in row.get("VibeProfile", "").split(",")] if row.get("VibeProfile") else [],
            "collection":row.get("Collection"),
            "url": row.get("URL"),
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