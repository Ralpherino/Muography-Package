# workflow/rules/inspection.smk
"""Optional per-run inspection."""

if TICKET.get("per_run", {}).get("inspect", False):

    rule inspect_run:
        input:
            ebe  = lambda wildcards: ebe_file(int(wildcards.run)),
            sett = lambda wildcards: sett_file(int(wildcards.run)),
        output:
            marker = run_output_dir("{run}") / "inspect.done",
        params:
            data_dir  = DATA_DIR,
            cache_dir = CACHE_DIR,
            out_dir   = lambda wildcards: run_output_dir(int(wildcards.run)),
        log:
            run_output_dir("{run}") / "inspect_run.log"
        shell:
            """
            mkdir -p {params.out_dir}
            python {SCRIPTS_DIR}/inspect_run.py \
                --data-dir {params.data_dir} \
                --output-dir {params.out_dir} \
                --cache-dir {params.cache_dir} \
                --detector {DETECTOR_NAME} \
                --run {wildcards.run} \
                > {log} 2>&1
            touch {output.marker}
            """