import gradio as gr
import json
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List, Optional
import pandas as pd


def create_classification_results_panel() -> gr.Column:
    """Create classification results display panel"""
    with gr.Column() as panel:
        gr.Markdown("Classification Results")
        
        with gr.Row():
            with gr.Column(scale=1):
                predicted_type = gr.Textbox(
                    label="Predicted RNA Type",
                    interactive=False,
                    elem_id="predicted_type"
                )
                
                confidence_score = gr.Textbox(
                    label="Confidence Score",
                    interactive=False
                )
            
            with gr.Column(scale=2):
                probability_plot = gr.Plot(
                    label="Classification Probabilities",
                    elem_id="probability_plot"
                )
        
        classification_details = gr.Code(
            label="Detailed Classification Results",
            elem_id="classification_details",
            language="json",
            interactive=False,
            lines=10
        )
        
        return panel, predicted_type, confidence_score, probability_plot, classification_details


def create_validation_results_panel() -> gr.Column:
    """Create validation results display panel"""
    with gr.Column() as panel:
        gr.Markdown("Validation Results")
        
        with gr.Row():
            with gr.Column(scale=1):
                validation_status = gr.HTML(
                    label="Validation Status",
                    elem_id="validation_status_result"
                )
                
                sequence_length = gr.Textbox(
                    label="Sequence Length",
                    interactive=False
                )
                
                gc_content = gr.Textbox(
                    label="GC Content (%)",
                    interactive=False
                )
            
            with gr.Column(scale=2):
                base_composition_plot = gr.Plot(
                    label="Base Composition",
                    elem_id="base_composition_plot"
                )
        
        validation_errors = gr.Textbox(
            label="Validation Errors",
            lines=3,
            interactive=False,
            visible=False
        )
        
        return panel, validation_status, sequence_length, gc_content, base_composition_plot, validation_errors


def create_similarity_search_results_panel() -> gr.Column:
    """Create similarity search results display panel"""
    with gr.Column() as panel:
        gr.Markdown("Similarity Search Results")
        
        with gr.Row():
            search_params = gr.HTML(
                label="Search Parameters",
                elem_id="search_params"
            )
        
        with gr.Row():
            results_table = gr.DataFrame(
                label="Similar Sequences",
                headers=["RNA Sequence", "Similarity Score"],
                datatype=["str", "number"],
                elem_id="similarity_results_table",
                value=None  # Don't show empty rows initially
            )
        
        similarity_plot = gr.Plot(
            label="Similarity Scores",
            elem_id="similarity_plot"
        )
        
        return panel, search_params, results_table, similarity_plot


def create_feature_importance_panel() -> gr.Column:
    """Create feature importance display panel"""
    with gr.Column() as panel:
        gr.Markdown("Feature Importance Analysis")
        
        feature_importance_plot = gr.Plot(
            label="Feature Importance",
            elem_id="feature_importance_plot"
        )
        
        model_info = gr.JSON(
            label="Model Information",
            elem_id="model_info"
        )
        
        return panel, feature_importance_plot, model_info


def update_classification_results(result: Dict[str, Any]) -> tuple:
    """Update classification results display"""
    if not result or not result.get('success', False):
        error_msg = result.get('error', 'Classification failed') if result else 'No results'
        return (
            f"Error: {error_msg}",
            0.0,
            create_empty_plot("Classification Error"),
            json.dumps({"error": error_msg}, indent=2)
        )
    
    data = result.get('data', {})
    predicted_type = data.get('predicted_type', 'Unknown')
    confidence = data.get('confidence', 0.0)
    probabilities = data.get('probabilities', {})
    
    # Create probability plot
    if probabilities:
        prob_plot = create_probability_plot(probabilities)
    else:
        prob_plot = create_empty_plot("No probability data")
    
    return (
        predicted_type,
        f"{confidence:.2f}" if confidence else "0.00",  # Format with 2 decimal places
        prob_plot,
        json.dumps(data, indent=2) if data else "{}"
    )


def update_validation_results(result: Dict[str, Any]) -> tuple:
    """Update validation results display"""
    if not result or not result.get('success', False):
        error_msg = result.get('error', 'Validation failed') if result else 'No results'
        return (
            f"<div style='color: red;'><strong>Error:</strong> {error_msg}</div>",
            "0",  # Return string for Textbox
            "0.00",  # Return string for Textbox
            create_empty_plot("Validation Error"),
            error_msg
        )
    
    data = result.get('data', {})
    is_valid = data.get('is_valid', False)
    sequence = data.get('sequence', '')
    length = data.get('length', 0)
    gc_content = data.get('gc_content', 0.0) * 100  # Convert to percentage
    errors = data.get('errors', [])
    
    # Create status HTML
    if is_valid:
        status_html = ""  # Empty string for valid sequences
    else:
        status_html = "<div style='color: red;'><strong>Invalid RNA Sequence</strong></div>"
    
    # Create base composition plot
    if sequence and is_valid:
        base_plot = create_base_composition_plot(sequence)
    else:
        base_plot = create_empty_plot("No valid sequence")
    
    # Format errors
    error_text = "\n".join(errors) if errors else ""
    
    return (
        status_html,
        str(length),  # Convert to string for Textbox
        f"{int(gc_content)}" if gc_content else "0",  # Format as integer
        base_plot,
        error_text
    )


def update_similarity_search_results(result: Dict[str, Any], top_k: int, threshold: float) -> tuple:
    """Update similarity search results display"""
    if not result or not result.get('success', False):
        error_msg = result.get('error', 'Search failed') if result else 'No results'
        return (
            f"<div style='color: red;'>Search failed: {error_msg}</div>",
            None,  # Return None instead of empty DataFrame
            create_empty_plot("Search Error")
        )
    
    data = result.get('data', {})
    query_sequence = data.get('query_sequence', '')
    results = data.get('results', [])
    total_found = data.get('total_found', 0)
    
    # Create search parameters display
    if total_found == 0:
        params_html = f"""
        <div style='font-family: monospace; font-size: 12px;'>
            <strong>Query:</strong> {query_sequence[:50]}{'...' if len(query_sequence) > 50 else ''}<br>
            <strong>Top K:</strong> {top_k} | <strong>Threshold:</strong> {threshold:.2f}<br>
            <strong style='color: orange;'>No similar sequences found with the given threshold</strong>
        </div>
        """
    else:
        params_html = f"""
        <div style='font-family: monospace; font-size: 12px;'>
            <strong>Query:</strong> {query_sequence[:50]}{'...' if len(query_sequence) > 50 else ''}<br>
            <strong>Top K:</strong> {top_k} | <strong>Threshold:</strong> {threshold:.2f}<br>
            <strong>Results Found:</strong> {total_found}
        </div>
        """
    
    # Create results DataFrame
    if results:
        df_data = []
        for result in results:
            # Handle both 'similarity_score' and 'similarity' field names
            similarity = result.get('similarity_score', result.get('similarity', 0))
            df_data.append({
                "RNA Sequence": result.get('sequence', '')[:100] + ('...' if len(result.get('sequence', '')) > 100 else ''),
                "Similarity Score": round(similarity, 4)
            })
        df = pd.DataFrame(df_data)
    else:
        # Return None for empty results instead of empty DataFrame
        df = None
    
    # Create similarity plot
    if results:
        similarity_plot = create_similarity_plot(results)
    else:
        similarity_plot = create_empty_plot("No similar sequences found")
    
    return params_html, df, similarity_plot


def update_feature_importance_results(result: Dict[str, Any]) -> tuple:
    """Update feature importance results display"""
    if not result or not result.get('success', False):
        error_msg = result.get('error', 'Feature importance failed') if result else 'No results'
        return (
            create_empty_plot("Feature Importance Error"),
            {"error": error_msg}
        )
    
    data = result.get('data', {})
    feature_importance = data.get('feature_importance', {})
    model_type = data.get('model_type', 'Unknown')
    
    # Create feature importance plot
    if feature_importance:
        importance_plot = create_feature_importance_plot(feature_importance)
    else:
        importance_plot = create_empty_plot("No feature importance data")
    
    model_info = {
        "model_type": model_type,
        "total_features": len(feature_importance),
        "top_features": dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10])
    }
    
    return importance_plot, model_info


def create_probability_plot(probabilities: Dict[str, float]) -> go.Figure:
    """Create probability bar plot"""
    rna_types = list(probabilities.keys())
    probs = list(probabilities.values())
    
    fig = go.Figure(data=[
        go.Bar(x=rna_types, y=probs, marker_color='skyblue')
    ])
    
    fig.update_layout(
        title="",
        xaxis_title="RNA Type",
        yaxis_title="Probability",
        yaxis=dict(range=[0, 1]),
        height=300
    )
    
    return fig


def create_base_composition_plot(sequence: str) -> go.Figure:
    """Create base composition pie chart"""
    base_counts = {
        'A': sequence.count('A'),
        'U': sequence.count('U'),
        'G': sequence.count('G'),
        'C': sequence.count('C')
    }
    
    bases = list(base_counts.keys())
    counts = list(base_counts.values())
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
    
    fig = go.Figure(data=[
        go.Pie(labels=bases, values=counts, marker_colors=colors)
    ])
    
    fig.update_layout(
        title="",
        height=300
    )
    
    return fig


def create_similarity_plot(results: List[Dict]) -> go.Figure:
    """Create similarity scores plot"""
    sequences = [f"Seq {i+1}" for i in range(len(results))]
    # Handle both 'similarity_score' and 'similarity' field names
    scores = [result.get('similarity_score', result.get('similarity', 0)) for result in results]
    
    fig = go.Figure(data=[
        go.Bar(x=sequences, y=scores, marker_color='lightgreen')
    ])
    
    fig.update_layout(
        title="Similarity Scores",
        xaxis_title="Similar Sequences",
        yaxis_title="Similarity Score",
        yaxis=dict(range=[0, 1]),
        height=300
    )
    
    return fig


def create_feature_importance_plot(importance: Dict[str, float]) -> go.Figure:
    """Create feature importance plot"""
    # Sort by importance
    sorted_items = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:15]
    features = [item[0] for item in sorted_items]
    importances = [item[1] for item in sorted_items]
    
    fig = go.Figure(data=[
        go.Bar(x=importances, y=features, orientation='h', marker_color='coral')
    ])
    
    fig.update_layout(
        title="Top 15 Feature Importances",
        xaxis_title="Importance Score",
        yaxis_title="Features",
        height=500
    )
    
    return fig


def create_empty_plot(message: str) -> go.Figure:
    """Create empty plot with message"""
    fig = go.Figure()
    
    fig.add_annotation(
        x=0.5,
        y=0.5,
        text=message,
        showarrow=False,
        font=dict(size=16, color="gray")
    )
    
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=300
    )
    
    return fig