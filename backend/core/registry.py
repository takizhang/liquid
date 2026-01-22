"""Plugin registry for collectors and analyzers."""
from typing import Type, Dict, Any


class CollectorRegistry:
    """Registry for data collectors - auto-discovery and management."""

    _collectors: Dict[str, Type] = {}

    @classmethod
    def register(cls, source_name: str):
        """Decorator to register a collector."""
        def decorator(collector_cls: Type):
            cls._collectors[source_name] = collector_cls
            return collector_cls
        return decorator

    @classmethod
    def get(cls, source_name: str):
        """Get collector instance by source name."""
        if source_name not in cls._collectors:
            raise ValueError(f"Unknown source: {source_name}. Available: {list(cls._collectors.keys())}")
        return cls._collectors[source_name]()

    @classmethod
    def list_sources(cls) -> list[str]:
        """List all registered sources."""
        return list(cls._collectors.keys())

    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        """Get all collector instances."""
        return {name: collector_cls() for name, collector_cls in cls._collectors.items()}


class AnalyzerRegistry:
    """Registry for AI analyzers."""

    _analyzers: Dict[str, Type] = {}

    @classmethod
    def register(cls, analyzer_name: str):
        """Decorator to register an analyzer."""
        def decorator(analyzer_cls: Type):
            cls._analyzers[analyzer_name] = analyzer_cls
            return analyzer_cls
        return decorator

    @classmethod
    def get(cls, analyzer_name: str):
        """Get analyzer instance by name."""
        if analyzer_name not in cls._analyzers:
            raise ValueError(f"Unknown analyzer: {analyzer_name}")
        return cls._analyzers[analyzer_name]()

    @classmethod
    def list_analyzers(cls) -> list[str]:
        """List all registered analyzers."""
        return list(cls._analyzers.keys())
