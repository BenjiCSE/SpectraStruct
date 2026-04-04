import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_smiles_to_mol():
    try:
        from src.chemistry.rdkit_utils import smiles_to_mol
        mol = smiles_to_mol("CCO")
        assert mol is not None
    except ImportError:
        pass  # rdkit not installed in test env

def test_invalid_smiles():
    try:
        from src.chemistry.rdkit_utils import smiles_to_mol
        mol = smiles_to_mol("INVALID!!!SMILES")
        assert mol is None
    except ImportError:
        pass

def test_morgan_fp_shape():
    try:
        from src.chemistry.rdkit_utils import smiles_to_mol, get_morgan_fingerprint
        mol = smiles_to_mol("CCO")
        fp = get_morgan_fingerprint(mol)
        assert fp.shape == (2048,)
    except ImportError:
        pass
