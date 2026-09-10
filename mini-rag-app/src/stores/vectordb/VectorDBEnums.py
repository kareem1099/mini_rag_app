from enum import Enum


class VectorDBEnums(Enum):
    QDRANT = "QDRANT"


class DistanceMethodEnums(Enum):
    COSINE = "cosine"
    DOT = "dot"
