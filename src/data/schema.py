from dataclasses import dataclass, field
from typing import Optional
import numpy as np

@dataclass
class MolecularExample:
    id: str
    smiles: str
    selfies: str
    formula: str
    fingerprint: np.ndarray        # (2048,) Morgan fingerprint, float32
    functional_groups: np.ndarray  # (N_FG,) binary, float32

    nmr_axis: Optional[np.ndarray] = None
    nmr_intensity: Optional[np.ndarray] = None
    ms_axis: Optional[np.ndarray] = None
    ms_intensity: Optional[np.ndarray] = None
    ir_axis: Optional[np.ndarray] = None
    ir_intensity: Optional[np.ndarray] = None

    nmr_binned: Optional[np.ndarray] = None   # (1024,)
    ms_binned: Optional[np.ndarray] = None    # (2048,)
    ir_binned: Optional[np.ndarray] = None    # (2048,)
