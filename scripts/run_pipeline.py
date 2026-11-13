"""Run the whole pipeline in order: ingest -> enrich -> dbt build -> export.

A failure in a critical step stops the run. Enrichment is not critical: if the tag
service is down, plays still get published (new artists show as 'unknown' until a
later run fills their tags in).
"""
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STEPS = [
    ("ingest new plays", ["scripts/run_incremental.py"], True),
    ("fetch tags for new artists", ["scripts/enrich_artists.py"], False),
    ("dbt build (models and tests)", ["scripts/run_dbt.py", "build"], True),
    ("export dashboard data", ["scripts/export_dashboard_data.py"], True),
]


def main():
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    started = time.time()
    warnings = []
    for name, cmd, critical in STEPS:
        print(f"\n=== {name} ===", flush=True)
        t0 = time.time()
        result = subprocess.run([sys.executable, *cmd], cwd=ROOT, env=env)
        elapsed = time.time() - t0
        if result.returncode != 0:
            if critical:
                print(f"\nFAILED at step '{name}' after {elapsed:.0f}s (exit code {result.returncode}).")
                sys.exit(result.returncode)
            warnings.append(name)
            print(f"=== WARNING: '{name}' failed (not critical), continuing ===", flush=True)
            continue
        print(f"=== done in {elapsed:.0f}s ===", flush=True)

    print(f"\nPipeline finished in {time.time() - started:.0f}s.")
    if warnings:
        print("Warnings: " + ", ".join(warnings))


if __name__ == "__main__":
    main()