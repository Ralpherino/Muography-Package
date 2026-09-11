# workflow/rules/preflight.smk
"""Lightweight validation before any analysis."""

rule preflight:
    output:
        touch("outputs/{ticket}/preflight.done")
    run:
        from pathlib import Path
        import re
        import yaml

        ticket_id = wildcards.ticket
        project_root = Path.cwd()
        data_dir = project_root

        ticket_file = project_root / "tickets" / f"{ticket_id}.yaml"
        with open(ticket_file) as fh:
            ticket = yaml.safe_load(fh)

        runs = set()
        if "runs" in ticket:
            runs.update(ticket["runs"])
        if ticket.get("efficiency_scan", {}).get("enabled"):
            runs.update(ticket["efficiency_scan"].get("runs", []))
        if ticket.get("comparison", {}).get("enabled"):
            runs.update(ticket["comparison"].get("runs", []))
        runs = sorted(runs)

        print(f"[preflight] Checking {len(runs)} runs: {runs}")

        missing = []
        for r in runs:
            ebe = data_dir / "ebe" / f"ElteLab2026A-Tracker_Run{r}.ebe"
            sett = data_dir / "sett" / f"ElteLab2026A-Tracker_Run{r}.sett"
            if not ebe.exists():
                missing.append(str(ebe))
            if not sett.exists():
                missing.append(str(sett))
        if missing:
            raise FileNotFoundError(
                "Missing data files:\n  - " + "\n  - ".join(missing)
            )

        expected = ticket.get("expected_hv", {})
        for r in runs:
            sett_path = data_dir / "sett" / f"ElteLab2026A-Tracker_Run{r}.sett"
            text = sett_path.read_text(encoding="utf-8")
            m = re.search(r"^HV:\s*(\d+)\s*V", text, flags=re.MULTILINE)
            actual = int(m.group(1)) if m else None

            if r in expected:
                if actual != expected[r]:
                    raise ValueError(
                        f"HV mismatch for run {r}: "
                        f"ticket expects {expected[r]} V, .sett says {actual} V"
                    )
                print(f"[preflight] Run {r}: HV {actual} V (OK)")
            else:
                print(f"[preflight] Run {r}: HV {actual} V")

        print("[preflight] All checks passed.")