# workflow/rules/comparison.smk
"""Cross-run trigger-efficiency comparison."""

if TICKET.get("comparison", {}).get("enabled", False):

    COMP_RUNS = TICKET["comparison"]["runs"]
    COMP_DIR  = comparison_output_dir()

    rule compare_runs:
        input:
            ebe  = [ebe_file(r) for r in COMP_RUNS],
            sett = [sett_file(r) for r in COMP_RUNS],
        output:
            table = COMP_DIR / "comparison_runs.csv",
        params:
            runs = COMP_RUNS,
            data_dir = DATA_DIR,
            cache_dir = CACHE_DIR,
        log:
            COMP_DIR / "compare_runs.log"
        shell:
            """
            mkdir -p {COMP_DIR}
            python {SCRIPTS_DIR}/compare_runs.py \
                --data-dir {params.data_dir} \
                --output-dir {COMP_DIR} \
                --cache-dir {params.cache_dir} \
                --detector {DETECTOR_NAME} \
                --runs {params.runs} \
                > {log} 2>&1
            """