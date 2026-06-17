"""Vector memory with RAG, long-term context, and semantic search."""
import sqlite3
import json
import hashlib
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import logging
from enum import Enum

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False
    logging.warning("sentence_transformers not available, using basic TF-IDF")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryType(Enum):
    CONVERSATION = "conversation"
    FACT = "fact"
    CODE = "code"
    DOCUMENT = "document"
    EPHEMERAL = "ephemeral"
    IMPORTANT = "important"

class VectorMemory:
    def __init__(self, db_path: str = "data/memory.db", embedding_model: str = "all-MiniLM-L6-v2"):
        self.db_path = db_path
        self.embedding_model = embedding_model
        self._init_db()
        
        if EMBEDDING_AVAILABLE:
            self.encoder = SentenceTransformer(embedding_model)
            self.embedding_dim = self.encoder.get_sentence_embedding_dimension()
        else:
            self.encoder = None
            self.embedding_dim = 384  # Default dimension for fallback
            logger.warning("Using basic TF-IDF embeddings (install sentence-transformers for better results)")
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main memory table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            embedding BLOB,
            memory_type TEXT NOT NULL,
            tags TEXT,
            metadata TEXT,
            importance REAL DEFAULT 1.0,
            access_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        )
        """)
        
        # Conversation history
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            role TEXT,
            content TEXT,
            tokens INTEGER,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_type ON memory(memory_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_tags ON memory(tags)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id)")
        
        conn.commit()
        conn.close()
    
    def store(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.FACT,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
        importance: float = 1.0,
        ttl_hours: Optional[int] = None,
    ) -> str:
        """Store content with optional embedding."""
        memory_id = hashlib.sha256(f"{content}{datetime.now().timestamp()}".encode()).hexdigest()[:16]
        
        # Generate embedding if encoder available
        embedding = None
        if self.encoder:
            embedding_array = self.encoder.encode(content)
            embedding = embedding_array.tobytes()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        expires_at = None
        if ttl_hours:
            expires_at = datetime.now().timestamp() + (ttl_hours * 3600)
        
        cursor.execute("""
        INSERT INTO memory (id, content, embedding, memory_type, tags, metadata, importance, expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            memory_id,
            content,
            embedding,
            memory_type.value,
            json.dumps(tags) if tags else None,
            json.dumps(metadata) if metadata else None,
            importance,
            expires_at,
        ))
        
        conn.commit()
        conn.close()
        return memory_id
    
    def retrieve(
        self,
        query: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 10,
        min_similarity: float = 0.3,
    ) -> List[Dict]:
        """Retrieve memories similar to query using semantic search."""
        if not self.encoder:
            # Fallback: basic keyword search
            return self._keyword_search(query, memory_type, limit)
        
        # Encode query
        query_embedding = self.encoder.encode(query)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all embeddings
        cursor.execute("""
        SELECT id, content, embedding, memory_type, tags, metadata, importance
        FROM memory
        WHERE embedding IS NOT NULL
        AND (expires_at IS NULL OR expires_at > ?)
        """, (datetime.now().timestamp(),))
        
        results = []
        for row in cursor.fetchall():
            mem_id, content, embedding_blob, mem_type, tags_json, metadata_json, importance = row
            
            if memory_type and mem_type != memory_type.value:
                continue
            
            # Calculate cosine similarity
            embedding_array = np.frombuffer(embedding_blob, dtype=np.float32)
            similarity = self._cosine_similarity(query_embedding, embedding_array)
            
            if similarity >= min_similarity:
                results.append({
                    "id": mem_id,
                    "content": content,
                    "similarity": float(similarity),
                    "memory_type": mem_type,
                    "tags": json.loads(tags_json) if tags_json else [],
                    "metadata": json.loads(metadata_json) if metadata_json else {},
                    "importance": importance,
                })
        
        # Sort by similarity * importance
        results.sort(key=lambda x: x["similarity"] * x["importance"], reverse=True)
        
        # Update access count
        for result in results[:limit]:
            cursor.execute("""
            UPDATE memory 
            SET access_count = access_count + 1, last_accessed = CURRENT_TIMESTAMP
            WHERE id = ?
            """, (result["id"],))
        
        conn.commit()
        conn.close()
        return results[:limit]
    
    def _keyword_search(self, query: str, memory_type: Optional[MemoryType], limit: int) -> List[Dict]:
        """Basic keyword search fallback."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query_words = query.lower().split()
        
        cursor.execute("""
        SELECT id, content, memory_type, tags, metadata, importance
        FROM memory
        WHERE (expires_at IS NULL OR expires_at > ?)
        """, (datetime.now().timestamp(),))
        
        results = []
        for row in cursor.fetchall():
            mem_id, content, mem_type, tags_json, metadata_json, importance = row
            
            if memory_type and mem_type != memory_type.value:
                continue
            
            # Simple word matching
            content_lower = content.lower()
            score = 0
            for word in query_words:
                if word in content_lower:
                    score += 1
            
            if score > 0:
                results.append({
                    "id": mem_id,
                    "content": content,
                    "similarity": score / len(query_words),
                    "memory_type": mem_type,
                    "tags": json.loads(tags_json) if tags_json else [],
                    "metadata": json.loads(metadata_json) if metadata_json else {},
                    "importance": importance,
                })
        
        results.sort(key=lambda x: x["similarity"] * x["importance"], reverse=True)
        
        # Update access count
        for result in results[:limit]:
            cursor.execute("""
            UPDATE memory 
            SET access_count = access_count + 1, last_accessed = CURRENT_TIMESTAMP
            WHERE id = ?
            """, (result["id"],))
        
        conn.commit()
        conn.close()
        return results[:limit]
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def store_conversation(
        self,
        session_id: str,
        role: str,
        content: str,
        tokens: Optional[int] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """Store conversation message."""
        conv_id = hashlib.sha256(f"{session_id}{role}{content}{datetime.now().timestamp()}".encode()).hexdigest()[:16]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO conversations (id, session_id, role, content, tokens, metadata)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            conv_id,
            session_id,
            role,
            content,
            tokens,
            json.dumps(metadata) if metadata else None,
        ))
        
        conn.commit()
        conn.close()
        return conv_id
    
    def get_conversation_history(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict]:
        """Get conversation history for a session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT id, role, content, tokens, metadata, created_at
        FROM conversations
        WHERE session_id = ?
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """, (session_id, limit, offset))
        
        results = []
        for row in cursor.fetchall():
            conv_id, role, content, tokens, metadata_json, created_at = row
            results.append({
                "id": conv_id,
                "role": role,
                "content": content,
                "tokens": tokens,
                "metadata": json.loads(metadata_json) if metadata_json else {},
                "created_at": created_at,
            })
        
        conn.close()
        return list(reversed(results))  # Return in chronological order
    
    def cleanup_expired(self) -> int:
        """Remove expired memories. Returns number removed."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        DELETE FROM memory
        WHERE expires_at IS NOT NULL AND expires_at <= ?
        """, (datetime.now().timestamp(),))
        
        removed = cursor.rowcount
        conn.commit()
        conn.close()
        return removed
    
    def get_stats(self) -> Dict:
        """Get memory statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*), memory_type FROM memory GROUP BY memory_type")
        type_counts = {row[1]: row[0] for row in cursor.fetchall()}
        
        cursor.execute("SELECT COUNT(*) FROM conversations")
        conv_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT session_id) FROM conversations")
        session_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM memory WHERE embedding IS NOT NULL")
        embedded_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(access_count) FROM memory")
        total_accesses = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "memory_by_type": type_counts,
            "total_memories": sum(type_counts.values()),
            "conversation_messages": conv_count,
            "unique_sessions": session_count,
            "embedded_memories": embedded_count,
            "total_accesses": total_accesses,
        }

# Singleton instance
vector_memory = VectorMemory()