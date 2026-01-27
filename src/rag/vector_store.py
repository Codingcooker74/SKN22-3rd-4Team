"""
Vector store for document embeddings and similarity search using Supabase
Uses Supabase REST API with pgvector extension
"""

import logging
import os
from typing import List, Dict, Optional
from openai import OpenAI
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages vector embeddings for financial documents using Supabase pgvector"""

    def __init__(
        self,
        table_name: str = "documents",
        embedding_model: str = "text-embedding-3-small",
        dimension: int = 1536,
    ):
        """
        Initialize vector store with Supabase

        Args:
            table_name: Name of the table in Supabase
            embedding_model: Model for generating embeddings
            dimension: Embedding dimension (1536 for text-embedding-3-small)
        """
        self.table_name = table_name
        self.embedding_model = embedding_model
        self.dimension = dimension

        # Get Supabase credentials
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL과 SUPABASE_KEY 환경 변수가 필요합니다.")

        # Initialize Supabase client
        self.supabase: Client = create_client(supabase_url, supabase_key)

        # Initialize OpenAI client for embeddings
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY 환경 변수가 필요합니다.")

        self.openai_client = OpenAI(api_key=self.openai_api_key)

        logger.info(f"Initialized Supabase vector store with table: {table_name}")

    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        response = self.openai_client.embeddings.create(model=self.embedding_model, input=text)
        return response.data[0].embedding

    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        response = self.openai_client.embeddings.create(model=self.embedding_model, input=texts)
        return [item.embedding for item in response.data]

    def add_documents(self, documents: List[Dict], batch_size: int = 100) -> int:
        """
        Add documents to the vector store

        Args:
            documents: List of document dictionaries with 'id', 'text', and 'metadata'
            batch_size: Number of documents to process at once

        Returns:
            Number of documents added
        """
        total_added = 0

        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]

            texts = [doc.get("text", "") for doc in batch]

            try:
                # Generate embeddings
                embeddings = self._get_embeddings(texts)

                # Prepare records for Supabase
                records = []
                for j, doc in enumerate(batch):
                    record = {
                        "content": doc.get("text", ""),
                        "embedding": embeddings[j],
                        "metadata": doc.get("metadata", {}),
                    }
                    if "id" in doc:
                        record["id"] = doc["id"]
                    records.append(record)

                # Insert to Supabase
                self.supabase.table(self.table_name).insert(records).execute()

                total_added += len(batch)
                logger.info(f"Added batch {i // batch_size + 1}, total: {total_added}")

            except Exception as e:
                logger.error(f"Error adding batch {i // batch_size + 1}: {str(e)}")

        logger.info(f"Total documents added: {total_added}")
        return total_added

    def similarity_search(
        self, query: str, k: int = 5, filter_dict: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for similar documents using pgvector

        Args:
            query: Search query
            k: Number of results to return
            filter_dict: Optional metadata filters

        Returns:
            List of similar documents with scores
        """
        try:
            # Generate query embedding
            query_embedding = self._get_embedding(query)

            # Call the match_documents function in Supabase
            response = self.supabase.rpc(
                "match_documents", {"query_embedding": query_embedding, "match_count": k}
            ).execute()

            # Format results
            documents = []
            for item in response.data:
                documents.append(
                    {
                        "id": item.get("id"),
                        "content": item.get("content"),
                        "metadata": item.get("metadata"),
                        "similarity": item.get("similarity"),
                    }
                )

            return documents

        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            return []

    def search_by_company(self, query: str, company: str, k: int = 5) -> List[Dict]:
        """
        Search for documents related to a specific company

        Args:
            query: Search query
            company: Company ticker or name
            k: Number of results

        Returns:
            List of relevant documents
        """
        # For now, do a general search and filter by company
        results = self.similarity_search(query, k * 2)

        # Filter by company ticker in metadata
        filtered = [doc for doc in results if doc.get("metadata", {}).get("ticker") == company]

        return filtered[:k]

    def get_stats(self) -> Dict:
        """Get statistics about the table"""
        try:
            response = self.supabase.table(self.table_name).select("id", count="exact").execute()
            count = response.count if response.count else 0
        except Exception:
            count = "Unknown"

        return {
            "table_name": self.table_name,
            "total_documents": count,
            "embedding_model": self.embedding_model,
            "dimension": self.dimension,
        }


# RAG Tool function for LangGraph
def rag_search_tool(query: str, ticker: str = None, k: int = 5) -> str:
    """
    Supabase Vector Store에서 질문과 관련된 문서를 검색합니다.
    LangGraph Tool로 사용될 함수입니다.
    """
    try:
        vector_store = VectorStore()

        if ticker:
            results = vector_store.search_by_company(query, ticker, k)
        else:
            results = vector_store.similarity_search(query, k)

        if not results:
            return "관련 문서를 찾을 수 없습니다."

        context = "\n---\n".join(
            [
                f"내용: {doc.get('content', 'N/A')[:500]}...\n메타데이터: {doc.get('metadata', {})}"
                for doc in results
            ]
        )

        return context

    except Exception as e:
        logger.error(f"RAG search error: {str(e)}")
        return f"검색 오류: {str(e)}"


if __name__ == "__main__":
    # 테스트: Vector Store 초기화 및 통계 확인
    try:
        print("🔄 Vector Store 연결 중...")
        store = VectorStore()
        stats = store.get_stats()
        print(f"✅ Vector Store 연결 성공!")
        print(f"   Table: {stats['table_name']}")
        print(f"   Documents: {stats['total_documents']}")
        print(f"   Embedding Model: {stats['embedding_model']}")
    except Exception as e:
        print(f"❌ 오류: {e}")
