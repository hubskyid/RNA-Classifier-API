import re
from typing import List, Tuple, Dict
import numpy as np


class RNAValidator:
    """RNA sequence validation class"""

    def __init__(self):
        #　Valid RNA bases
        self.valid_bases = set('AUGC')
        # Minimum/maximum length
        self.min_length = 1
        self.max_length = 50000
        # Abnormal GC content threshold
        self.min_gc_content = 0.0
        self.max_gc_content = 1.0

    def validate_rna_sequence(self, sequence: str) -> Tuple[bool, List[str]]:
        """
        Comprehensive RNA sequence validation

        Args:
            sequence (str): RNA sequence for validation

        Returns:
            Tuple[bool, List[str]]: (Validation results, error message list)
        """
        errors = []

        # None check
        if sequence is None:
            errors.append("The sequence is None")
            return False, errors

        # String type check
        if not isinstance(sequence, str):
            errors.append("The sequence must be a string")
            return False, errors

        # Empty string check
        if not sequence.strip():
            errors.append("An empty sequence is invalid")
            return False, errors

        # Normalize string and re-check
        cleaned_sequence = sequence.strip().upper()

        # Length check
        if len(cleaned_sequence) < self.min_length:
            errors.append(f"The sequence length is too short: {self.min_length}	")

        if len(cleaned_sequence) > self.max_length:
            errors.append(f"The sequence length is too long: {self.max_length}	")

        # Valid base check
        invalid_bases = set(cleaned_sequence) - self.valid_bases
        if invalid_bases:
            errors.append(f"Invalid bases are included: {', '.join(sorted(invalid_bases))}")

        # Checking for consecutive identical bases (detecting abnormal sequences)
        if len(cleaned_sequence) > 0:
            max_repeat_length = self._check_repetitive_sequence(cleaned_sequence)
            if max_repeat_length > 50:

                errors.append(f"An abnormal repetitive sequence was detected{max_repeat_length}")

        # GC content check
        if len(cleaned_sequence) > 0 and not invalid_bases:
            gc_content = self._calculate_gc_content(cleaned_sequence)
            if gc_content < self.min_gc_content or gc_content > self.max_gc_content:
                errors.append(f"The GC content is out of range: {gc_content:.3f} (Valid range: {self.min_gc_content}-{self.max_gc_content})")

        return len(errors) == 0, errors

    def validate_sequence_name(self, name: str) -> Tuple[bool, List[str]]:
        """Validating the sequence name"""
        errors = []

        if name is None:
            return True, []

        if not isinstance(name, str):
            errors.append("The sequence name must be a string")
            return False, errors

        if len(name.strip()) == 0:
            return True, []

        if len(name) > 100:
            errors.append("The sequence name is too long (maximum 100 characters)")

        # Special character check
        if re.search(r'[<>:"/\|?*]', name):
            errors.append("The sequence name contains invalid characters")

        return len(errors) == 0, errors

    def validate_classification_params(self, top_k: int, confidence_threshold: float) -> Tuple[bool, List[str]]:
        """Validating classification parameters"""
        errors = []

        if not isinstance(top_k, int) or top_k <= 0 or top_k > 100:
            errors.append("Please specify top_k as an integer from 1 to 100")

        if not isinstance(confidence_threshold, (int, float)) or confidence_threshold < 0.0 or confidence_threshold > 1.0:
            errors.append("Please specify confidence_threshold as an integer from 0.0 to 1.0")

        return len(errors) == 0, errors

    def _calculate_gc_content(self, sequence: str) -> float:
        """GC content calculation"""
        if len(sequence) == 0:
            return 0.0

        g_count = sequence.count('G')
        c_count = sequence.count('C')
        return (g_count + c_count) / len(sequence)

    def _check_repetitive_sequence(self, sequence: str) -> int:
        """Check for consecutive identical bases"""
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

    def get_sequence_statistics(self, sequence: str) -> Dict:
        """Get statistics of the RNA sequence"""
        if not sequence:
            return {}

        cleaned = sequence.upper()
        length = len(cleaned)

        if length == 0:
            return {}

        base_counts = {
            'A': cleaned.count('A'),
            'U': cleaned.count('U'),
            'G': cleaned.count('G'),
            'C': cleaned.count('C')
        }

        gc_content = (base_counts['G'] + base_counts['C']) / length
        au_content = (base_counts['A'] + base_counts['U']) / length

        return {
            "length": length,
            "base_counts": base_counts,
            "base_frequencies": {
                base: count / length for base, count in base_counts.items()
            },
            "gc_content": gc_content,
            "au_content": au_content,
            "max_repeat_length": self._check_repetitive_sequence(cleaned)
        }

    def suggest_corrections(self, sequence: str) -> List[str]:
        """ Create proposed fixes for the array"""
        suggestions = []

        if not sequence:
            return suggestions

        # Proposed modification of DNA sequences (T-containing)
        if 'T' in sequence.upper():
            suggestions.append("he sequence contains T. Please use U for the RNA sequence")
            corrected = sequence.upper().replace('T', 'U')
            suggestions.append(f"Example: {corrected}")

        # Detecting lowercase characters
        if sequence != sequence.upper():
            suggestions.append("Recommend writing sequences in uppercase")

        # Detecting whitespace
        if re.search(r'\s', sequence):
            suggestions.append("The sequence contains a space. Please remove it")
            corrected = re.sub(r'\s', '', sequence)
            suggestions.append(f"Example: {corrected}")

        return suggestions

    def validate_search_params(self, top_k: int, similarity_threshold: float) -> Tuple[bool, List[str]]:
        """Validation of search parameters"""
        errors = []

        if not isinstance(top_k, int) or top_k <= 0 or top_k > 100:
            errors.append("Please specify top_k as an integer from 1 to 100")

        if not isinstance(similarity_threshold, (int, float)) or similarity_threshold < 0.0 or similarity_threshold > 1.0:
            errors.append("Please specify similarity_threshold as an integer from 0.0 to 1.0")

        return len(errors) == 0, errors

    def validate_metadata(self, metadata: Dict) -> Tuple[bool, List[str]]:
        """Validation of metadata"""
        errors = []

        if metadata is None:
            return True, []

        if not isinstance(metadata, dict):
            errors.append("Metadata must be in a dictionary format")
            return False, errors

        # Key/value type and length check
        for key, value in metadata.items():
            if not isinstance(key, str):
                errors.append(f"Metadata keys must be strings: {key}")

            if len(str(key)) > 100:
                errors.append(f"Metadata keys are too long: {key}")

            if isinstance(value, str) and len(value) > 1000:
                errors.append(f"Metadata values are too long: {key}")

        return len(errors) == 0, errors
