import chromadb
from chromadb.config import Settings
import hashlib
from datetime import datetime

class ChatMemoryStore:
    """User-specific long-term chat memory using ChromaDB."""
    
    def __init__(self, persist_dir="data/chat_memory"):
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        # We'll use one collection per user for isolation
        self._collections = {}
    
    def _get_user_collection(self, user_id: int):
        """Get or create a collection for a specific user."""
        collection_name = f"chat_memory_user_{user_id}"
        if collection_name not in self._collections:
            self._collections[collection_name] = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        return self._collections[collection_name]
    
    def add_message(self, user_id: int, session_id: int, role: str, content: str):
        """Store a chat message in long-term memory."""
        if not content or len(content.strip()) < 10:
            return  # Skip very short messages
        
        collection = self._get_user_collection(user_id)
        doc_id = hashlib.md5(f"{user_id}:{session_id}:{content[:50]}".encode()).hexdigest()
        
        try:
            collection.add(
                ids=[doc_id],
                documents=[content],
                metadatas=[{
                    "session_id": session_id,
                    "role": role,
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user_id
                }]
            )
        except Exception as e:
            print(f"Memory store error: {e}")
    
    def search_memories(self, user_id: int, query: str, top_k: int = 5) -> list:
        """Search user's past messages for relevant context."""
        if not query or len(query.strip()) < 5:
            return []
        
        collection = self._get_user_collection(user_id)
        if collection.count() == 0:
            return []
        
        try:
            results = collection.query(
                query_texts=[query],
                n_results=min(top_k, collection.count())
            )
            
            memories = []
            if results and results.get('ids') and results['ids'][0]:
                for i, doc_id in enumerate(results['ids'][0]):
                    memories.append({
                        "content": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i] if results.get('metadatas') else {},
                        "similarity": round(1 - results['distances'][0][i], 2) if results.get('distances') else 0
                    })
            
            return memories
        except Exception as e:
            print(f"Memory search error: {e}")
            return []
    
    def get_recent_memories(self, user_id: int, limit: int = 5) -> list:
        """Get most recent memories for the user."""
        collection = self._get_user_collection(user_id)
        if collection.count() == 0:
            return []
        
        try:
            results = collection.get(limit=limit)
            memories = []
            if results and results.get('ids'):
                for i, doc_id in enumerate(results['ids']):
                    memories.append({
                        "content": results['documents'][i],
                        "metadata": results['metadatas'][i] if results.get('metadatas') else {}
                    })
            return memories
        except:
            return []
    
    def clear_user_memory(self, user_id: int):
        """Delete all memories for a user."""
        collection_name = f"chat_memory_user_{user_id}"
        try:
            self.client.delete_collection(collection_name)
            if collection_name in self._collections:
                del self._collections[collection_name]
        except:
            pass