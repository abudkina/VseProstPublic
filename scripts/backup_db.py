#!/usr/bin/env python3
"""Полный дамп MySQL БД. Использует .env (DEV_DB_* или DB_* при FLASK_ENV=production)."""
import os
import sys
import gzip
import shutil
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime

# корень проекта
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKUPS_DIR = PROJECT_ROOT / "backups"


def load_dotenv():
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip()
            if v.startswith('"') and v.endswith('"'):
                v = v[1:-1].replace('\\"', '"')
            elif v.startswith("'") and v.endswith("'"):
                v = v[1:-1].replace("\\'", "'")
            os.environ.setdefault(k, v)


def get_db_config():
    load_dotenv()
    env = os.getenv("FLASK_ENV", "development")
    prefix = "DB_" if env == "production" else "DEV_DB_"
    host = os.getenv(f"{prefix}HOST", "127.0.0.1")
    port = os.getenv(f"{prefix}PORT", "3306")
    user = os.getenv(f"{prefix}USER", "root")
    password = os.getenv(f"{prefix}PASSWORD", "")
    name = os.getenv(f"{prefix}NAME", "vseprost")
    if not password and env != "testing":
        print("ERROR: set {}PASSWORD in .env".format(prefix), file=sys.stderr)
        sys.exit(1)
    return {"host": host, "port": port, "user": user, "password": password, "name": name}


def find_mysqldump():
    exe = shutil.which("mysqldump")
    if exe:
        return exe
    for base in [
        r"C:\Program Files\MySQL\MySQL Server 8.0\bin",
        r"C:\Program Files\MySQL\MySQL Server 5.7\bin",
        "/usr/bin",
        "/usr/local/bin",
    ]:
        p = Path(base) / "mysqldump"
        if p.exists():
            return str(p)
        if (Path(base) / "mysqldump.exe").exists():
            return str(Path(base) / "mysqldump.exe")
    return None


def main():
    do_gzip = "--no-gzip" not in sys.argv
    cfg = get_db_config()
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    base_name = f"vseprost_{cfg['name']}_{ts}.sql"
    out_path = BACKUPS_DIR / base_name

    mysqldump_exe = find_mysqldump()
    if not mysqldump_exe:
        print("ERROR: mysqldump not found. Install MySQL client tools.", file=sys.stderr)
        sys.exit(1)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".cnf", delete=False, encoding="utf-8"
    ) as f:
        f.write(
            "[client]\nuser={user}\npassword={password}\nhost={host}\nport={port}\n".format(
                **cfg
            )
        )
        cnf_path = f.name

    try:
        cmd = [
            mysqldump_exe,
            "--defaults-extra-file=" + cnf_path,
            "--single-transaction",
            "--routines",
            "--triggers",
            "--events",
            "--set-charset",
            "--default-character-set=utf8mb4",
            cfg["name"],
        ]
        with open(out_path, "wb") as fp:
            ret = subprocess.run(cmd, stdout=fp, stderr=subprocess.PIPE, timeout=3600)
        if ret.returncode != 0:
            print(ret.stderr.decode("utf-8", errors="replace"), file=sys.stderr)
            sys.exit(ret.returncode)
    finally:
        try:
            os.unlink(cnf_path)
        except Exception:
            pass

    if do_gzip:
        with open(out_path, "rb") as f_in:
            with gzip.open(str(out_path) + ".gz", "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        out_path.unlink()
        out_path = Path(str(out_path) + ".gz")

    print(out_path.resolve())


if __name__ == "__main__":
    main()
