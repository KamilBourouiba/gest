from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class ProfileDefinition:
    name: str
    file_suffix: str
    purpose: str
    typical_time_base: str
    runtime_target: str
    allowed_payloads: tuple[str, ...]
    recommended_capabilities: tuple[str, ...]


PROFILES: Final[dict[str, ProfileDefinition]] = {
    "full": ProfileDefinition(
        name="full",
        file_suffix=".gest.full.json",
        purpose="Authoring, archival interchange, and high-fidelity offline processing.",
        typical_time_base="seconds",
        runtime_target="editor / dataset / offline compiler",
        allowed_payloads=("raw_float32", "packed_float16", "blob_ref"),
        recommended_capabilities=("hierarchy", "hermite_tangents", "blob_external"),
    ),
    "rt": ProfileDefinition(
        name="rt",
        file_suffix=".gest.rt.json",
        purpose="Low-latency streaming or device playback with short chunks.",
        typical_time_base="ticks",
        runtime_target="avatar runtime / embedded player / SGPU queue",
        allowed_payloads=("raw_float32", "packed_float16"),
        recommended_capabilities=("streaming_segments", "inline_pose"),
    ),
    "cmp": ProfileDefinition(
        name="cmp",
        file_suffix=".gest.cmp.json",
        purpose="Compressed storage and transport through blobs, deltas, or dictionaries.",
        typical_time_base="seconds",
        runtime_target="network / archive / batch compiler",
        allowed_payloads=("packed_float16", "raw_uint8", "base64", "blob_ref"),
        recommended_capabilities=("blob_external", "delta_frames", "pose_dictionary"),
    ),
    "neural": ProfileDefinition(
        name="neural",
        file_suffix=".gest.neural.json",
        purpose="Non-semantic latent motion bundles decoded by a known numeric decoder.",
        typical_time_base="seconds",
        runtime_target="neural decoder / learned motion upsampler",
        allowed_payloads=("float16", "float32", "int8", "uint8", "base64", "blob_ref"),
        recommended_capabilities=("latent_channels", "decoder_hint", "numeric_control"),
    ),
}

PROFILE_ALIASES: Final[dict[str, str]] = {
    "neural_bundle": "neural",
}


def normalize_profile(name: str | None) -> str:
    if not name:
        return "full"
    return PROFILE_ALIASES.get(name, name)


def get_profile(name: str | None) -> ProfileDefinition:
    normalized = normalize_profile(name)
    try:
        return PROFILES[normalized]
    except KeyError as e:
        raise ValueError(f"Unknown .gest profile: {name!r}") from e


def profile_names() -> tuple[str, ...]:
    return tuple(PROFILES)

