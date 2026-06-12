import chromadb
import json
import sqlite3
from datetime import datetime

class IncidentStore:
    def __init__(self, persist_dir="data/chroma"):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="incidents",
            metadata={"hnsw:space": "cosine"}
        )
    
    def load_from_db(self):
        """Load incidents from SQLite into ChromaDB"""
        conn = sqlite3.connect("aegis_core.db")
        c = conn.cursor()
        incidents = c.execute("SELECT id, anomaly_description FROM incidents").fetchall()
        conn.close()
        
        for incident_id, anomaly_json in incidents:
            try:
                text = str(anomaly_json) if anomaly_json else ""
                self.collection.add(
                    ids=[str(incident_id)],
                    documents=[text],
                    metadatas=[{"incident_id": incident_id}]
                )
            except Exception as e:
                print(f"Failed to load incident {incident_id}: {e}")
        
        print(f"✅ Loaded {len(incidents)} incidents into ChromaDB")
    
    def search_similar(self, query: str, top_k: int = 3):
        """Find similar incidents"""
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        return results

if __name__ == "__main__":
    store = IncidentStore()
    store.load_from_db()