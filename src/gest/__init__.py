"""gest package: .gest gesture IR in JSON or YAML."""

from gest.document import load_json_bytes, load_json_path, load_path, load_yaml_path
from gest.profiles import get_profile, normalize_profile, profile_names
from gest.sgm import GestCompileError, compile_to_bytes
from gest.sgm_decode import GestDecodeError, decode_sgm_bytes, decoded_to_pose_timeline
from gest.sgm_roundtrip import gest_document_from_sgm_bytes
from gest.validate import is_fully_valid, validate_all, validate_document

__version__ = "0.2.0"

__all__ = [
    "load_json_path",
    "load_json_bytes",
    "load_yaml_path",
    "load_path",
    "compile_to_bytes",
    "GestCompileError",
    "get_profile",
    "normalize_profile",
    "profile_names",
    "decode_sgm_bytes",
    "decoded_to_pose_timeline",
    "GestDecodeError",
    "gest_document_from_sgm_bytes",
    "validate_document",
    "validate_all",
    "is_fully_valid",
    "__version__",
]
