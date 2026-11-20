"""Versioned output-only correction; historical ReLU builder is unchanged."""
from tensorflow import keras
from .final_cnn import build_model as build_relu_model
VERSION = 'CAUSAL_CNN_FINAL_SOFTPLUS_V1'
def build_model(mask):
    model = build_relu_model(mask)
    model.get_layer('conv_3').activation = keras.activations.softplus
    return model
