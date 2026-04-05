import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import numpy as np
from src.data.binning import bin_spectrum

def test_output_shape():
    axis = np.array([1.0, 2.0, 3.0])
    intensity = np.array([1.0, 2.0, 3.0])
    result = bin_spectrum(axis, intensity, 0.0, 14.0, 1024)
    assert result.shape == (1024,)

def test_output_dtype():
    result = bin_spectrum(np.array([1.0]), np.array([1.0]), 0.0, 14.0, 1024)
    assert result.dtype == np.float32

def test_normalized_range():
    axis = np.linspace(0, 14, 100)
    intensity = np.random.rand(100)
    result = bin_spectrum(axis, intensity, 0.0, 14.0, 1024, normalize=True)
    assert result.max() <= 1.0 + 1e-6
    assert result.min() >= 0.0

def test_empty_input():
    result = bin_spectrum(np.array([]), np.array([]), 0.0, 14.0, 1024)
    assert result.shape == (1024,)
    assert result.sum() == 0.0
