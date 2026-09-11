# ------------------------------------------------------------------
# Preflight helpers
# ------------------------------------------------------------------
def check_run_files_exist(runs: list[int]) -> None:
    """Raise a clear error if any required .ebe or .sett is missing."""
    missing = []
    for r in runs:
        if not ebe_file(r).exists():
            missing.append(f"ebe/ElteLab2026A-Tracker_Run{r}.ebe")
        if not sett_file(r).exists():
            missing.append(f"sett/ElteLab2026A-Tracker_Run{r}.sett")
    if missing:
        raise FileNotFoundError(
            "The following required data files are missing:\n  - "
            + "\n  - ".join(missing)
        )

def parse_hv_from_sett(run: int) -> int | None:
    """Return the nominal HV stored in the .sett file (or None)."""
    import re
    text = sett_file(run).read_text(encoding="utf-8")
    m = re.search(r"^HV:\s*(\d+)\s*V", text, flags=re.MULTILINE)
    return int(m.group(1)) if m else None