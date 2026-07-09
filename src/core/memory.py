# src/core/memory.py
# Memory System
# Give agents memory so they can remember past interactions so they need to learn from previous tasks and maintain context.
# Short-term and long-term memory with persistence.
# ============================================

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from src.utils.logger import log


@dataclass
class MemoryEntry:
    """A single memory entry."""

    id: str
    content: str
    type: str  # "conversation", "research", "observation", "fact"
    timestamp: str
    metadata: Dict[str, Any]
    tags: List[str]


class ShortTermMemory:
    """
    Short-term memory for the current task/conversation. It acts like RAM

    Agents need to remember what happened in the current session.
    it stores entries in a list with a maximum size.
    """

    def __init__(self, max_entries: int = 100):
        """
        Initialize short-term memory.

        Args:
            max_entries: Maximum number of entries to keep
        """
        self.max_entries = max_entries
        self._entries: List[MemoryEntry] = []
        log.info(f"ShortTermMemory initialized (max_entries={max_entries})")

    def add(
        self,
        content: str,
        entry_type: str = "general",
        metadata: Dict[str, Any] = None,
        tags: List[str] = None,
    ) -> None:
        """
        Add an entry to short-term memory.

        Args:
            content: The content to store
            entry_type: Type of entry (conversation, research, observation, fact)
            metadata: Additional metadata
            tags: Tags for searching
        """
        entry = MemoryEntry(
            id=f"st_{datetime.now().timestamp()}",
            content=content,
            type=entry_type,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {},
            tags=tags or [],
        )

        self._entries.append(entry)

        # Trim if needed
        if len(self._entries) > self.max_entries:
            self._entries.pop(0)

        log.debug(f"ShortTermMemory: Added entry ({entry_type})")

    def get_recent(self, limit: int = 10) -> List[MemoryEntry]:
        """
        Get the most recent entries.

        Args:
            limit: Number of entries to return

        Returns:
            List of recent entries
        """
        return self._entries[-limit:]

    def search(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        """
        Search for entries containing the query.

        Args:
            query: The search query
            limit: Number of entries to return

        Returns:
            List of matching entries
        """
        results = []
        for entry in reversed(self._entries):
            if query.lower() in entry.content.lower():
                results.append(entry)
                if len(results) >= limit:
                    break
        return results

    def clear(self) -> None:
        """Clear all short-term memory."""
        self._entries = []
        log.info("ShortTermMemory cleared")

    def get_all(self) -> List[MemoryEntry]:
        """Get all entries."""
        return self._entries

    def get_context(self, max_entries: int = 10) -> str:
        """
        Get a formatted context string for the LLM.

        Coz Agents need to see their recent history.
        this formats the recent entries as a string.
        """
        if not self._entries:
            return ""

        recent = self.get_recent(max_entries)
        context_lines = ["Recent history:"]

        for entry in recent:
            context_lines.append(f"- [{entry.type}] {entry.content[:200]}...")

        return "\n".join(context_lines)


class LongTermMemory:
    """
    Long-term memory for persistent storage.

    WHY: Agents need to remember past tasks and learn over time.
    HOW: Stores entries in a JSON file on disk.
    """

    def __init__(self, storage_file: str = "memory.json", max_entries: int = 1000):
        """
        Initialize long-term memory.

        Args:
            storage_file: File to store memory
            max_entries: Maximum entries to keep
        """
        self.storage_file = storage_file
        self.max_entries = max_entries
        self._entries: List[MemoryEntry] = []

        # Load existing memory if it exists
        self._load()

        log.info(f"LongTermMemory initialized (max_entries={max_entries})")

    def _load(self) -> None:
        """Load memory from disk."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r") as f:
                    data = json.load(f)

                for entry_data in data:
                    # Convert back to MemoryEntry
                    entry = MemoryEntry(
                        id=entry_data["id"],
                        content=entry_data["content"],
                        type=entry_data["type"],
                        timestamp=entry_data["timestamp"],
                        metadata=entry_data.get("metadata", {}),
                        tags=entry_data.get("tags", []),
                    )
                    self._entries.append(entry)

                log.info(f"Loaded {len(self._entries)} entries from {self.storage_file}")
            except Exception as e:
                log.error(f"Failed to load memory: {e}")
                self._entries = []

    def _save(self) -> None:
        """Save memory to disk."""
        try:
            data = [asdict(entry) for entry in self._entries]
            with open(self.storage_file, "w") as f:
                json.dump(data, f, indent=2)
            log.debug(f"Saved {len(self._entries)} entries to {self.storage_file}")
        except Exception as e:
            log.error(f"Failed to save memory: {e}")

    def add(
        self,
        content: str,
        entry_type: str = "general",
        metadata: Dict[str, Any] = None,
        tags: List[str] = None,
    ) -> None:
        """
        Add an entry to long-term memory.

        Args:
            content: The content to store
            entry_type: Type of entry
            metadata: Additional metadata
            tags: Tags for searching
        """
        entry = MemoryEntry(
            id=f"lt_{datetime.now().timestamp()}",
            content=content,
            type=entry_type,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {},
            tags=tags or [],
        )

        self._entries.append(entry)

        # Trim if needed
        if len(self._entries) > self.max_entries:
            self._entries.pop(0)

        # Save to disk
        self._save()

        log.debug(f"LongTermMemory: Added entry ({entry_type})")

    def search(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        """
        Search for entries containing the query.

        Args:
            query: The search query
            limit: Number of entries to return

        Returns:
            List of matching entries
        """
        results = []
        for entry in reversed(self._entries):
            if query.lower() in entry.content.lower():
                results.append(entry)
                if len(results) >= limit:
                    break
        return results

    def search_by_type(self, entry_type: str, limit: int = 10) -> List[MemoryEntry]:
        """
        Search for entries of a specific type.

        Args:
            entry_type: The type to search for
            limit: Number of entries to return

        Returns:
            List of matching entries
        """
        results = [e for e in reversed(self._entries) if e.type == entry_type]
        return results[:limit]

    def search_by_tags(self, tags: List[str], limit: int = 10) -> List[MemoryEntry]:
        """
        Search for entries with specific tags.

        Args:
            tags: List of tags to search for
            limit: Number of entries to return

        Returns:
            List of matching entries
        """
        results = []
        for entry in reversed(self._entries):
            if any(tag in entry.tags for tag in tags):
                results.append(entry)
                if len(results) >= limit:
                    break
        return results

    def get_recent(self, limit: int = 10) -> List[MemoryEntry]:
        """Get the most recent entries."""
        return self._entries[-limit:]

    def clear(self) -> None:
        """Clear all long-term memory."""
        self._entries = []
        self._save()
        log.info("LongTermMemory cleared")

    def get_context(self, query: Optional[str] = None, limit: int = 5) -> str:
        """
        Get a formatted context string for the LLM.

        Args:
            query: Optional search query to filter context
            limit: Number of entries to include

        Returns:
            Formatted context string
        """
        if not self._entries:
            return ""

        if query:
            entries = self.search(query, limit)
        else:
            entries = self.get_recent(limit)

        if not entries:
            return ""

        context_lines = ["Past memories:"]

        for entry in entries:
            context_lines.append(f"- [{entry.type}] {entry.content[:200]}...")

        return "\n".join(context_lines)


class MemorySystem:
    """
    Complete memory system combining short-term and long-term memory.

    because agents need both immediate context and long-term storage.
    combines ShortTermMemory and LongTermMemory.
    """

    def __init__(self, short_term_max: int = 100, long_term_file: str = "memory.json"):
        """
        Initialize the memory system.

        Args:
            short_term_max: Max entries in short-term memory
            long_term_file: File for long-term storage
        """
        self.short_term = ShortTermMemory(max_entries=short_term_max)
        self.long_term = LongTermMemory(storage_file=long_term_file)
        self.current_task: Optional[str] = None

        log.info("MemorySystem initialized")

    def start_task(self, task_id: str) -> None:
        """Start a new task, clearing short-term memory."""
        self.current_task = task_id
        self.short_term.clear()
        log.info(f"Started new task: {task_id}")

    def remember(
        self,
        content: str,
        entry_type: str = "general",
        metadata: Dict[str, Any] = None,
        tags: List[str] = None,
    ) -> None:
        """
        Remember something in both short-term and long-term memory.

        Args:
            content: The content to remember
            entry_type: Type of entry
            metadata: Additional metadata
            tags: Tags for searching
        """
        # Add to short-term
        self.short_term.add(content, entry_type, metadata, tags)

        # If it's important (e.g., research, fact), add to long-term
        if entry_type in ["research", "fact", "observation", "conclusion"]:
            self.long_term.add(content, entry_type, metadata, tags)

        log.debug(f"Remembered: {content[:100]}...")

    def recall(self, query: Optional[str] = None, limit: int = 5) -> str:
        """
        Recall relevant memories for the current context.

        Args:
            query: Optional search query
            limit: Number of entries to include

        Returns:
            Formatted context string
        """
        context_parts = []

        # Get short-term context
        short_context = self.short_term.get_context(max_entries=limit)
        if short_context:
            context_parts.append(short_context)

        # Get long-term context
        long_context = self.long_term.get_context(query, limit)
        if long_context:
            context_parts.append(long_context)

        return "\n\n".join(context_parts) if context_parts else ""

    def get_recent(self, limit: int = 10) -> List[MemoryEntry]:
        """Get recent entries from both memories."""
        recent = self.short_term.get_recent(limit)
        # Add long-term if short-term is empty
        if not recent:
            recent = self.long_term.get_recent(limit)
        return recent

    def clear(self) -> None:
        """Clear short-term memory (keep long-term)."""
        self.short_term.clear()
        log.info("Cleared short-term memory (long-term preserved)")


# Creating a global instance
memory = MemorySystem()
