"""실행 위치와 무관하게 모델 파일을 찾는 경로 도우미."""

from __future__ import annotations

import os
from pathlib import Path


MODEL_NAMES = (
    "nil_pumpkin.pt",
    "pumpkin_best.pt",
    "best.pt",
)


def vision_model_candidates() -> tuple[Path, ...]:
    model_dirs: list[Path] = []

    env_root = os.environ.get("NILARM_REPOSITORY_ROOT")
    if env_root:
        model_dirs.append(
            Path(env_root).expanduser().resolve()
            / "src" / "vision_pkg" / "models"
        )

    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "src" / "vision_pkg" / "models"
        if candidate.is_dir():
            model_dirs.append(candidate)
            break

    cwd_candidate = (
        Path.cwd().resolve() / "src" / "vision_pkg" / "models"
    )
    if cwd_candidate.is_dir():
        model_dirs.append(cwd_candidate)

    try:
        from ament_index_python.packages import (
            get_package_share_directory,
        )
        model_dirs.append(
            Path(get_package_share_directory("vision_pkg")) / "models"
        )
    except Exception:
        pass

    result: list[Path] = []
    seen: set[Path] = set()

    for directory in model_dirs:
        for name in MODEL_NAMES:
            path = directory / name
            if path not in seen:
                seen.add(path)
                result.append(path)

    return tuple(result)
