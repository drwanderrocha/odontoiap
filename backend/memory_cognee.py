"""
Cognee Memory Integration for OdontoAI
Provides persistent long-term memory for the clinical AI copilot.
"""

import os
import asyncio
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

import cognee
from cognee import remember, recall, forget, serve
from pydantic import BaseModel, Field


class MemoryConfig(BaseModel):
    """Configuration for Cognee memory layer."""
    llm_api_key: str = Field(default_factory=lambda: os.getenv("LLM_API_KEY", ""))
    cognee_base_url: Optional[str] = Field(default_factory=lambda: os.getenv("COGNEE_BASE_URL"))
    cognee_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("COGNEE_API_KEY"))
    postgres_dsn: Optional[str] = Field(default_factory=lambda: os.getenv("DATABASE_URL"))
    dataset: str = "odontoai_clinical"


class ClinicalMemory:
    """
    High-level interface for OdontoAI's clinical memory.
    
    Uses Cognee to store and retrieve:
    - Biomechanical rules & attachment designs (from teach workspace)
    - Anonymized clinical cases & outcomes
    - Literature summaries (RAG-ready)
    - User preferences & teaching notes
    """
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or MemoryConfig()
        self._initialized = False
        self._serve_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> None:
        """Initialize Cognee connection (local or cloud)."""
        if self._initialized:
            return
            
        if self.config.cognee_base_url and self.config.cognee_api_key:
            # Cloud/remote mode
            await serve(
                url=self.config.cognee_base_url,
                api_key=self.config.cognee_api_key
            )
        else:
            # Local mode - uses SQLite/LanceDB/KuzuDB embedded
            # If postgres_dsn provided, Cognee will use Postgres backend
            if self.config.postgres_dsn:
                os.environ["DB_PROVIDER"] = "postgres"
                os.environ["VECTOR_DB_PROVIDER"] = "pgvector"
                os.environ["GRAPH_DATABASE_PROVIDER"] = "postgres"
                os.environ["CACHE_BACKEND"] = "postgres"
                
        os.environ["LLM_API_KEY"] = self.config.llm_api_key
        self._initialized = True
    
    async def close(self) -> None:
        """Disconnect from Cognee."""
        await cognee.disconnect()
        self._initialized = False
    
    # ============ Clinical Knowledge ============
    
    async def store_biomechanical_rule(
        self,
        movement_type: str,
        tooth_type: str,
        mf_ratio_mm: float,
        attachment_design: Dict[str, Any],
        overcorrection_factor: float,
        source: str,
        confidence: float = 0.9
    ) -> str:
        """Store a biomechanical rule for a specific movement."""
        content = f"""
Biomechanical Rule: {movement_type} for {tooth_type}
- Target M/F ratio: {mf_ratio_mm} mm
- Attachment design: {attachment_design}
- Overcorrection factor: {overcorrection_factor}x
- Source: {source}
- Confidence: {confidence}
""".strip()
        
        from cognee.tasks.ingestion.data_item import DataItem
        data_item = DataItem(
            data=content,
            label=f"biomechanical_rule_{movement_type}_{tooth_type}",
            external_metadata={
                "type": "biomechanical_rule",
                "movement": movement_type,
                "tooth": tooth_type,
                "source": source,
                "confidence": confidence
            }
        )
        
        await remember(
            data_item,
            dataset_name=self.config.dataset,
        )
        return f"rule_{movement_type}_{tooth_type}"
    
    async def get_biomechanical_rules(
        self,
        movement_type: Optional[str] = None,
        tooth_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve biomechanical rules, optionally filtered."""
        query = "biomechanical rules for aligner therapy"
        if movement_type:
            query += f" {movement_type}"
        if tooth_type:
            query += f" {tooth_type}"
            
        results = await recall(query, datasets=[self.config.dataset])
        return [
            {
                "content": r.get("content", ""),
                "metadata": r.get("metadata", {}),
                "score": r.get("score", 0)
            }
            for r in results
            if r.get("metadata", {}).get("type") == "biomechanical_rule"
        ]
    
    async def store_clinical_case(
        self,
        case_id: str,
        diagnosis: str,
        treatment_plan: Dict[str, Any],
        biomechanics_notes: str,
        outcome: Optional[str] = None,
        anonymized: bool = True
    ) -> str:
        """Store an anonymized clinical case for learning."""
        content = f"""
Clinical Case: {case_id}
Diagnosis: {diagnosis}
Treatment Plan: {treatment_plan}
Biomechanics Notes: {biomechanics_notes}
Outcome: {outcome or 'In progress'}
Anonymized: {anonymized}
""".strip()
        
        from cognee.tasks.ingestion.data_item import DataItem
        data_item = DataItem(
            data=content,
            label=f"clinical_case_{case_id}",
            external_metadata={
                "type": "clinical_case",
                "case_id": case_id,
                "diagnosis": diagnosis,
                "anonymized": anonymized
            }
        )
        
        await remember(
            data_item,
            dataset_name=self.config.dataset,
        )
        return f"case_{case_id}"
    
    async def find_similar_cases(
        self,
        diagnosis: str,
        movement_types: List[str]
    ) -> List[Dict[str, Any]]:
        """Find similar clinical cases for reference."""
        query = f"clinical case {diagnosis} {' '.join(movement_types)}"
        results = await recall(query, datasets=[self.config.dataset])
        return [
            {
                "content": r.get("content", ""),
                "metadata": r.get("metadata", {}),
                "score": r.get("score", 0)
            }
            for r in results
            if r.get("metadata", {}).get("type") == "clinical_case"
        ]
    
    # ============ Literature & RAG ============
    
    async def store_literature_summary(
        self,
        title: str,
        authors: str,
        year: int,
        doi: str,
        key_findings: List[str],
        clinical_relevance: str,
        tags: List[str]
    ) -> str:
        """Store a literature summary for RAG retrieval."""
        content = f"""
Literature: {title} ({year})
Authors: {authors}
DOI: {doi}
Key Findings: {'; '.join(key_findings)}
Clinical Relevance: {clinical_relevance}
Tags: {', '.join(tags)}
""".strip()
        
        from cognee.tasks.ingestion.data_item import DataItem
        data_item = DataItem(
            data=content,
            label=f"literature_{doi.replace('/', '_')}",
            external_metadata={
                "type": "literature",
                "title": title,
                "year": year,
                "doi": doi,
                "tags": tags
            }
        )
        
        await remember(
            data_item,
            dataset_name=self.config.dataset,
        )
        return f"lit_{doi.replace('/', '_')}"
    
    async def search_literature(
        self,
        query: str,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search stored literature by semantic query."""
        results = await recall(query, datasets=[self.config.dataset])
        filtered = [
            r for r in results
            if r.get("metadata", {}).get("type") == "literature"
        ]
        if tags:
            filtered = [
                r for r in filtered
                if any(t in r.get("metadata", {}).get("tags", []) for t in tags)
            ]
        return filtered
    
    # ============ User Preferences & Teaching ============
    
    async def store_user_preference(
        self,
        user_id: str,
        preference_key: str,
        preference_value: Any,
        context: str = ""
    ) -> str:
        """Store user preference (teaching style, notation, etc.)."""
        content = f"User {user_id} preference: {preference_key} = {preference_value}. Context: {context}"
        
        from cognee.tasks.ingestion.data_item import DataItem
        data_item = DataItem(
            data=content,
            label=f"user_preference_{user_id}_{preference_key}",
            external_metadata={
                "type": "user_preference",
                "user_id": user_id,
                "key": preference_key
            }
        )
        
        await remember(
            data_item,
            dataset_name=self.config.dataset,
        )
        return f"pref_{user_id}_{preference_key}"
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Retrieve all preferences for a user."""
        results = await recall(
            f"user {user_id} preferences",
            dataset=self.config.dataset
        )
        prefs = {}
        for r in results:
            if r.get("metadata", {}).get("type") == "user_preference":
                key = r.get("metadata", {}).get("key")
                if key:
                    prefs[key] = r.get("content", "")
        return prefs
    
    # ============ Session Memory (Fast Cache) ============
    
    async def store_session_context(
        self,
        session_id: str,
        context: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """Store transient session context (syncs to graph in background)."""
        from cognee.tasks.ingestion.data_item import DataItem
        data_item = DataItem(
            data=context,
            label=f"session_context_{session_id}",
            external_metadata=metadata or {"type": "session_context"}
        )
        
        await remember(
            data_item,
            dataset_name=self.config.dataset,
            session_id=session_id,
        )
    
    async def get_session_context(
        self,
        session_id: str,
        query: str
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant session context."""
        results = await recall(query, datasets=[self.config.dataset], session_id=session_id)
        return results
    
    # ============ Maintenance ============
    
    async def forget_dataset(self) -> None:
        """Clear all memory (use with caution)."""
        await forget(dataset_name=self.config.dataset)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        # This would require direct DB access or Cognee admin API
        return {
            "dataset": self.config.dataset,
            "status": "connected" if self._initialized else "disconnected"
        }


# Global instance
_memory: Optional[ClinicalMemory] = None


async def get_memory() -> ClinicalMemory:
    """Get or create global memory instance."""
    global _memory
    if _memory is None:
        _memory = ClinicalMemory()
        await _memory.initialize()
    return _memory


async def close_memory() -> None:
    """Close global memory connection."""
    global _memory
    if _memory:
        await _memory.close()
        _memory = None


@asynccontextmanager
async def memory_session():
    """Context manager for memory lifecycle."""
    mem = await get_memory()
    try:
        yield mem
    finally:
        # Keep connection alive for reuse
        pass