"""Run dbt from the dbt/ folder after loading .env (dbt does not read .env itself)."""
import subprocess
import sys

from dotenv import load_dotenv

load_dotenv()
result = subprocess.run(["dbt", *sys.argv[1:]], cwd="dbt")
sys.exit(result.returncode)