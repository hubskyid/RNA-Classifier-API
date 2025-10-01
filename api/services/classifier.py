import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from typing import Dict, Tuple, Optional
import pickle
import os
from ..models.rna_models import RNAType, ClassificationResult


class RNAMLClassifier:
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.scaler = None
        self.label_encoder = {
            'mRNA': 0, 'tRNA': 1, 'rRNA': 2, 'microRNA': 3, 'lncRNA': 4
        }
        self.reverse_label_encoder = {v: k for k, v in self.label_encoder.items()}
        self.model_path = model_path or "models/rna_classifier_model.pkl"
        self.scaler_path = model_path or "models/rna_scaler.pkl"
        
        self._load_or_train_model()
    
    def _extract_features(self, sequence: str) -> np.ndarray:
        """Extract from RNA sequence for ML classification"""
        sequence = sequence.upper()
        length = len(sequence)
        
        if length == 0:
            return np.zeros(20)
        
        # Statistics of nucleotide composition
        a_count = sequence.count('A')
        u_count = sequence.count('U')
        g_count = sequence.count('G')
        c_count = sequence.count('C')
        
        # Statistics of nucleotide frequencies
        a_freq = a_count / length
        u_freq = u_count / length
        g_freq = g_count / length
        c_freq = c_count / length
        
        # GC content and other ratios
        gc_content = (g_count + c_count) / length
        au_ratio = (a_count + u_count) / length
        purine_ratio = (a_count + g_count) / length  # A, G
        pyrimidine_ratio = (u_count + c_count) / length  # U, C
        
        # 2-mer frequencies
        dimers = ['AA', 'AU', 'AG', 'AC', 'UU', 'UG', 'UC', 'GG', 'GC', 'CC']
        dimer_freqs = []
        for dimer in dimers:
            count = 0
            for i in range(len(sequence) - 1):
                if sequence[i:i+2] == dimer:
                    count += 1
            dimer_freqs.append(count / (length - 1) if length > 1 else 0)
        
        # Structure the vector
        features = [
            length,
            a_freq, u_freq, g_freq, c_freq,
            gc_content, au_ratio, purine_ratio, pyrimidine_ratio
        ] + dimer_freqs
        
        return np.array(features)
    
    def _generate_synthetic_data(self, n_samples: int = 1000) -> Tuple[np.ndarray, np.ndarray]:
        """Synthesize RNA sequence data for training"""
        np.random.seed(42)
        X = []
        y = []
        
        for rna_type in self.label_encoder.keys():
            for _ in range(n_samples // len(self.label_encoder)):
                if rna_type == 'mRNA':
                    # long sequences with moderate GC content
                    length = np.random.randint(200, 3000)
                    gc_prob = 0.4 + np.random.normal(0, 0.1)
                elif rna_type == 'tRNA':
                    # tRNA: short sequences with high GC content
                    length = np.random.randint(70, 90)
                    gc_prob = 0.6 + np.random.normal(0, 0.05)
                elif rna_type == 'rRNA':
                    # rRNA: middle-length sequences with high GC content
                    length = np.random.randint(120, 180)
                    gc_prob = 0.55 + np.random.normal(0, 0.05)
                elif rna_type == 'microRNA':
                    # microRNA: short sequences with moderate GC content
                    length = np.random.randint(18, 25)
                    gc_prob = 0.45 + np.random.normal(0, 0.1)
                else:  
                    # lncRNA: long sequences with variable GC content
                    length = np.random.randint(200, 10000)
                    gc_prob = 0.4 + np.random.normal(0, 0.1)
                
                gc_prob = np.clip(gc_prob, 0.2, 0.8)
                
                # Creating random RNA sequence
                sequence = ''.join(np.random.choice(
                    ['A', 'U', 'G', 'C'],
                    size=length,
                    p=[(1-gc_prob)/2, (1-gc_prob)/2, gc_prob/2, gc_prob/2]
                ))
                
                features = self._extract_features(sequence)
                X.append(features)
                y.append(self.label_encoder[rna_type])
        
        return np.array(X), np.array(y)
    
    def _train_model(self) -> None:
        """ML model training"""
        print("Creating synthetic data...")
        X, y = self._generate_synthetic_data()
        
        #Train-test　
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Normalization
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # RandomForestClassifier
        print("Training...")
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluation on test set
        y_pred = self.model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"Model Accuracy: {accuracy:.3f}")
        
        # classification report
        self._save_model()
    
    def _save_model(self) -> None:
        """Save the trained model"""
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
        with open(self.scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        print(f"Save to the model: {self.model_path}")
    
    def _load_model(self) -> bool:
        """Read to the saved model"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                print("Read to the saved model")
                return True
        except Exception as e:
            print(f"Failed to load model: {e}")
        return False
    
    def _load_or_train_model(self) -> None:
        """Read to the saved model or train a new one"""
        if not self._load_model():
            print("No saved model found. A new model will be trained...")
            self._train_model()
    
    def classify(self, sequence: str) -> ClassificationResult:
        """RNA sequence classification using ML model"""
        if self.model is None or self.scaler is None:
            raise RuntimeError("Model is not loaded or trained.")
        
        # Extraction and Normalization
        features = self._extract_features(sequence).reshape(1, -1)
        features_scaled = self.scaler.transform(features)
        
        # Estimation and probability calculation
        prediction = self.model.predict(features_scaled)[0]
        probabilities = self.model.predict_proba(features_scaled)[0]
        
        # Result structuring and return
        predicted_type = RNAType(self.reverse_label_encoder[prediction])
        confidence = probabilities[prediction]
        
        prob_dict = {
            self.reverse_label_encoder[i]: float(prob) 
            for i, prob in enumerate(probabilities)
        }
        
        return ClassificationResult(
            predicted_type=predicted_type,
            confidence=float(confidence),
            probabilities=prob_dict
        )
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Road to the importance of each model"""
        if self.model is None:
            return {}
        
        feature_names = [
            'length', 'A_freq', 'U_freq', 'G_freq', 'C_freq',
            'GC_content', 'AU_ratio', 'purine_ratio', 'pyrimidine_ratio'
        ] + [f'{dimer}_freq' for dimer in ['AA', 'AU', 'AG', 'AC', 'UU', 'UG', 'UC', 'GG', 'GC', 'CC']]
        
        importance = self.model.feature_importances_
        return dict(zip(feature_names, importance))


# Singleton instance - lazy initialization
_ml_classifier_instance = None

def get_ml_classifier_instance():
    global _ml_classifier_instance
    if _ml_classifier_instance is None:
        try:
            _ml_classifier_instance = RNAMLClassifier()
        except Exception as e:
            print(f"Error initializing ML Classifier: {e}")
            raise
    return _ml_classifier_instance