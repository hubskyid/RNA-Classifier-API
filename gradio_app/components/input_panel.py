import gradio as gr
from typing import Tuple, Optional, List
import re


def validate_rna_sequence(sequence: str) -> Tuple[bool, str, List[str]]:
    """Validate RNA sequence input"""
    errors = []
    
    if not sequence:
        return False, "", ["Please enter an RNA sequence to begin validation"]
    
    # Clean sequence
    cleaned_sequence = sequence.strip().upper()
    
    # Check valid RNA bases
    valid_bases = set('AUGC')
    invalid_bases = set(cleaned_sequence) - valid_bases
    
    if invalid_bases:
        errors.append(f"Invalid characters detected: {', '.join(sorted(invalid_bases))}. Only A, U, G, C are allowed in RNA sequences.")
    
    # Check sequence length
    if len(cleaned_sequence) < 1:
        errors.append("The sequence is too short. Please enter at least 1 nucleotide.")
    elif len(cleaned_sequence) > 50000:
        errors.append("The sequence is too long. Maximum length is 50,000 nucleotides.")
    
    # Check for excessive repeats
    max_repeat = check_repetitive_sequence(cleaned_sequence)
    if max_repeat > 50:
        errors.append(f"Too many consecutive identical nucleotides detected ({max_repeat}). This might indicate a data quality issue.")
    
    is_valid = len(errors) == 0
    return is_valid, cleaned_sequence, errors


def validate_dot_bracket(structure: str) -> Tuple[bool, str, List[str]]:
    """Validate dot-bracket structure notation"""
    errors = []
    
    if not structure:
        return True, "", []  
    
    cleaned_structure = structure.strip()
    
    # Check valid dot-bracket characters
    valid_chars = set('().<>[]{}')
    invalid_chars = set(cleaned_structure) - valid_chars
    
    if invalid_chars:
        errors.append(f"Invalid structure notation characters: {', '.join(sorted(invalid_chars))}. Only ( ) < > [ ] {{ }} . are allowed.")
    
    # Check bracket balance
    bracket_pairs = [('(', ')'), ('<', '>'), ('[', ']'), ('{', '}')]
    for open_bracket, close_bracket in bracket_pairs:
        open_count = cleaned_structure.count(open_bracket)
        close_count = cleaned_structure.count(close_bracket)
        if open_count != close_count:
            errors.append(f"Unbalanced structure notation: {open_bracket}{close_bracket} brackets don't match. Each opening bracket must have a corresponding closing bracket.")
    
    is_valid = len(errors) == 0
    return is_valid, cleaned_structure, errors


def check_repetitive_sequence(sequence: str) -> int:
    """Check for repetitive sequences"""
    if len(sequence) == 0:
        return 0
    
    max_repeat = 1
    current_repeat = 1
    
    for i in range(1, len(sequence)):
        if sequence[i] == sequence[i-1]:
            current_repeat += 1
            max_repeat = max(max_repeat, current_repeat)
        else:
            current_repeat = 1
    
    return max_repeat


def calculate_sequence_stats(sequence: str) -> dict:
    """Calculate sequence statistics"""
    if not sequence:
        return {}
    
    length = len(sequence)
    base_counts = {
        'A': sequence.count('A'),
        'U': sequence.count('U'),
        'G': sequence.count('G'),
        'C': sequence.count('C')
    }
    
    gc_content = (base_counts['G'] + base_counts['C']) / length if length > 0 else 0
    au_content = (base_counts['A'] + base_counts['U']) / length if length > 0 else 0
    
    return {
        "length": length,
        "base_counts": base_counts,
        "gc_content": gc_content,
        "au_content": au_content,
        "max_repeat_length": check_repetitive_sequence(sequence)
    }


def create_rna_input_panel() -> gr.Column:
    """Create RNA sequence input panel with real-time validation"""
    with gr.Column() as panel:
        gr.Markdown("RNA Sequence Input")
        
        with gr.Row():
            with gr.Column(scale=2):
                sequence_input = gr.Textbox(
                    label="RNA Sequence (AUGC)",
                    placeholder="Enter RNA sequence here... (e.g., AUGCGAUCGAUC)",
                    lines=3,
                    max_lines=10,
                    elem_id="rna_sequence_input"
                )
                
                sequence_name = gr.Textbox(
                    label="Sequence Name",
                    placeholder="Enter sequence name",
                    max_lines=1
                )
                
                sequence_description = gr.Textbox(
                    label="Description",
                    placeholder="Enter sequence description",
                    lines=2,
                    max_lines=5
                )
            
            with gr.Column(scale=1):
                validation_status = gr.HTML(
                    value="<div style='color: gray;'>Enter RNA sequence for validation</div>",
                    label="Validation Status"
                )
                
                sequence_stats = gr.HTML(
                    value="<div>No sequence entered</div>",
                    label="Sequence Statistics"
                )
        
        return panel, sequence_input, sequence_name, sequence_description, validation_status, sequence_stats


def create_dot_bracket_input_panel() -> gr.Column:
    """Create dot-bracket structure input panel"""
    with gr.Column() as panel:
        gr.Markdown("Dot-Bracket Structure")
        gr.Markdown("Use parentheses `()`, square brackets `[]`, angle brackets `<>`, or curly braces `{}` to represent secondary structure.")
        
        with gr.Row():
            with gr.Column(scale=2):
                structure_input = gr.Textbox(
                    label="Dot-Bracket Structure",
                    placeholder="Enter dot-bracket notation... (e.g., (((...))))",
                    lines=2,
                    max_lines=5,
                    elem_id="dot_bracket_input"
                )
            
            with gr.Column(scale=1):
                structure_validation = gr.HTML(
                    value="<div style='color: gray;'></div>",
                    label="Structure Validation"
                )
                
                # Add Analysis Parameters below the validation message
                gr.Markdown("Analysis Parameters")
                
        return panel, structure_input, structure_validation


def update_sequence_validation(sequence: str) -> Tuple[str, str]:
    """Update sequence validation display"""
    is_valid, cleaned_seq, errors = validate_rna_sequence(sequence)
    
    if not sequence:
        status_html = "<div style='color: gray;'>Enter RNA sequence for validation</div>"
        stats_html = "<div>No sequence entered</div>"
    elif is_valid:
        status_html = "<div style='color: green; font-weight: bold;'> Valid RNA sequence</div>"
        stats = calculate_sequence_stats(cleaned_seq)
        stats_html = f"""
        <div style='font-family: monospace; font-size: 12px;'>
            <strong>Length:</strong> {stats.get('length', 0)} bases<br>
            <strong>GC Content:</strong> {stats.get('gc_content', 0):.1%}<br>
            <strong>Base Counts:</strong> A:{stats.get('base_counts', {}).get('A', 0)} U:{stats.get('base_counts', {}).get('U', 0)} G:{stats.get('base_counts', {}).get('G', 0)} C:{stats.get('base_counts', {}).get('C', 0)}
        </div>
        """
    else:
        error_list = "<br>".join([f"error: {error}" for error in errors])
        status_html = f"<div style='color: red; font-weight: bold;'>Sequence Validation Failed<br>{error_list}</div>"
        stats_html = "<div style='color: red;'>Please correct the sequence to see statistics</div>"
    
    return status_html, stats_html


def update_structure_validation(structure: str) -> str:
    """Update dot-bracket structure validation display"""
    if not structure:
        return "<div style='color: gray;'></div>"
    
    is_valid, cleaned_structure, errors = validate_dot_bracket(structure)
    
    if is_valid:
        return "<div style='color: green; font-weight: bold;'> Valid dot-bracket structure</div>"
    else:
        error_list = "<br>".join([f"error: {error}" for error in errors])
        return f"<div style='color: red; font-weight: bold;'>Structure Validation Failed<br>{error_list}</div>"