"""
LSTM Model for Iceberg Trajectory Prediction
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input, Attention, MultiHeadAttention
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras.losses import MeanSquaredError
import pickle
from typing import List, Tuple, Dict
import warnings
warnings.filterwarnings('ignore')

class IcebergTrajectoryLSTM:
    """
    LSTM model for predicting iceberg trajectories
    """
    
    def __init__(self, 
                 sequence_length: int = 30,
                 prediction_horizon: int = 7,
                 lstm_units: List[int] = [128, 64],
                 dropout_rate: float = 0.2,
                 learning_rate: float = 0.001):
        """
        Initialize the LSTM model
        
        Args:
            sequence_length: Number of past days to use as input
            prediction_horizon: Number of future days to predict
            lstm_units: List of LSTM layer sizes
            dropout_rate: Dropout rate for regularization
            learning_rate: Learning rate for optimizer
        """
        self.sequence_length = sequence_length
        self.prediction_horizon = prediction_horizon
        self.lstm_units = lstm_units
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        
        self.model = None
        self.scalers = {}
        self.feature_columns = []
        self.target_columns = ['lat', 'lon']
        
    def select_features(self, df: pd.DataFrame) -> List[str]:
        """
        Select the most relevant features for the model
        """
        # Core position features
        core_features = ['lat', 'lon']
        
        # Velocity and acceleration features
        motion_features = ['vel_lat', 'vel_lon', 'speed_km_day', 'direction', 
                          'acc_lat', 'acc_lon', 'acc_magnitude']
        
        # Size and physical features
        physical_features = ['area_km2', 'size_ratio', 'area_change_rate']
        
        # Time and seasonal features
        temporal_features = ['day_of_year', 'days_since_start']
        
        # Smoothed features (if available)
        smoothed_features = []
        for window in [3, 7, 15]:
            if f'speed_avg_{window}d' in df.columns:
                smoothed_features.extend([f'speed_avg_{window}d', f'speed_std_{window}d'])
        
        # Spatial features
        spatial_features = ['distance_from_coast', 'net_displacement', 'tortuosity']
        
        # Combine all feature groups
        all_features = (core_features + motion_features + physical_features + 
                       temporal_features + smoothed_features + spatial_features)
        
        # Filter to only existing columns
        available_features = [f for f in all_features if f in df.columns]
        
        print(f"Selected {len(available_features)} features: {available_features}")
        return available_features
    
    def prepare_sequences(self, df: pd.DataFrame, iceberg_id: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sequences for a single iceberg
        
        Returns:
            X: Input sequences (n_sequences, sequence_length, n_features)
            y: Target sequences (n_sequences, prediction_horizon, 2)  # lat, lon
        """
        # Filter data for this iceberg
        iceberg_data = df[df['iceberg_id'] == iceberg_id].copy()
        iceberg_data = iceberg_data.sort_values('datetime').reset_index(drop=True)
        
        if len(iceberg_data) < self.sequence_length + self.prediction_horizon:
            return np.array([]), np.array([])
        
        # Get feature data
        feature_data = iceberg_data[self.feature_columns].values
        target_data = iceberg_data[self.target_columns].values
        
        # Create sequences
        X_sequences = []
        y_sequences = []
        
        for i in range(len(iceberg_data) - self.sequence_length - self.prediction_horizon + 1):
            # Input sequence
            X_seq = feature_data[i:i + self.sequence_length]
            
            # Target sequence (future positions)
            y_seq = target_data[i + self.sequence_length:i + self.sequence_length + self.prediction_horizon]
            
            X_sequences.append(X_seq)
            y_sequences.append(y_seq)
        
        return np.array(X_sequences), np.array(y_sequences)
    
    def prepare_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Prepare training data from processed iceberg dataframe
        """
        print("Preparing training sequences...")
        
        # Select features
        self.feature_columns = self.select_features(df)
        
        # Clean data
        df_clean = df.copy()
        
        # Fill missing values
        for col in self.feature_columns:
            if col in df_clean.columns:
                if df_clean[col].dtype in ['float64', 'int64']:
                    df_clean[col] = df_clean[col].fillna(df_clean[col].median())
                else:
                    df_clean[col] = df_clean[col].fillna(df_clean[col].mode()[0] if len(df_clean[col].mode()) > 0 else 0)
        
        # Replace infinite values
        df_clean = df_clean.replace([np.inf, -np.inf], np.nan)
        df_clean = df_clean.fillna(0)
        
        # Collect sequences from all icebergs
        all_X = []
        all_y = []
        
        iceberg_ids = df_clean['iceberg_id'].unique()
        print(f"Processing {len(iceberg_ids)} icebergs...")
        
        for iceberg_id in iceberg_ids:
            X_berg, y_berg = self.prepare_sequences(df_clean, iceberg_id)
            
            if len(X_berg) > 0:
                all_X.append(X_berg)
                all_y.append(y_berg)
                print(f"  {iceberg_id}: {len(X_berg)} sequences")
        
        if not all_X:
            raise ValueError("No valid sequences found!")
        
        # Combine all sequences
        X = np.concatenate(all_X, axis=0)
        y = np.concatenate(all_y, axis=0)
        
        print(f"Total sequences: {len(X)}")
        print(f"Input shape: {X.shape}")
        print(f"Output shape: {y.shape}")
        
        # Scale features
        self.fit_scalers(X, y)
        X_scaled = self.transform_features(X)
        y_scaled = self.transform_targets(y)
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_scaled, test_size=0.2, random_state=42, shuffle=True
        )
        
        print(f"Training sequences: {len(X_train)}")
        print(f"Testing sequences: {len(X_test)}")
        
        return X_train, X_test, y_train, y_test
    
    def fit_scalers(self, X: np.ndarray, y: np.ndarray):
        """
        Fit scalers for features and targets
        """
        print("Fitting data scalers...")
        
        # Feature scaler (normalize each feature across all sequences and time steps)
        n_samples, n_timesteps, n_features = X.shape
        X_reshaped = X.reshape(-1, n_features)
        
        self.scalers['features'] = StandardScaler()
        self.scalers['features'].fit(X_reshaped)
        
        # Target scaler (lat/lon coordinates)
        n_samples, n_pred_steps, n_targets = y.shape
        y_reshaped = y.reshape(-1, n_targets)
        
        self.scalers['targets'] = StandardScaler()
        self.scalers['targets'].fit(y_reshaped)
        
        print("Scalers fitted successfully")
    
    def transform_features(self, X: np.ndarray) -> np.ndarray:
        """Transform features using fitted scaler"""
        n_samples, n_timesteps, n_features = X.shape
        X_reshaped = X.reshape(-1, n_features)
        X_scaled = self.scalers['features'].transform(X_reshaped)
        return X_scaled.reshape(n_samples, n_timesteps, n_features)
    
    def transform_targets(self, y: np.ndarray) -> np.ndarray:
        """Transform targets using fitted scaler"""
        n_samples, n_pred_steps, n_targets = y.shape
        y_reshaped = y.reshape(-1, n_targets)
        y_scaled = self.scalers['targets'].transform(y_reshaped)
        return y_scaled.reshape(n_samples, n_pred_steps, n_targets)
    
    def inverse_transform_targets(self, y_scaled: np.ndarray) -> np.ndarray:
        """Inverse transform predictions back to original scale"""
        original_shape = y_scaled.shape
        y_reshaped = y_scaled.reshape(-1, 2)
        y_original = self.scalers['targets'].inverse_transform(y_reshaped)
        return y_original.reshape(original_shape)
    
    def build_model(self, input_shape: Tuple[int, int]) -> Model:
        """
        Build LSTM model architecture
        """
        print(f"Building LSTM model with input shape: {input_shape}")
        
        # Input layer
        inputs = Input(shape=input_shape, name='sequence_input')
        
        # LSTM layers
        x = inputs
        for i, units in enumerate(self.lstm_units):
            return_sequences = i < len(self.lstm_units) - 1  # Return sequences for all but last LSTM
            
            x = LSTM(units, 
                    return_sequences=return_sequences,
                    dropout=self.dropout_rate,
                    recurrent_dropout=self.dropout_rate,
                    name=f'lstm_{i+1}')(x)
            
            x = Dropout(self.dropout_rate, name=f'dropout_{i+1}')(x)
        
        # Dense layers for prediction
        x = Dense(64, activation='relu', name='dense_1')(x)
        x = Dropout(self.dropout_rate, name='dropout_final')(x)
        
        # Output layer: predict lat/lon for each future time step
        outputs = Dense(self.prediction_horizon * 2, activation='linear', name='predictions')(x)
        
        # Reshape to (batch_size, prediction_horizon, 2)
        outputs = tf.reshape(outputs, [-1, self.prediction_horizon, 2])
        
        # Create model
        model = Model(inputs=inputs, outputs=outputs, name='iceberg_trajectory_lstm')
        
        # Compile model
        model.compile(
            optimizer=Adam(learning_rate=self.learning_rate),
            loss=MeanSquaredError(),
            metrics=['mae']
        )
        
        print("Model built successfully!")
        print(model.summary())
        
        return model
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray, 
              X_val: np.ndarray, y_val: np.ndarray,
              epochs: int = 100, batch_size: int = 32,
              model_save_path: str = None) -> Dict:
        """
        Train the LSTM model
        """
        print("Starting model training...")
        
        # Build model
        self.model = self.build_model((X_train.shape[1], X_train.shape[2]))
        
        # Callbacks
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=15, restore_best_weights=True),
            ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=10, min_lr=1e-6)
        ]
        
        if model_save_path:
            callbacks.append(
                ModelCheckpoint(model_save_path, monitor='val_loss', save_best_only=True)
            )
        
        # Train model
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        print("Training completed!")
        return history.history
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions with the trained model
        """
        if self.model is None:
            raise ValueError("Model not trained yet!")
        
        # Scale input
        X_scaled = self.transform_features(X)
        
        # Make predictions
        predictions_scaled = self.model.predict(X_scaled)
        
        # Inverse transform to original scale
        predictions = self.inverse_transform_targets(predictions_scaled)
        
        return predictions
    
    def save_model(self, filepath: str):
        """Save model and scalers"""
        # Save Keras model
        self.model.save(f"{filepath}_model.h5")
        
        # Save scalers and metadata
        metadata = {
            'scalers': self.scalers,
            'feature_columns': self.feature_columns,
            'target_columns': self.target_columns,
            'sequence_length': self.sequence_length,
            'prediction_horizon': self.prediction_horizon,
            'lstm_units': self.lstm_units,
            'dropout_rate': self.dropout_rate,
            'learning_rate': self.learning_rate
        }
        
        with open(f"{filepath}_metadata.pkl", 'wb') as f:
            pickle.dump(metadata, f)
        
        print(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load model and scalers"""
        # Load Keras model
        self.model = tf.keras.models.load_model(f"{filepath}_model.h5")
        
        # Load scalers and metadata
        with open(f"{filepath}_metadata.pkl", 'rb') as f:
            metadata = pickle.load(f)
        
        self.scalers = metadata['scalers']
        self.feature_columns = metadata['feature_columns']
        self.target_columns = metadata['target_columns']
        self.sequence_length = metadata['sequence_length']
        self.prediction_horizon = metadata['prediction_horizon']
        self.lstm_units = metadata['lstm_units']
        self.dropout_rate = metadata['dropout_rate']
        self.learning_rate = metadata['learning_rate']
        
        print(f"Model loaded from {filepath}")

def main():
    """
    Test the model building
    """
    print("Testing LSTM model architecture...")
    
    # Create dummy data for testing
    sequence_length = 30
    n_features = 15
    prediction_horizon = 7
    batch_size = 32
    
    # Initialize model
    model = IcebergTrajectoryLSTM(
        sequence_length=sequence_length,
        prediction_horizon=prediction_horizon,
        lstm_units=[128, 64],
        dropout_rate=0.2,
        learning_rate=0.001
    )
    
    # Create dummy input data
    X_dummy = np.random.random((batch_size, sequence_length, n_features))
    y_dummy = np.random.random((batch_size, prediction_horizon, 2))
    
    # Build and compile model
    keras_model = model.build_model((sequence_length, n_features))
    
    # Test prediction
    pred_dummy = keras_model.predict(X_dummy)
    print(f"Input shape: {X_dummy.shape}")
    print(f"Output shape: {pred_dummy.shape}")
    print(f"Target shape: {y_dummy.shape}")
    
    print("Model architecture test completed! ✓")

if __name__ == "__main__":
    main()