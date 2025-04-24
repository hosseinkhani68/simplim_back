from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class VectorStore:
    def __init__(self):
        # Initialize Qdrant client
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            api_key=os.getenv("QDRANT_API_KEY", "")
        )
        
        # Initialize sentence transformer for embeddings
        try:
            self.encoder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', cache_folder='./models')
        except Exception as e:
            print(f"Error loading model: {e}")
            # Fallback to a simpler model
            self.encoder = SentenceTransformer('sentence-transformers/paraphrase-MiniLM-L3-v2', cache_folder='./models')
        
        # Collection name for text simplifications
        self.collection_name = "text_simplifications"
        
        # Create collection if it doesn't exist
        self._create_collection()

    def _create_collection(self):
        try:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=384,  # Dimension of the embeddings
                    distance=models.Distance.COSINE
                )
            )
        except Exception as e:
            # Collection might already exist
            pass

    def store_simplification(self, original_text: str, simplified_text: str, 
                           complexity_level: int, user_id: int) -> int:
        """
        Store a text simplification in the vector database.
        Returns the ID of the stored record.
        """
        # Generate embedding for the original text
        embedding = self.encoder.encode(original_text).tolist()
        
        # Create payload
        payload = {
            "original_text": original_text,
            "simplified_text": simplified_text,
            "complexity_level": complexity_level,
            "user_id": user_id
        }
        
        # Store in Qdrant
        point_id = self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=len(self.client.scroll(self.collection_name)[0]) + 1,
                    vector=embedding,
                    payload=payload
                )
            ]
        )
        
        return point_id[0]

    def find_similar_simplifications(self, text: str, user_id: int, 
                                  limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find similar text simplifications based on the input text.
        """
        # Generate embedding for the input text
        embedding = self.encoder.encode(text).tolist()
        
        # Search in Qdrant
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=embedding,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value=user_id)
                    )
                ]
            ),
            limit=limit
        )
        
        return [
            {
                "original_text": hit.payload["original_text"],
                "simplified_text": hit.payload["simplified_text"],
                "complexity_level": hit.payload["complexity_level"],
                "score": hit.score
            }
            for hit in search_result
        ]

    def get_simplification_history(self, user_id: int, 
                                 limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the user's simplification history.
        """
        scroll_result = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value=user_id)
                    )
                ]
            ),
            limit=limit
        )
        
        return [
            {
                "original_text": record.payload["original_text"],
                "simplified_text": record.payload["simplified_text"],
                "complexity_level": record.payload["complexity_level"]
            }
            for record in scroll_result[0]
        ] 