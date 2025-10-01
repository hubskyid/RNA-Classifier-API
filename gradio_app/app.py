import gradio as gr
import asyncio
import sys
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from .api_client import default_client
from utils.config import config
from utils.logger import gradio_logger
from utils.error_handler import ErrorHandler
from .components.input_panel import (
    create_rna_input_panel, 
    create_dot_bracket_input_panel,
    update_sequence_validation,
    update_structure_validation
)
from .components.results_panel import (
    create_classification_results_panel,
    create_validation_results_panel,
    create_similarity_search_results_panel,
    update_classification_results,
    update_validation_results,
    update_similarity_search_results
)


def analyze_rna_sequence(sequence: str, name: str, description: str, 
                        structure: str, top_k: int, threshold: float) -> tuple:
    """Main analysis function that calls all API endpoints"""
    if not sequence or not sequence.strip():
        empty_result = {"success": False, "error": "No sequence provided"}
        return (
            *update_validation_results(empty_result),
            *update_classification_results(empty_result),
            *update_similarity_search_results(empty_result, top_k, threshold)
        )
    
    gradio_logger.info(f"Analyzing RNA sequence: {sequence[:20]}... (length: {len(sequence)})")
    
    # Ensure sequence is properly formatted (uppercase, no spaces)
    clean_sequence = sequence.strip().upper()
    
    # Call validation API
    validation_result = ErrorHandler.safe_api_call(
        default_client.validate_sequence, clean_sequence, name, description
    )
    
    # Call classification API  
    classification_result = ErrorHandler.safe_api_call(
        default_client.classify_sequence, clean_sequence
    )
    
    # Call similarity search API
    gradio_logger.info(f"Calling similarity search with: sequence={clean_sequence[:20]}..., top_k={top_k}, threshold={threshold}")
    similarity_result = ErrorHandler.safe_api_call(
        default_client.search_similar_sequences, clean_sequence, top_k, threshold
    )
    
    return (
        *update_validation_results(validation_result),
        *update_classification_results(classification_result),
        *update_similarity_search_results(similarity_result, top_k, threshold)
    )


def check_api_health() -> str:
    """Check API server health"""
    result = ErrorHandler.safe_api_call(default_client.health_check)
    
    if result.get('success', False):
        data = result.get('data', {})
        status = data.get('status', 'unknown')
        services = data.get('services', {})
        
        classifier_status = services.get('classifier', {}).get('status', 'unknown')
        vectordb_status = services.get('vectordb', {}).get('status', 'unknown')
        
        if status == 'healthy':
            return f"<div style='color: green;'><strong>API Status: Healthy</strong><br>Classifier: {classifier_status}<br>VectorDB: {vectordb_status}</div>"
        else:
            return f"<div style='color: orange;'><strong>API Status: {status}</strong><br>Classifier: {classifier_status}<br>VectorDB: {vectordb_status}</div>"
    else:
        error = result.get('error', 'Unknown error')
        return f"<div style='color: red;'><strong>API Status: Offline</strong><br>Error: {error}</div>"


def handle_put_operation(sequence: str, name: str, description: str) -> str:
    """Handle PUT operation to update entire sequence using sequence as identifier"""
    if not sequence:
        return "Error: RNA sequence is required for PUT operation"
    
    sequence_data = {
        "sequence": sequence,
        "name": name or "",
        "description": description or ""
    }
    
    # Use sequence itself as the identifier
    gradio_logger.info(f"Updating sequence with PUT: {sequence[:20]}...")
    result = ErrorHandler.safe_api_call(
        default_client.update_sequence, sequence, sequence_data
    )
    
    if result.get('success', False):
        return f"Update successful\nSequence: {sequence[:30]}{'...' if len(sequence) > 30 else ''}\nName: {name or 'N/A'}"
    else:
        error_msg = result.get('error', 'Unknown error')
        return f"Update failed: {error_msg}"



def handle_delete_operation(sequence: str) -> str:
    """Handle DELETE operation to remove a sequence"""
    if not sequence:
        return "Error: RNA sequence is required for DELETE operation"
    
    # Use sequence itself as the identifier
    gradio_logger.info(f"Deleting sequence: {sequence[:20]}...")
    result = ErrorHandler.safe_api_call(
        default_client.delete_sequence, sequence
    )
    
    if result.get('success', False):
        data = result.get('data', {})
        status = data.get('status', 'unknown')
        if status == 'deleted':
            return f"Delete successful\nSequence removed from database"
        elif status == 'not_found':
            return "Delete info: Sequence not found in database\nNote: The sequence may not exist or has already been deleted"
        else:
            return f"Delete completed with status: {status}"
    else:
        error_msg = result.get('error', 'Unknown error')
        return f"Delete failed: {error_msg}"


def handle_clear_all_operation() -> str:
    """Handle clearing all sequences from VectorDB"""
    gradio_logger.warning("Clearing all sequences from VectorDB")
    result = ErrorHandler.safe_api_call(default_client.clear_vectordb)
    
    if result.get('success', False):
        data = result.get('data', {})
        previous_count = data.get('previous_count', 0)
        current_count = data.get('current_count', 0)
        return f"Clear all successful\nDeleted {previous_count} sequences\nDatabase is now empty"
    else:
        error_msg = result.get('error', 'Unknown error')
        return f"Clear all failed: {error_msg}"


def create_main_interface():
    """Create the main Gradio interface"""
    # Custom CSS for pink Clear All button
    custom_css = """
    #clear_all_btn {
        background-color: #FF69B4 !important;
        color: white !important;
    }
    #clear_all_btn:hover {
        background-color: #FF1493 !important;
    }
    """
    
    with gr.Blocks(title="RNA Analysis Tool", theme=gr.themes.Soft(), css=custom_css) as app:
        gr.Markdown("""
        # RNA Analysis Tool
        
        Analyze RNA sequences using machine learning classification and similarity search.
        """)
        
        # API Status
        with gr.Row():
            api_status = gr.HTML(
                value=check_api_health(),
                label="API Status"
            )
            refresh_status_btn = gr.Button("Refresh Status", size="sm")
        
        with gr.Tabs():
            # Main Analysis Tab
            with gr.TabItem("RNA Analysis"):
                with gr.Row():
                    # Left Column: Input Panels
                    with gr.Column(scale=1):
                        # RNA Sequence Input
                        rna_panel, sequence_input, sequence_name, sequence_description, validation_status, sequence_stats = create_rna_input_panel()
                        
                        # Dot-Bracket Structure Input
                        structure_panel, structure_input, structure_validation = create_dot_bracket_input_panel()
                        
                        with gr.Row():
                            top_k_input = gr.Slider(
                                minimum=1,
                                maximum=20,
                                value=5,
                                step=1,
                                label="Top K Similar Sequences"
                            )
                            
                            threshold_input = gr.Slider(
                                minimum=0.0,
                                maximum=1.0,
                                value=0.5,
                                step=0.1,
                                label="Similarity Threshold"
                            )
                        
                        analyze_btn = gr.Button(
                            "Analyze RNA Sequence",
                            variant="primary",
                            size="lg"
                        )
                    
                    # Right Column: Results Panels  
                    with gr.Column(scale=2):
                        # Validation Results
                        val_panel, val_status, seq_length, gc_content, base_comp_plot, val_errors = create_validation_results_panel()
                        
                        # Classification Results
                        class_panel, predicted_type, confidence_score, probability_plot, classification_details = create_classification_results_panel()
                        
                        # Similarity Search Results
                        sim_panel, search_params, results_table, similarity_plot = create_similarity_search_results_panel()
            
            # RNA Sequence Tab with Management Features
            with gr.TabItem("RNA Sequence"):
                gr.Markdown("""
                ### RNA Sequence Examples & Management
                
                Select an example sequence to automatically populate the operation fields.
                """)
                
                # Example RNA Sequences Section
                gr.Markdown("#### Example RNA Sequences")
                
                examples = [
                    ["AUGCGAUCGAUC", "Short mRNA", "Example short mRNA sequence", "", 5, 0.5],
                    ["GCGCCGCGCCGCGCCGCGCCGCGCCGCGCCGCGCCGCGCCGCGCCGCGC", "tRNA-like", "High GC content sequence", "((((((((....))))))))", 3, 0.7],
                    ["AUGCAUGCAUGCAUGC", "microRNA", "Short regulatory RNA", "", 10, 0.3],
                    ["AAAAAAAAAUGCGAUCGAUCGAUCGAUC" * 10, "Long sequence", "Long RNA sequence for lncRNA classification", "", 5, 0.5]
                ]
                
                example_table = gr.Dataset(
                    components=[
                        sequence_input, sequence_name, sequence_description, 
                        structure_input, top_k_input, threshold_input
                    ],
                    samples=examples,
                    label="Click to load example and enable operations"
                )
                
                gr.Markdown("---")
                
                # Sequence Management and Results Side by Side
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("#### Sequence Management")
                        gr.Markdown("*Select an example above to enable operations*")
                        
                        # Input fields for sequence data (read-only, populated from examples)
                        crud_sequence_input = gr.Textbox(
                            label="RNA Sequence",
                            placeholder="Select an example sequence above",
                            lines=3,
                            info="Automatically populated from selected example",
                            interactive=False
                        )
                        
                        crud_name_input = gr.Textbox(
                            label="Sequence Name",
                            placeholder="Select an example sequence above",
                            interactive=True
                        )
                        
                        crud_description_input = gr.Textbox(
                            label="Description",
                            placeholder="Select an example sequence above",
                            lines=2,
                            interactive=True
                        )
                        
                        # CRUD operation buttons (initially hidden)
                        with gr.Row():
                            update_btn = gr.Button("Update", variant="primary", visible=False)
                            delete_btn = gr.Button("Delete", variant="stop", visible=False)
                            clear_all_btn = gr.Button("Clear All", variant="secondary", visible=True, elem_id="clear_all_btn")
                    
                    with gr.Column(scale=1):
                        gr.Markdown("#### Result")
                        operation_result = gr.Textbox(
                            label="Operation Status",
                            value="No operation performed yet",
                            lines=4,
                            interactive=False,
                            elem_classes="operation-result"
                        )
        
        # Event Handlers
        
        # Real-time sequence validation
        sequence_input.change(
            fn=update_sequence_validation,
            inputs=[sequence_input],
            outputs=[validation_status, sequence_stats]
        )
        
        # Real-time structure validation
        structure_input.change(
            fn=update_structure_validation,
            inputs=[structure_input],
            outputs=[structure_validation]
        )
        
        # Main analysis button
        analyze_btn.click(
            fn=analyze_rna_sequence,
            inputs=[
                sequence_input, sequence_name, sequence_description,
                structure_input, top_k_input, threshold_input
            ],
            outputs=[
                val_status, seq_length, gc_content, base_comp_plot, val_errors,
                predicted_type, confidence_score, probability_plot, classification_details,
                search_params, results_table, similarity_plot
            ]
        )
        
        # API status refresh
        refresh_status_btn.click(
            fn=check_api_health,
            outputs=[api_status]
        )
        
        # Examples dataset click - populate both analysis and CRUD fields
        def handle_example_selection(example_data):
            """Handle example selection and populate fields"""
            # example_data contains: [sequence, name, description, structure, top_k, threshold]
            sequence = example_data[0]
            name = example_data[1]
            description = example_data[2]
            structure = example_data[3]
            top_k = example_data[4]
            threshold = example_data[5]
            
            # Return values for all outputs
            return (
                # Analysis tab fields
                sequence, name, description, structure, top_k, threshold,
                # CRUD operation fields
                sequence, name, description,
                # Show operation buttons
                gr.update(visible=True),  # update_btn
                gr.update(visible=True),  # delete_btn
            )
        
        example_table.click(
            fn=handle_example_selection,
            inputs=[example_table],
            outputs=[
                # Analysis tab fields
                sequence_input, sequence_name, sequence_description,
                structure_input, top_k_input, threshold_input,
                # CRUD operation fields
                crud_sequence_input, crud_name_input, crud_description_input,
                # Operation buttons visibility
                update_btn, delete_btn
            ]
        )
        
        # CRUD Operations Event Handlers
        update_btn.click(
            fn=handle_put_operation,
            inputs=[crud_sequence_input, crud_name_input, crud_description_input],
            outputs=[operation_result]
        )
        
        delete_btn.click(
            fn=handle_delete_operation,
            inputs=[crud_sequence_input],
            outputs=[operation_result]
        )
        
        clear_all_btn.click(
            fn=handle_clear_all_operation,
            outputs=[operation_result]
        )
    
    return app


def launch_app(server_name: Optional[str] = None, server_port: Optional[int] = None, 
               share: Optional[bool] = None, debug: Optional[bool] = None):
    """Launch the Gradio application"""
    import socket
    
    # Use config values if not provided
    server_name = server_name or config.GRADIO_HOST
    server_port = server_port or config.GRADIO_PORT
    share = share if share is not None else config.GRADIO_SHARE
    debug = debug if debug is not None else config.GRADIO_DEBUG
    
    # Try to find an available port if the default one is in use
    original_port = server_port
    max_retries = 10
    for i in range(max_retries):
        try:
            # Test if port is available
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((server_name, server_port))
                s.close()
                break  # Port is available
        except OSError:
            if i < max_retries - 1:
                server_port = original_port + i + 1
                gradio_logger.info(f"Port {original_port + i} is in use, trying port {server_port}")
            else:
                gradio_logger.error(f"Cannot find available port after {max_retries} attempts")
                raise
    
    gradio_logger.info(f"Starting Gradio app on {server_name}:{server_port}")
    gradio_logger.info(f"Share: {share}, Debug: {debug}")
    gradio_logger.info(f"API URL: {config.API_BASE_URL}")
    
    # Check API health but don't fail if it's not available
    try:
        health = default_client.health_check()
        if health.get('success'):
            gradio_logger.info(f"API server is healthy: {health.get('data', {}).get('status', 'unknown')}")
        else:
            gradio_logger.warning(f"API server health check failed: {health.get('error', 'Unknown error')}")
            gradio_logger.warning("Gradio app will start anyway, but API functions may not work")
    except Exception as e:
        gradio_logger.warning(f"Could not check API health: {str(e)}")
        gradio_logger.warning("Gradio app will start anyway, but API functions may not work")
    
    app = create_main_interface()
    
    app.launch(
        server_name=server_name,
        server_port=server_port,
        share=share,
        debug=debug,
        show_error=True,
        max_threads=config.GRADIO_MAX_THREADS
    )


if __name__ == "__main__":
    launch_app()