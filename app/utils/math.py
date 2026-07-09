from numpy import sqrt

def cosine_similarity(vector1: list[float], vector2:list[float])-> float:
    """Calculate the cosine similarity between two vectors."""
    if len(vector1) != len(vector2):
        raise ValueError("Vectors must be of the same length")
    
    dot_product = sum(a * b for a, b in zip(vector1, vector2))

    """Calculate the magnitude of each vector."""
    mag1 = sqrt(sum(a * a for a in vector1))
    mag2 = sqrt(sum(b * b for b in vector2))

    if mag1 == 0 or mag2 == 0:
        return 0.0  # Avoid division by zero; if either vector is zero, similarity is 0
    
    return dot_product / (mag1 * mag2)