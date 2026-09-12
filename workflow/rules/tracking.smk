# workflow/rules/tracking.smk
"""Per-run angular reconstruction and flux plots."""

PER_RUN = TICKET.get("per_run", {})
WANT_FIG4 = PER_RUN.get("figure4", False)
WANT_FIG5 = PER_RUN.get("figure5", False)
WANT_FIG6 = PER_RUN.get("figure6", False)
WANT_FIG7 = PER_RUN.get("figure7", False)

# Figure 4 (always required when any later figure is requested)
if WANT_FIG4 or WANT_FIG5 or WANT_FIG6 or WANT_FIG7:

    rule figure4_angular_distributions:
        input:
            ebe  = lambda wildcards: ebe_file(int(wildcards.run)),
            sett = lambda wildcards: sett_file(int(wildcards.run)),
        output:
            fig4a  = run_output_dir("{run}") / "zenith_theta_flux.png",
            fig4b  = run_output_dir("{run}") / "theta_x_flux.png",
            tracks = run_output_dir("{run}") / "run{run}_endpoint_tracks.csv",
        params:
            data_dir  = DATA_DIR,
            cache_dir = CACHE_DIR,
            out_dir   = lambda wildcards: run_output_dir(int(wildcards.run)),
            time_mode = "timestamps",
        log:
            run_output_dir("{run}") / "angular_distributions.log"
        shell:
            """
            mkdir -p {params.out_dir}
            python {SCRIPTS_DIR}/angular_distributions.py \
                --data-dir {params.data_dir} \
                --output-dir {params.out_dir} \
                --cache-dir {params.cache_dir} \
                --detector {DETECTOR_NAME} \
                --run {wildcards.run} \
                --time-mode {params.time_mode} \
                > {log} 2>&1
            """

if WANT_FIG5:

    rule figure5_angular_map:
        input:
            tracks = run_output_dir("{run}") / "run{run}_endpoint_tracks.csv",
            ebe    = lambda wildcards: ebe_file(int(wildcards.run)),
        output:
            plot = run_output_dir("{run}") / "theta_x_theta_y_flux.png",
        params:
            data_dir  = DATA_DIR,
            cache_dir = CACHE_DIR,
            out_dir   = lambda wildcards: run_output_dir(int(wildcards.run)),
            time_mode = "timestamps",
        log:
            run_output_dir("{run}") / "angular_map.log"
        shell:
            """
            python {SCRIPTS_DIR}/angular_map.py \
                --data-dir {params.data_dir} \
                --output-dir {params.out_dir} \
                --cache-dir {params.cache_dir} \
                --detector {DETECTOR_NAME} \
                --run {wildcards.run} \
                --time-mode {params.time_mode} \
                > {log} 2>&1
            """

if WANT_FIG6:

    rule figure6_y_slice:
        input:
            tracks = run_output_dir("{run}") / "run{run}_endpoint_tracks.csv",
            ebe    = lambda wildcards: ebe_file(int(wildcards.run)),
        output:
            plot     = run_output_dir("{run}") / "theta_x_y_slice_flux.png",
            selected = run_output_dir("{run}") / "run{run}_y_slice_events.csv",
        params:
            data_dir  = DATA_DIR,
            cache_dir = CACHE_DIR,
            out_dir   = lambda wildcards: run_output_dir(int(wildcards.run)),
            time_mode = "timestamps",
            max_dy    = 1,
        log:
            run_output_dir("{run}") / "y_slice.log"
        shell:
            """
            python {SCRIPTS_DIR}/y_slice.py \
                --data-dir {params.data_dir} \
                --output-dir {params.out_dir} \
                --cache-dir {params.cache_dir} \
                --detector {DETECTOR_NAME} \
                --run {wildcards.run} \
                --time-mode {params.time_mode} \
                --max-dy-strip {params.max_dy} \
                > {log} 2>&1
            """

if WANT_FIG7:

    rule figure7_flux:
        input:
            tracks = run_output_dir("{run}") / "run{run}_endpoint_tracks.csv",
            ebe    = lambda wildcards: ebe_file(int(wildcards.run)),
        output:
            table = run_output_dir("{run}") / "flux_table.csv",
            plot  = run_output_dir("{run}") / "flux.png",
        params:
            data_dir  = DATA_DIR,
            cache_dir = CACHE_DIR,
            out_dir   = lambda wildcards: run_output_dir(int(wildcards.run)),
            time_mode = "timestamps",
            max_dy    = 1,
        log:
            run_output_dir("{run}") / "flux.log"
        shell:
            """
            python {SCRIPTS_DIR}/flux.py \
                --data-dir {params.data_dir} \
                --output-dir {params.out_dir} \
                --cache-dir {params.cache_dir} \
                --detector {DETECTOR_NAME} \
                --run {wildcards.run} \
                --time-mode {params.time_mode} \
                --max-dy-strip {params.max_dy} \
                > {log} 2>&1
            """