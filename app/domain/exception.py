class VectorStoreError(Exception):
    """Root exception for all vector store operations"""
    pass

class DimensionMismatchErrors(VectorStoreError):
    """Raised when the vector shape violates the collection's schema."""
    pass

class PortUnavailibleError(VectorStoreError):
    """Raised when the infrastructure is completely unreachable after retries."""
    pass

class PointNotFoundError(VectorStoreError):
    """Raised when attempting to operate on a point ID that does not exist."""
    pass