# Snakefile
"""
Top-level entry point for the MWPC analysis factory.
One ticket = one analysis request.
"""

from pathlib import Path
import yaml

# ------------------------------------------------------------------
# Ticket loading
# ------------------------------------------------------------------
TICKET_ID = config.get("ticket")
if not TICKET_ID:
    raise ValueError(
        "No ticket specified. Run with:\n"
        "  snakemake --config ticket=LAB-REPORT-2026 ..."
    )

TICKET_FILE = Path("tickets") / f"{TICKET_ID}.yaml"
if not TICKET_FILE.exists():
    raise FileNotFoundError(f"Ticket not found: {TICKET_FILE}")

with open(TICKET_FILE) as fh:
    TICKET = yaml.safe_load(fh)

assert TICKET["ticket"]["id"] == TICKET_ID, "Ticket ID mismatch"

DETECTOR_NAME = TICKET.get("detector", "elte_mwpc_2026")

# ------------------------------------------------------------------
# Shared path helpers
# ------------------------------------------------------------------
PROJECT_ROOT = Path.cwd()
DATA_DIR     = PROJECT_ROOT
CACHE_DIR    = PROJECT_ROOT / "cache"
OUTPUT_ROOT  = PROJECT_ROOT / "outputs"
SCRIPTS_DIR  = PROJECT_ROOT / "scripts"

def ebe_file(run: int) -> Path:
    return DATA_DIR / "ebe" / f"ElteLab2026A-Tracker_Run{run}.ebe"

def sett_file(run: int) -> Path:
    return DATA_DIR / "sett" / f"ElteLab2026A-Tracker_Run{run}.sett"

def ticket_output_dir() -> Path:
    return OUTPUT_ROOT / TICKET_ID

def run_output_dir(run: int) -> Path:
    return ticket_output_dir() / f"run{run}"

def efficiency_output_dir() -> Path:
    return ticket_output_dir() / "efficiency"

def comparison_output_dir() -> Path:
    return ticket_output_dir() / "comparison"

def all_requested_runs() -> list[int]:
    runs = set()
    if "runs" in TICKET:
        runs.update(TICKET["runs"])
    if TICKET.get("efficiency_scan", {}).get("enabled"):
        runs.update(TICKET["efficiency_scan"].get("runs", []))
    if TICKET.get("comparison", {}).get("enabled"):
        runs.update(TICKET["comparison"].get("runs", []))
    return sorted(runs)

# ------------------------------------------------------------------
# Includes
# ------------------------------------------------------------------
include: "workflow/rules/preflight.smk"
include: "workflow/rules/inspection.smk"
include: "workflow/rules/efficiency.smk"
include: "workflow/rules/tracking.smk"
include: "workflow/rules/comparison.smk"

# ------------------------------------------------------------------
# Targets – must match exactly the output names defined in the rules
# ------------------------------------------------------------------
def ticket_targets():
    targets = []

    # inspection
    if TICKET.get("per_run", {}).get("inspect", False):
        for r in TICKET.get("runs", []):
            targets.append(str(run_output_dir(r) / "inspect.done"))

    # efficiency
    if TICKET.get("efficiency_scan", {}).get("enabled", False):
        eff = efficiency_output_dir()
        targets.append(str(eff / "efficiency_scan_table.csv"))
        if TICKET["efficiency_scan"].get("figure2", True):
            targets.append(str(eff / "all_efficiencies.png"))
        if TICKET["efficiency_scan"].get("figure3", True):
            targets.append(str(eff / "efficiencies_2x2.png"))

    # tracking
    per = TICKET.get("per_run", {})
    for r in TICKET.get("runs", []):
        out = run_output_dir(r)

        if any(per.get(f, False) for f in ("figure4", "figure5", "figure6", "figure7")):
            targets.append(str(out / f"run{r}_endpoint_tracks.csv"))

        if per.get("figure5", False):
            targets.append(str(out / "theta_x_theta_y_flux.png"))

        if per.get("figure6", False):
            targets.append(str(out / "theta_x_y_slice_flux.png"))

        if per.get("figure7", False):
            targets.append(str(out / "flux.png"))

    # comparison
    if TICKET.get("comparison", {}).get("enabled", False):
        targets.append(str(comparison_output_dir() / "comparison_runs.csv"))

    return targets


rule all:
    input:
        f"outputs/{TICKET_ID}/preflight.done",
        ticket_targets()
    default_target: True