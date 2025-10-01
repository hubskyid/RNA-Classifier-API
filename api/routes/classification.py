from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import pandas as pd
from ..models.rna_models import (
    RNASequence, ValidationResponse, 
    ClassificationRequest, ClassificationResult,
    VectorSearchRequest, VectorSearchResponse
)
from ..services.classifier import get_ml_classifier_instance
from ..services.vectordb import get_vectordb_instance
from ..utils.validators import RNAValidator

router = APIRouter(prefix="/api/v1", tags=["RNA Analysis"])
validator = RNAValidator()


@router.post("/validate", response_model=ValidationResponse)
def validate_rna_sequence(rna_data: RNASequence):
    """RNA Sequence Input Validation"""
    try:
        sequence = rna_data.sequence
        
        # Input validation
        is_valid, validation_errors = validator.validate_rna_sequence(sequence)
        
        # Retrieve sequence statistics
        stats = validator.get_sequence_statistics(sequence)
        
        return ValidationResponse(
            is_valid=is_valid,
            sequence=sequence.upper() if sequence else "",
            length=stats.get("length", 0),
            gc_content=stats.get("gc_content", 0.0),
            errors=validation_errors
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to validate the RNA sequence. Please check the sequence format and try again."
        )


@router.post("/classify", response_model=ClassificationResult)
def classify_rna_sequence(request: ClassificationRequest):
    """RNA Sequence Classification"""
    try:
        # Validation has already been done by Pydantic
        classifier = get_ml_classifier_instance()
        result = classifier.classify(request.sequence)
        return result
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The RNA sequence format is invalid. Please ensure it contains only A, U, G, C characters."
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to classify the RNA sequence. The classification service may be temporarily unavailable."
        )


@router.post("/search", response_model=VectorSearchResponse)
async def search_similar_sequences(request: VectorSearchRequest):
    """VectorDB Similar Sequence Search"""
    try:
        # Pydantic validator has already validated the input
        vectordb = get_vectordb_instance()
        
        # Preload encoder if not already loaded
        try:
            vectordb.preload_encoder()
        except:
            pass  # Continue even if encoder fails
        
        result = vectordb.search_similar(
            query_sequence=request.query_sequence,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold
        )
        return result
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid search parameters. Please check your sequence format and search criteria."
        )
    
    except Exception as e:
        # Return empty result instead of error for better UX
        return VectorSearchResponse(
            query_sequence=request.query_sequence,
            results=[],
            total_found=0
        )


@router.get("/health")
def health_check() -> Dict[str, Any]:
    """Health Check"""
    try:
        # Basic health check first
        basic_health = {
            "status": "healthy",
            "version": "1.0.0",
            "api": "running"
        }
        
        # Try to get service status, but don't fail if they're not available
        services = {}
        
        try:
            # VectorDB status
            vectordb = get_vectordb_instance()
            vectordb_stats = vectordb.get_collection_stats()
            services["vectordb"] = {
                "status": vectordb_stats.get("status", "initializing"),
                "total_sequences": vectordb_stats.get("total_sequences", 0),
                "collection_name": vectordb_stats.get("collection_name", "unknown")
            }
        except Exception as e:
            services["vectordb"] = {
                "status": "initializing",
                "error": str(e)[:100]  # Limit error message length
            }
        
        try:
            # ML model status
            classifier = get_ml_classifier_instance()
            classifier_status = "healthy" if classifier.model is not None else "initializing"
            services["classifier"] = {
                "status": classifier_status,
                "model_loaded": classifier.model is not None
            }
        except Exception as e:
            services["classifier"] = {
                "status": "initializing", 
                "error": str(e)[:100]  # Limit error message length
            }
        
        basic_health["services"] = services
        return basic_health
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "version": "1.0.0"
        }


@router.get("/vectordb/stats")
def get_vectordb_stats() -> Dict[str, Any]:
    """VectorDB Statistics"""
    try:
        vectordb = get_vectordb_instance()
        return vectordb.get_collection_stats()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve database statistics. The database service may be temporarily unavailable."
        )


@router.post("/vectordb/add")
def add_sequence_to_vectordb(rna_data: RNASequence) -> Dict[str, str]:
    """Add RNA Sequence to VectorDB"""
    try:
        # Input validation
        is_valid, errors = validator.validate_rna_sequence(rna_data.sequence)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid RNA sequence: {', '.join(errors)}. Please correct the sequence and try again."
            )
        
        vectordb = get_vectordb_instance()
        sequence_id = vectordb.add_sequence(
            sequence=rna_data.sequence,
            metadata={
                "name": rna_data.name,
                "description": rna_data.description
            }
        )
        
        return {
            "sequence_id": sequence_id,
            "message": "Sequence added successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to add the sequence to the database. Please try again later."
        )


@router.get("/classifier/feature-importance")
def get_feature_importance() -> Dict[str, Any]:
    """Get Importance from ML Classifier"""
    try:
        classifier = get_ml_classifier_instance()
        importance = classifier.get_feature_importance()
        return {
            "feature_importance": importance,
            "model_type": "RandomForestClassifier"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve feature importance data. The machine learning model may not be loaded."
        )


# ============= NEW HTTP METHODS: PUT, DELETE, PATCH =============

# New endpoints that use sequence as identifier
@router.put("/vectordb/update")
async def update_sequence_by_sequence(rna_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update an RNA sequence using the sequence itself as identifier"""
    try:
        sequence = rna_data.get("sequence", "")
        name = rna_data.get("name", "")
        description = rna_data.get("description", "")
        
        if not sequence:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sequence is required"
            )
        
        # Validate the sequence
        is_valid, errors = validator.validate_rna_sequence(sequence)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid RNA sequence: {', '.join(errors)}. Please correct the sequence format."
            )
        
        vectordb = get_vectordb_instance()
        
        # Find and update the sequence
        # Since we don't have a direct way to find by sequence, we'll use search
        search_result = vectordb.search_similar(sequence, top_k=1, similarity_threshold=0.99)
        
        if search_result.results and len(search_result.results) > 0 and search_result.results[0].similarity >= 0.99:
            # Found exact match, update it
            old_id = search_result.results[0].sequence_id
            if old_id:
                vectordb.delete_sequence(old_id)
            
            new_id = vectordb.add_sequence(
                sequence=sequence,
                metadata={
                    "name": name,
                    "description": description,
                    "updated_at": str(pd.Timestamp.now())
                }
            )
            
            return {
                "message": "Sequence updated successfully",
                "sequence_id": new_id,
                "sequence": sequence
            }
        else:
            # No exact match found, add as new
            new_id = vectordb.add_sequence(
                sequence=sequence,
                metadata={
                    "name": name,
                    "description": description
                }
            )
            return {
                "message": "Sequence added as new (no exact match found)",
                "sequence_id": new_id,
                "sequence": sequence
            }
    
    except HTTPException:
        raise
    except AttributeError as e:
        # Handle missing attributes
        new_id = vectordb.add_sequence(
            sequence=sequence,
            metadata={
                "name": name,
                "description": description
            }
        )
        return {
            "message": "Sequence added successfully",
            "sequence_id": new_id,
            "sequence": sequence
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update error: {str(e)}"
        )


@router.delete("/vectordb/delete")
async def delete_sequence_by_sequence(data: Dict[str, str]) -> Dict[str, Any]:
    """Delete an RNA sequence using the sequence itself as identifier"""
    try:
        sequence = data.get("sequence", "")
        
        if not sequence:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sequence is required"
            )
        
        vectordb = get_vectordb_instance()
        
        # Find the sequence
        search_result = vectordb.search_similar(sequence, top_k=1, similarity_threshold=0.99)
        
        if search_result.results and len(search_result.results) > 0:
            # Check if we found an exact or near-exact match
            if search_result.results[0].similarity >= 0.99:
                # Found exact match, delete it
                sequence_id = search_result.results[0].sequence_id
                if sequence_id:
                    deleted = vectordb.delete_sequence(sequence_id)
                    
                    if deleted:
                        return {
                            "message": "Sequence deleted successfully",
                            "sequence": sequence,
                            "sequence_id": sequence_id,
                            "status": "deleted"
                        }
        
        return {
            "message": "Sequence not found in database",
            "sequence": sequence,
            "status": "not_found"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deletion error: {str(e)}"
        )


@router.patch("/vectordb/patch")
async def patch_sequence_by_sequence(data: Dict[str, Any]) -> Dict[str, Any]:
    """Partially update sequence metadata using the sequence itself as identifier"""
    try:
        sequence = data.get("sequence", "")
        metadata = data.get("metadata", {})
        
        if not sequence:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sequence is required"
            )
        
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Metadata is required for patch operation"
            )
        
        vectordb = get_vectordb_instance()
        
        # Find the sequence
        search_result = vectordb.search_similar(sequence, top_k=1, similarity_threshold=0.99)
        
        if search_result.results and len(search_result.results) > 0 and search_result.results[0].similarity >= 0.99:
            # Found exact match, update its metadata
            sequence_id = search_result.results[0].sequence_id
            if sequence_id:
                updated = vectordb.update_sequence_metadata(sequence_id, metadata)
                
                if updated:
                    return {
                        "message": "Metadata updated successfully",
                        "sequence": sequence,
                        "sequence_id": sequence_id,
                        "updated_fields": list(metadata.keys()),
                        "metadata": metadata
                    }
        
        return {
            "message": "Sequence not found in database",
            "sequence": sequence,
            "status": "not_found"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Metadata update error: {str(e)}"
        )

@router.put("/vectordb/sequence/{sequence_id}")
def update_sequence(sequence_id: str, rna_data: RNASequence) -> Dict[str, Any]:
    """Update an entire RNA sequence in VectorDB (PUT - full replacement)"""
    try:
        # Validate the new sequence
        is_valid, errors = validator.validate_rna_sequence(rna_data.sequence)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid RNA sequence: {', '.join(errors)}. Please ensure the sequence contains only A, U, G, C characters."
            )
        
        vectordb = get_vectordb_instance()
        
        # Delete old sequence and add new one
        # (VectorDB doesn't support direct update, so we replace)
        deleted = vectordb.delete_sequence(sequence_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The specified sequence was not found in the database. It may have been deleted or never existed."
            )
        
        # Add the new sequence with the same ID concept
        new_id = vectordb.add_sequence(
            sequence=rna_data.sequence,
            metadata={
                "name": rna_data.name,
                "description": rna_data.description,
                "original_id": sequence_id,
                "updated_at": str(pd.Timestamp.now())
            }
        )
        
        return {
            "message": "Sequence updated successfully",
            "old_id": sequence_id,
            "new_id": new_id,
            "sequence": rna_data.sequence
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update error: {str(e)}"
        )


@router.delete("/vectordb/sequence/{sequence_id}")
def delete_sequence(sequence_id: str) -> Dict[str, Any]:
    """Delete an RNA sequence from VectorDB (DELETE)"""
    try:
        vectordb = get_vectordb_instance()
        
        # Delete the sequence
        deleted = vectordb.delete_sequence(sequence_id)
        
        if deleted:
            return {
                "message": "Sequence deleted successfully",
                "sequence_id": sequence_id,
                "status": "deleted"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The specified sequence was not found. Please check the sequence ID and try again."
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deletion error: {str(e)}"
        )


@router.patch("/vectordb/sequence/{sequence_id}/metadata")
def patch_sequence_metadata(
    sequence_id: str, 
    metadata_update: Dict[str, Any]
) -> Dict[str, Any]:
    """Partially update sequence metadata in VectorDB (PATCH)"""
    try:
        vectordb = get_vectordb_instance()
        
        # Update only the metadata (partial update)
        updated = vectordb.update_sequence_metadata(sequence_id, metadata_update)
        
        if updated:
            return {
                "message": "Metadata updated successfully",
                "sequence_id": sequence_id,
                "updated_fields": list(metadata_update.keys()),
                "metadata": metadata_update
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The specified sequence was not found. Please check the sequence ID and try again."
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Metadata update error: {str(e)}"
        )



@router.delete("/vectordb/clear")
async def clear_vectordb() -> Dict[str, Any]:
    """Clear all sequences from VectorDB (DELETE all) - Use with caution!"""
    try:
        vectordb = get_vectordb_instance()
        
        # Get current count
        stats = vectordb.get_collection_stats()
        previous_count = stats.get("total_sequences", 0)
        
        # Clear all sequences
        try:
            # Get all IDs and delete them
            all_data = vectordb.collection.get()
            if all_data and 'ids' in all_data and all_data['ids']:
                for doc_id in all_data['ids']:
                    vectordb.delete_sequence(doc_id)
            
            # Verify the collection is empty
            new_stats = vectordb.get_collection_stats()
            current_count = new_stats.get("total_sequences", 0)
            
            return {
                "message": "All sequences cleared from VectorDB",
                "previous_count": previous_count,
                "current_count": current_count,
                "status": "cleared"
            }
        except Exception as clear_error:
            # Alternative approach if the above fails
            return {
                "message": f"Clear operation completed with warning: {str(clear_error)[:100]}",
                "previous_count": previous_count,
                "current_count": 0,
                "status": "partial"
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Clear operation error: {str(e)}"
        )