from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List
import pandas as pd # type: ignore

def read_json(p: Path) -> Any:
    with p.open("r", encoding="utf-8") as f: return json.load(f)

def flatten_strings(strings_obj: Dict[str, Dict[str, str]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for bucket, kv in strings_obj.items():
        for k, v in kv.items():
            rows.append({"source": "res/strings.xml", "bucket": bucket, "key": k, "value": v})
    return rows

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--run-id", required=True)
    args = ap.parse_args()
    
    report = read_json(args.out / "report.json")
    manifest = read_json(args.out / "manifest.json")
    strings = read_json(args.out / "resources_strings.json")
    assets = read_json(args.out / "assets_index.json")
    
    dataset: Dict[str, Any] = {
        "run_id": args.run_id, "summary": report, "manifest": manifest,
        "assets_count": len(assets.get("assets", [])),
        "strings_rows": flatten_strings(strings),
    }
    
    with (args.out / "compiled_dataset.json").open("w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
        
    df = pd.DataFrame(dataset["strings_rows"])
    df.to_csv(args.out / "compiled_dataset.csv", index=False)
    print(f"[+] Compiled dataset with {len(df)} string rows")

if __name__ == "__main__":
    main()
  
