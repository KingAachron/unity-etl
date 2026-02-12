from __future__ import annotations
import argparse
import csv
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List
from androguard.core.apk import APK # type: ignore
from utils import relpath, safe_mkdir, sha256_file, walk_files, write_json

def run_cmd(cmd: List[str], cwd: Path | None = None) -> None:
    proc = subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed ({proc.returncode}): {' '.join(cmd)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")

def unzip_apk(apk_path: Path, dest: Path) -> None:
    safe_mkdir(dest)
    run_cmd(["unzip", "-q", "-o", str(apk_path), "-d", str(dest)])

def apktool_decode(apk_path: Path, dest: Path) -> None:
    safe_mkdir(dest)
    run_cmd(["apktool", "d", "-f", "-q", str(apk_path), "-o", str(dest)])

def extract_manifest_info(apk_path: Path) -> Dict[str, Any]:
    a = APK(str(apk_path))
    info: Dict[str, Any] = {
        "package": a.get_package(),
        "app_name": a.get_app_name(),
        "version_name": a.get_androidversion_name(),
        "version_code": a.get_androidversion_code(),
        "min_sdk": a.get_min_sdk_version(),
        "target_sdk": a.get_target_sdk_version(),
        "permissions": sorted(list(set(a.get_permissions() or []))),
        "activities": sorted(list(set(a.get_activities() or []))),
        "services": sorted(list(set(a.get_services() or []))),
        "receivers": sorted(list(set(a.get_receivers() or []))),
    }
    return info

def extract_resource_strings(decoded_dir: Path) -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    res_dir = decoded_dir / "res"
    if not res_dir.exists(): return out
    import xml.etree.ElementTree as ET
    for values_dir in res_dir.glob("values*"):
        if not values_dir.is_dir(): continue
        strings_xml = values_dir / "strings.xml"
        if not strings_xml.exists(): continue
        try:
            tree = ET.parse(strings_xml)
            root = tree.getroot()
            bucket: Dict[str, str] = {}
            for child in root.findall("string"):
                name = child.attrib.get("name")
                if not name: continue
                text = child.text or ""
                bucket[name] = text.strip()
            out[values_dir.name] = bucket
        except Exception:
            continue
    return out

def index_files(root: Path, out_csv: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for p, size in walk_files(root):
        h = sha256_file(p)
        rows.append({"path": relpath(p, root), "size_bytes": size, "sha256": h})
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["path", "size_bytes", "sha256"])
        w.writeheader()
        for r in rows: w.writerow(r)
    return rows

def detect_unity_signals(unzipped_dir: Path) -> Dict[str, Any]:
    signals: Dict[str, Any] = {}
    candidates = ["lib/arm64-v8a/libil2cpp.so", "lib/armeabi-v7a/libil2cpp.so", "assets/bin/Data/Managed", "assets/bin/Data/global-metadata.dat"]
    found = []
    for c in candidates:
        if (unzipped_dir / c).exists(): found.append(c)
    signals["unity_candidates_found"] = found
    signals["has_assets_dir"] = (unzipped_dir / "assets").exists()
    signals["has_lib_dir"] = (unzipped_dir / "lib").exists()
    return signals

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apk", required=True, type=Path)
    ap.add_argument("--work", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--apk-sha", required=True)
    args = ap.parse_args()
    
    unzipped = args.work / "unzipped"
    decoded = args.work / "apktool_decoded"
    
    unzip_apk(args.apk, unzipped)
    apktool_decode(args.apk, decoded)
    manifest_info = extract_manifest_info(args.apk)
    strings = extract_resource_strings(decoded)
    index_files(unzipped, args.out / "files_index_unzipped.csv")
    index_files(decoded, args.out / "files_index_decoded.csv")
    unity_signals = detect_unity_signals(unzipped)
    
    assets_index: Dict[str, Any] = {"assets": []}
    assets_dir = unzipped / "assets"
    if assets_dir.exists():
        for p, size in walk_files(assets_dir):
            assets_index["assets"].append({"path": relpath(p, unzipped), "size_bytes": size, "sha256": sha256_file(p)})
            
    report: Dict[str, Any] = {
        "run_id": args.run_id, "apk_sha256": args.apk_sha, "apk_file": str(args.apk),
        "manifest": manifest_info, "unity_signals": unity_signals,
        "strings_buckets": {k: len(v) for k, v in strings.items()},
    }
    
    write_json(args.out / "manifest.json", manifest_info)
    write_json(args.out / "resources_strings.json", strings)
    write_json(args.out / "assets_index.json", assets_index)
    write_json(args.out / "report.json", report)

if __name__ == "__main__":
    main()
  
