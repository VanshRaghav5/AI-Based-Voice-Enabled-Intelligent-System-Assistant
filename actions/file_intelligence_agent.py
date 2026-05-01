import hashlib
import os
import shutil
import tempfile
from pathlib import Path


def _resolve(raw: str) -> Path:
    if not raw:
        return Path.home()
    aliases = {
        "desktop": Path.home() / "Desktop",
        "downloads": Path.home() / "Downloads",
        "documents": Path.home() / "Documents",
        "home": Path.home(),
        "temp": Path(tempfile.gettempdir()),
    }
    key = raw.strip().lower()
    return aliases.get(key, Path(raw).expanduser())


def _fmt_size(n: int) -> str:
    x = float(n)
    for u in ["B", "KB", "MB", "GB", "TB"]:
        if x < 1024:
            return f"{x:.1f} {u}"
        x /= 1024
    return f"{x:.1f} TB"


def _hash_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def _find_large_files(base: Path, min_size_bytes: int, limit: int = 100) -> str:
    rows = []
    for p in base.rglob("*"):
        if p.is_file():
            try:
                size = p.stat().st_size
                if size >= min_size_bytes:
                    rows.append((size, p))
            except Exception:
                continue
    rows.sort(reverse=True)
    rows = rows[: max(1, min(limit, 500))]
    if not rows:
        return f"No files >= {_fmt_size(min_size_bytes)} found in {base}."
    lines = [f"Found {len(rows)} large file(s) in {base}:"]
    for size, p in rows:
        lines.append(f"  {_fmt_size(size):>10}  {p}")
    return "\n".join(lines)


def _find_duplicates(base: Path, limit_groups: int = 50) -> str:
    by_size: dict[int, list[Path]] = {}
    for p in base.rglob("*"):
        if p.is_file():
            try:
                by_size.setdefault(p.stat().st_size, []).append(p)
            except Exception:
                continue

    dup_groups: list[tuple[str, list[Path], int]] = []
    for size, files in by_size.items():
        if len(files) < 2:
            continue
        by_hash: dict[str, list[Path]] = {}
        for f in files:
            try:
                h = _hash_file(f)
                by_hash.setdefault(h, []).append(f)
            except Exception:
                continue
        for h, same in by_hash.items():
            if len(same) >= 2:
                dup_groups.append((h, same, size))

    if not dup_groups:
        return f"No duplicates found in {base}."

    dup_groups = dup_groups[: max(1, min(limit_groups, 200))]
    lines = [f"Duplicate groups in {base}: {len(dup_groups)}"]
    for _, group, size in dup_groups:
        lines.append(f"\n[{_fmt_size(size)}] x{len(group)}")
        for path in group:
            lines.append(f"  {path}")
    return "\n".join(lines)


def _clean_temp_cache(paths: list[Path]) -> str:
    removed = 0
    freed = 0
    for root in paths:
        if not root.exists() or not root.is_dir():
            continue
        for item in root.rglob("*"):
            try:
                if item.is_file():
                    size = item.stat().st_size
                    item.unlink(missing_ok=True)
                    removed += 1
                    freed += size
            except Exception:
                continue
    return f"Cleanup done. Removed {removed} file(s), freed {_fmt_size(freed)}."


def _disk_trend(base: Path) -> str:
    usage = shutil.disk_usage(base)
    pct = (usage.used / usage.total) * 100 if usage.total else 0.0
    return (
        f"Disk trend snapshot for {base}: "
        f"used={_fmt_size(usage.used)} total={_fmt_size(usage.total)} usage={pct:.1f}%"
    )


def file_intelligence_agent(parameters: dict | None = None, player=None) -> str:
    params = parameters or {}
    action = str(params.get("action", "")).strip().lower()
    base = _resolve(str(params.get("path", "home")))

    if action == "find_large_files":
        min_gb = float(params.get("min_size_gb", 1.0))
        min_bytes = int(min_gb * 1024 * 1024 * 1024)
        return _find_large_files(base, min_bytes, limit=int(params.get("limit", 100)))

    if action == "find_duplicates":
        return _find_duplicates(base, limit_groups=int(params.get("limit_groups", 50)))

    if action == "clean_temp_cache":
        temp_candidates = [
            Path(tempfile.gettempdir()),
            Path.home() / "AppData" / "Local" / "Temp",
        ]
        return _clean_temp_cache(temp_candidates)

    if action == "disk_trend":
        return _disk_trend(base)

    return "Unknown action. Use: find_large_files, find_duplicates, clean_temp_cache, disk_trend."
