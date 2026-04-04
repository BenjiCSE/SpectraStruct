from typing import Optional
try:
    import selfies as sf
    SELFIES_AVAILABLE = True
except ImportError:
    SELFIES_AVAILABLE = False

def smiles_to_selfies(smiles: str) -> Optional[str]:
    if not SELFIES_AVAILABLE:
        return None
    try:
        return sf.encoder(smiles)
    except Exception:
        return None

def selfies_to_smiles(selfies_str: str) -> Optional[str]:
    if not SELFIES_AVAILABLE:
        return None
    try:
        return sf.decoder(selfies_str)
    except Exception:
        return None

def is_valid_selfies(selfies_str: str) -> bool:
    s = selfies_to_smiles(selfies_str)
    return s is not None and len(s) > 0
