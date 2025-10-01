from pydantic import BaseModel, Field, validator
from typing import List, Optional
from enum import Enum


class RNAType(str, Enum):
    mRNA = "mRNA"
    tRNA = "tRNA"
    rRNA = "rRNA"
    microRNA = "microRNA"
    lncRNA = "lncRNA"


class RNASequence(BaseModel):
    sequence: str = Field(..., min_length=1, max_length=10000, description="RNA sequence (AUGC)")
    name: Optional[str] = Field(None, max_length=100, description="Name of the RNA sequence")
    description: Optional[str] = Field(None, max_length=500, description="Description of the RNA sequence")

    @validator('sequence')
    def validate_rna_sequence(cls, v):
        if not v or not v.strip():
            raise ValueError("Enter a valid RNA sequence")
        
        # Remove any whitespace and convert to uppercase
        sequence_upper = v.strip().upper()
        
        valid_bases = set('AUGC')
        if not all(base in valid_bases for base in sequence_upper):
            invalid_bases = set(sequence_upper) - valid_bases
            raise ValueError(f"The sequence contains invalid bases: {invalid_bases}")
        
        return sequence_upper


class ValidationResponse(BaseModel):
    is_valid: bool
    sequence: str
    length: int
    gc_content: float
    errors: List[str] = []


class ClassificationRequest(BaseModel):
    sequence: str = Field(..., min_length=1, description="RNA sequence for classification")
    
    @validator('sequence')
    def validate_sequence(cls, v):
        if not v or not v.strip():
            raise ValueError("Sequence cannot be empty")
        
        # Remove any whitespace and convert to uppercase
        sequence_upper = v.strip().upper()
        
        valid_bases = set('AUGC')
        if not all(base in valid_bases for base in sequence_upper):
            invalid_bases = set(sequence_upper) - valid_bases
            raise ValueError(f"The sequence contains invalid bases: {invalid_bases}")
        
        return sequence_upper


class ClassificationResult(BaseModel):
    predicted_type: RNAType
    confidence: float = Field(..., ge=0.0, le=1.0)
    probabilities: dict[str, float]


class VectorSearchRequest(BaseModel):
    query_sequence: str = Field(..., min_length=1, description="The RNA search query sequence")
    top_k: int = Field(5, ge=1, le=50, description="Retrieve the top K results")
    similarity_threshold: float = Field(0.5, ge=0.0, le=1.0, description="Similarity for results")

    @validator('query_sequence')
    def validate_query_sequence(cls, v):
        if not v or not v.strip():
            raise ValueError("Query sequence cannot be empty")
        
        # Remove any whitespace and convert to uppercase
        sequence_upper = v.strip().upper()
        
        valid_bases = set('AUGC')
        if not all(base in valid_bases for base in sequence_upper):
            invalid_bases = set(sequence_upper) - valid_bases
            raise ValueError(f"The sequence contains invalid bases: {invalid_bases}")
        
        return sequence_upper


class SimilarSequence(BaseModel):
    sequence: str
    sequence_id: Optional[str] = None
    similarity: float = Field(..., ge=0.0, le=1.0)
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    metadata: Optional[dict] = None


class VectorSearchResponse(BaseModel):
    query_sequence: str
    results: List[SimilarSequence]
    total_found: int