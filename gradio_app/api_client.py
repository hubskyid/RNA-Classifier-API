import requests
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import config
from utils.logger import gradio_logger
from utils.error_handler import ErrorHandler


class RNAAnalysisAPIClient:
    """REST API client for RNA Analysis API"""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or config.API_BASE_URL).rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.timeout = config.REQUEST_TIMEOUT
        gradio_logger.info(f"API Client initialized with base URL: {self.base_url}")
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute HTTP request using REST API client"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            gradio_logger.debug(f"Making {method} request to {endpoint}")
            
            if method.upper() == 'GET':
                response = self.session.get(url, timeout=7200)  # 2 hours timeout
            elif method.upper() == 'POST':
                response = self.session.post(
                    url, 
                    data=json.dumps(data) if data else None,
                    timeout=7200  # 2 hours timeout
                )
            elif method.upper() == 'PUT':
                response = self.session.put(
                    url,
                    data=json.dumps(data) if data else None,
                    timeout=7200  # 2 hours timeout
                )
            elif method.upper() == 'DELETE':
                response = self.session.delete(
                    url,
                    data=json.dumps(data) if data else None,
                    timeout=7200  # 2 hours timeout
                )
            elif method.upper() == 'PATCH':
                response = self.session.patch(
                    url,
                    data=json.dumps(data) if data else None,
                    timeout=7200  # 2 hours timeout
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            result = response.json()
            gradio_logger.debug(f"Request successful: {method} {endpoint}")
            return {
                'success': True,
                'data': result,
                'status_code': response.status_code
            }
            
        except requests.exceptions.ConnectionError as e:
            gradio_logger.error(f"Connection error: {str(e)}")
            return ErrorHandler.handle_api_error(e)
        except requests.exceptions.Timeout as e:
            gradio_logger.error(f"Request timeout: {str(e)}")
            return ErrorHandler.handle_api_error(e)
        except requests.exceptions.HTTPError as e:
            try:
                error_detail = e.response.json().get('detail', str(e))
                # Log the full error response for debugging
                gradio_logger.error(f"Full error response: {e.response.text}")
            except:
                error_detail = str(e)
            gradio_logger.warning(f"HTTP Error {e.response.status_code}: {error_detail}")
            gradio_logger.warning(f"Request URL: {url}")
            gradio_logger.warning(f"Request data: {data}")
            return {
                'success': False,
                'error': f'{error_detail}',
                'status_code': e.response.status_code
            }
        except Exception as e:
            gradio_logger.error(f"Unexpected error: {str(e)}")
            return ErrorHandler.handle_api_error(e)
    
    def health_check(self) -> Dict[str, Any]:
        """Health check endpoint via REST API"""
        return self._make_request('GET', '/api/v1/health')
    
    def validate_sequence(self, sequence: str, name: str = "", description: str = "") -> Dict[str, Any]:
        """RNA sequence validation via REST API"""
        data = {
            'sequence': sequence,
            'name': name,
            'description': description
        }
        return self._make_request('POST', '/api/v1/validate', data)
    
    def classify_sequence(self, sequence: str) -> Dict[str, Any]:
        """RNA sequence classification via REST API"""
        data = {'sequence': sequence}
        return self._make_request('POST', '/api/v1/classify', data)
    
    def search_similar_sequences(self, query_sequence: str, top_k: int = 5, 
                                similarity_threshold: float = 0.5) -> Dict[str, Any]:
        """Similar sequence search via REST API"""
        data = {
            'query_sequence': query_sequence,
            'top_k': top_k,
            'similarity_threshold': similarity_threshold
        }
        return self._make_request('POST', '/api/v1/search', data)
    
    def get_feature_importance(self) -> Dict[str, Any]:
        """Get feature importance via REST API"""
        return self._make_request('GET', '/api/v1/classifier/feature-importance')
    
    def add_sequence_to_vectordb(self, sequence: str, name: str = "", 
                                description: str = "") -> Dict[str, Any]:
        """Add sequence to VectorDB via REST API"""
        data = {
            'sequence': sequence,
            'name': name,
            'description': description
        }
        return self._make_request('POST', '/api/v1/vectordb/add', data)
    
    def get_vectordb_stats(self) -> Dict[str, Any]:
        """Get VectorDB statistics via REST API"""
        return self._make_request('GET', '/api/v1/vectordb/stats')
    
    # ============= NEW METHODS FOR PUT, DELETE, PATCH =============
    
    def update_sequence(self, sequence: str, sequence_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an entire RNA sequence (PUT) - uses sequence as identifier"""
        data = {
            'sequence': sequence,
            **sequence_data
        }
        return self._make_request('PUT', '/api/v1/vectordb/update', data)
    
    def delete_sequence(self, sequence: str) -> Dict[str, Any]:
        """Delete an RNA sequence - uses sequence as identifier"""
        data = {'sequence': sequence}
        return self._make_request('DELETE', '/api/v1/vectordb/delete', data)
    
    def patch_sequence_metadata(self, sequence: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Partially update sequence metadata (PATCH) - uses sequence as identifier"""
        data = {
            'sequence': sequence,
            'metadata': metadata
        }
        return self._make_request('PATCH', '/api/v1/vectordb/patch', data)
    
    def clear_vectordb(self) -> Dict[str, Any]:
        """Clear all sequences from VectorDB - Use with caution!"""
        return self._make_request('DELETE', '/api/v1/vectordb/clear', {})


# Default REST API client instance
default_client = RNAAnalysisAPIClient()