# MuographyPackage v1.1.1

A reproducible, ticket-driven analysis factory for multi-wire proportional chamber (MWPC) cosmic-ray muon data.

One YAML ticket describes an entire analysis request.  
Snakemake builds the dependency graph, runs only what is needed, and isolates every result under `outputs/<TICKET_ID>/`.

The physics calculations remain in ordinary Python scripts.  
The workflow only orchestrates them.

---

## 1. Design Principles

| Layer | Responsibility | Where it lives |
|---|---|---|
| Detector configuration | Geometry, pitch, chamber order, DAQ mapping | `detectors/*.yaml` |
| Run metadata | HV, gas, notes, timestamps, event counts | `.sett` files (never duplicated) |
| Analysis decisions | Which runs, which plots, efficiency scan, comparison | `tickets/*.yaml` |
| Physics | Efficiency, tracking, flux, etc. | `scripts/*.py` |
| Orchestration | Dependency resolution, isolation, reproducibility | Snakemake (`.smk` files) |

This separation lets you analyse any MWPC that produces the same `.ebe` + `.sett` format by simply writing a new detector YAML and a new ticket.

---

## 2. Repository Layout

```text
MuographyPackage/
├── Snakefile                      # top-level entry point
├── tickets/                       # analysis requests
│   └── LAB-REPORT-2026.yaml
├── detectors/                     # physical + DAQ configuration
│   └── elte_mwpc_2026.yaml
├── workflow/
│   └── rules/
│       ├── preflight.smk
│       ├── inspection.smk
│       ├── efficiency.smk
│       ├── tracking.smk
│       └── comparison.smk
├── scripts/                       # pure physics + I/O
│   ├── inspect_run.py
│   ├── efficiency_table.py
│   ├── all_efficiencies.py
│   ├── separate_efficiencies.py
│   ├── angular_distributions.py
│   ├── angular_map.py
│   ├── y_slice.py
│   ├── flux.py
│   ├── compare_runs.py
│   ├── cli_common.py
│   ├── mwpc_config.py
│   ├── mwpc_detector.py
│   ├── mwpc_efficiency.py
│   ├── mwpc_io.py
│   └── mwpc_tracking.py
├── ebe/                           # raw event files
├── sett/                          # settings / metadata files
├── cache/                         # parsed-run pickles (auto-generated)
└── outputs/                       # all results, isolated by ticket
    └── LAB-REPORT-2026/
        ├── preflight.done
        ├── efficiency/
        └── run200/
```

---

## 3. Quick Start

### 3.1 Prerequisites

- Python ≥ 3.10
- Snakemake ≥ 7
- pandas
- numpy
- matplotlib
- scipy
- PyYAML

```bash
pip install snakemake pandas numpy matplotlib scipy pyyaml
```

### 3.2 Data Layout

Place your data exactly like this:

```text
ebe/ElteLab2026A-Tracker_RunNNN.ebe
sett/ElteLab2026A-Tracker_RunNNN.sett
```

### 3.3 Run an Analysis

```bash
snakemake -j 8 --config ticket=LAB-REPORT-2026
```

Dry-run first:

```bash
snakemake -n -p --config ticket=LAB-REPORT-2026
```

---

## 4. Writing a Ticket

A ticket is a YAML file in `tickets/`.

Example: `tickets/LAB-REPORT-2026.yaml`

```yaml
ticket:
  id: "LAB-REPORT-2026"
  title: "Reproduction of the March 2026 lab report"

detector: "elte_mwpc_2026"          # must match a file in detectors/

# Runs for which per-run plots are requested
runs:
  - 200

per_run:
  inspect: false
  figure4: true          # angular distributions + track CSV
  figure5: true          # 2-D θx–θy map
  figure6: true          # Y-slice
  figure7: true          # flux

efficiency_scan:
  enabled: true
  runs: [202, 203, 204, 205, 206, 207, 208, 209]
  figure2: true          # all efficiencies on one canvas
  figure3: true          # individual + 2×2 panel

comparison:
  enabled: false
  # runs: [200, 209]     # only needed when enabled: true
```

### Ticket Rules

- `ticket.id` must equal the filename without `.yaml`.
- `detector` selects the geometry/DAQ configuration.
- Only the products set to `true` are generated.
- Outputs never overwrite each other; everything lives under `outputs/<ticket.id>/`.

---

## 5. Detector Configuration

Geometry and DAQ mapping live in `detectors/`.

Reference file: `detectors/elte_mwpc_2026.yaml`

```yaml
name: "elte_mwpc_2026"
description: "6-layer MWPC tower (HR-14 … HR-8)"

pitch_cm: 1.2
endpoint_separation_cm: 30.0
n_strips: 64

trigger_labels: [T5, T4, T3, T2, T1, T0]
chamber_names:  [HR14, HRA, HRB, HR13, HR12, HR8]

efficiency:
  reference_top: "HR14"
  reference_bottom: "HR8"
  under_test: "HRB"

tracking:
  endpoint_top: "HR14"
  endpoint_bottom: "HR8"
```

To analyse a different MWPC:

1. Copy the YAML.
2. Change the pitch, separation, chamber names, and other detector-specific values.
3. Point a ticket at the new detector name:

```yaml
detector: "my_new_mwpc"
```

No Python code changes are required.

---

## 6. What Each Script Does

| Script | Purpose |
|---|---|
| `inspect_run.py` | Print metadata + first events of one run |
| `efficiency_table.py` | Build numerical efficiency table vs HV |
| `all_efficiencies.py` | Figure-style combined efficiency plot |
| `separate_efficiencies.py` | Individual efficiency plots + 2×2 panel |
| `angular_distributions.py` | Reconstruct endpoint tracks + θ and θx distributions |
| `angular_map.py` | 2-D θx–θy flux map |
| `y_slice.py` | θx distribution for \|ΔY_strip\| ≤ 1 |
| `flux.py` | Report-style angular muon flux |
| `compare_runs.py` | Trigger-efficiency comparison between runs |

All scripts accept:

```text
--data-dir
--output-dir
--cache-dir
--detector
--no-cache
```

plus their specific arguments such as `--run`, `--runs`, etc.

---

## 7. Output Isolation

Every ticket produces a completely self-contained directory:

```text
outputs/LAB-REPORT-2026/
├── preflight.done
├── efficiency/
│   ├── efficiency_scan_table.csv
│   ├── all_efficiencies.png
│   └── efficiencies_2x2.png
└── run200/
    ├── run200_endpoint_tracks.csv
    ├── zenith_theta_flux.png
    ├── theta_x_flux.png
    ├── theta_x_theta_y_flux.png
    ├── theta_x_y_slice_flux.png
    ├── flux.png
    └── flux_table.csv
```

You can delete or archive any ticket directory without affecting others.

---

## 8. Preflight Checks

Before any analysis, the workflow:

1. Verifies that every required `.ebe` and `.sett` file exists.
2. Reports the nominal HV of each run, parsed from the `.sett` file.
3. Optionally enforces HV expectations if you add an `expected_hv` section to the ticket.

---

## 9. Adding a New Analysis

1. Place new `.ebe` / `.sett` files in the data directories.
2. Create a new ticket YAML, or copy an existing one.
3. Set the desired flags and run list.
4. Execute:

```bash
snakemake -j 8 --config ticket=YOUR-TICKET-ID
```

---

## 10. Caching

Parsed runs are stored as pickles in `cache/`.

Delete the corresponding `cache/run_NNN.pkl` if you change the parser.

Force a full re-parse with `--no-cache` when that option is passed through the workflow rules.

---

## 11. Reproducibility Notes

- Detector geometry is versioned in YAML.
- Analysis decisions are versioned in the ticket.
- Raw data remain untouched.
- Snakemake records the executed workflow and dependency state.

For stronger provenance, a future rule can write a `provenance.json` file into every ticket output directory containing information such as:

- Git commit
- Ticket hash
- Execution date
- Input file checksums

---

## 12. Common Commands

```bash
# Dry-run
snakemake -n -p --config ticket=LAB-REPORT-2026

# Full analysis using 8 cores
snakemake -j 8 --config ticket=LAB-REPORT-2026

# Only the preflight
snakemake preflight --config ticket=LAB-REPORT-2026

# Force re-run of everything
snakemake -j 8 --config ticket=LAB-REPORT-2026 --forceall

# Clean a ticket
rm -rf outputs/LAB-REPORT-2026 .snakemake
```

---

## 13. Extending the Factory

The current design deliberately stops at the point of diminishing returns.

Natural extensions include:

1. Ticket-configurable analysis parameters such as bin width, time mode, and maximum ΔY.
2. A simple run registry such as `runs.yaml` for metadata-based selection.
3. Automatic provenance files.
4. Additional detector YAMLs.

None of these require rewriting the existing physics scripts or the core workflow structure.

---

## 14. Contact / Citation

This package was developed for the ELTE MWPC cosmic-muon laboratory exercise (March 2026) and subsequently generalised into a reusable analysis factory.
