from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def safe_mkdir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, sort_keys=False)

def walk_files(root: Path) -> Iterable[Tuple[Path, int]]:
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            p = Path(dirpath) / name
            try:
                yield p, p.stat().st_size
            except FileNotFoundError:
                continue

def relpath(p: Path, root: Path) -> str:
    return str(p.relative_to(root)).replace("\\", "/")
  
