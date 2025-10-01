import json
# import chromadb
from pinecone import Pinecone
import numpy as np
import os
from openai import OpenAI
from typing import List, Dict, Optional
import uuid
from ..models.rna_models import VectorSearchResponse, SimilarSequence


class RNAVectorDB:
    def __init__(self, model_name: str = "text-embedding-3-small"):
        self.model_name = model_name
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Connect to DB
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        INDEX_NAME = "rna-openai-embed"

        self.collection = pc.Index(INDEX_NAME)
    
    def _encode_sequence(self, sequence: str) -> List[float]:
        """Encoding an RNA sequence into a vector"""
        response = self.openai_client.embeddings.create(
            model=self.model_name,
            input=sequence
        )
        return response.data[0].embedding

    def search_similar(self, query_sequence: str, top_k: int = 5,
                    similarity_threshold: float = 0.5) -> VectorSearchResponse:
        """Searching for similar sequences"""
        # Embed user's RNA sequence 
        q_emb = self._encode_sequence(query_sequence)

        # RAG to Pinecone
        results = self.collection.query(vector=q_emb, top_k=top_k, include_metadata=True)

        similar_sequences = []

        if results and "matches" in results:
            for match in results["matches"]:
                seq_id = match.get("id")
                metadata = match.get("metadata", {})
                score = match.get("score", 0.0)

                # Optionally filter by threshold
                if score >= similarity_threshold:
                    similar_sequences.append(
                        SimilarSequence(
                            sequence=metadata.get("sequence", ""),  # store RNA sequence in metadata when inserting
                            sequence_id=seq_id,
                            similarity=score,   # Pinecone "score" is usually cosine similarity (0–1)
                            similarity_score=score,
                            metadata=metadata
                        )
                    )

        return VectorSearchResponse(
            query_sequence=query_sequence.upper(),
            results=similar_sequences,
            total_found=len(similar_sequences)
        )

    def get_collection_stats(self) -> Dict:
        """Getting collection statistics"""
        count = self.collection.count()
        return {
            "total_sequences": count,
            "collection_name": self.collection_name,
            "status": "healthy"
        }

    def delete_sequence(self, sequence_id: str) -> bool:
        """Deleting a sequence by a specified ID"""
        try:
            self.collection.delete(ids=[sequence_id])
            return True
        except Exception as e:
            print(f"Sequence deletion error: {e}")
            return False

    def update_sequence_metadata(self, sequence_id: str, new_metadata: Dict) -> bool:
        """Updating the metadata of a sequence"""
        try:
            self.collection.update(
                ids=[sequence_id],
                metadatas=[new_metadata]
            )
            return True
        except Exception as e:
            print(f"Metadata update error: {e}")
            return False


# Singleton instance - lazy initialization
_vectordb_instance = None

def get_vectordb_instance():
    global _vectordb_instance
    if _vectordb_instance is None:
        try:
            import os
            # Skip heavy initialization for faster startup
            os.environ['SKIP_SAMPLE_DATA'] = 'true'
            _vectordb_instance = RNAVectorDB()
        except Exception as e:
            print(f"Error initializing VectorDB: {e}")
            # Return a mock instance to prevent crashes
            class MockVectorDB:
                def get_collection_stats(self):
                    return {"status": "initializing", "total_sequences": 0, "collection_name": "rna_sequences"}
                def search_similar(self, *args, **kwargs):
                    from ..models.rna_models import VectorSearchResponse
                    return VectorSearchResponse(query_sequence="", results=[], total_found=0)
                def add_sequence(self, *args, **kwargs):
                    return "mock_id"
            _vectordb_instance = MockVectorDB()
    return _vectordb_instance
