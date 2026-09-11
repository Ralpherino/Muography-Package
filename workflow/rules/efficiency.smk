# workflow/rules/efficiency.smk
"""Efficiency-scan rules."""

if TICKET.get("efficiency_scan", {}).get("enabled", False):

    EFF_RUNS = TICKET["efficiency_scan"]["runs"]
    WANT_FIG2 = TICKET["efficiency_scan"].get("figure2", True)
    WANT_FIG3 = TICKET["efficiency_scan"].get("figure3", True)

    EFF_DIR = efficiency_output_dir()
    TABLE   = EFF_DIR / "efficiency_scan_table.csv"

    rule build_efficiency_table:
        input:
            ebe  = [ebe_file(r) for r in EFF_RUNS],
            sett = [sett_file(r) for r in EFF_RUNS],
        output:
            table = TABLE,
        params:
            runs = EFF_RUNS,
            data_dir = DATA_DIR,
            cache_dir = CACHE_DIR,
        log:
            EFF_DIR / "build_efficiency_table.log"
        shell:
            """
            mkdir -p {EFF_DIR}
            python {SCRIPTS_DIR}/efficiency_table.py \
                --data-dir {params.data_dir} \
                --output-dir {EFF_DIR} \
                --cache-dir {params.cache_dir} \
                --detector {DETECTOR_NAME} \
                --runs {params.runs} \
                > {log} 2>&1
            """

    if WANT_FIG2:
        rule figure2_all_efficiencies:
            input:
                table = TABLE,
            output:
                plot = EFF_DIR / "all_efficiencies.png",
            params:
                data_dir = DATA_DIR,
                cache_dir = CACHE_DIR,
            log:
                EFF_DIR / "figure2.log"
            shell:
                """
                python {SCRIPTS_DIR}/all_efficiencies.py \
                    --data-dir {params.data_dir} \
                    --output-dir {EFF_DIR} \
                    --cache-dir {params.cache_dir} \
                    --detector {DETECTOR_NAME} \
                    --table efficiency_scan_table.csv \
                    > {log} 2>&1
                """

    if WANT_FIG3:
        rule figure3_separate_efficiencies:
            input:
                table = TABLE,
            output:
                panel = EFF_DIR / "efficiencies_2x2.png",
            params:
                data_dir = DATA_DIR,
                cache_dir = CACHE_DIR,
            log:
                EFF_DIR / "figure3.log"
            shell:
                """
                python {SCRIPTS_DIR}/separate_efficiencies.py \
                    --data-dir {params.data_dir} \
                    --output-dir {EFF_DIR} \
                    --cache-dir {params.cache_dir} \
                    --detector {DETECTOR_NAME} \
                    --table efficiency_scan_table.csv \
                    > {log} 2>&1
                """