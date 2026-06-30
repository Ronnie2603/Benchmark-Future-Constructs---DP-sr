# Benchmark Future Constructs - DP-sr

This repository compares two versions of the same DP-sr benchmark:

* `encodings/test_with_future_constructs.idlvsr`: encoding that uses future constructs.
* `encodings/test_without_future_constructs.idlvsr`: equivalent encoding without future constructs.
* `scripts/generate_logs.py`: generates deterministic input logs.
* `scripts/run_10_runs.py`: runs each encoding 10 times for every input size.
* `scripts/generate_plots.py`: averages the 10 runs and generates one comparison plot for each input size.
* `logs/`: generated input logs used for the comparison.
* `plots results/`: default directory for generated plot PNGs. Already containing comparison plots.

The benchmark results are based on 10 runs for every combination of encoding and input size. At each timepoint, the plots compare the average latency of the 10 runs with future constructs against the average latency of the 10 runs without future constructs.

The repository also provides a pre-release DP-sr executable `.jar` that includes support for future constructs. The official DP-sr release containing this feature will be published soon. Until then, the provided pre-release `.jar` should be used to reproduce the experiments in this repository.

## Setup

Install the Python dependencies:

```bash
python -m pip install -r requirement.txt
```

Make sure Java 11 is installed.

## DP-sr Pre-release Executable

Use the provided `.jar` when running the experiments. For example:

```bash
java -jar DP-sr-v1.1.0-pre-release.jar \
  --program=encodings/test_with_future_constructs.idlvsr \
  --log=logs/test__500_facts.log \
  --parallelism=1 \
  --t-unit=min \
  --verbose
```

where:
* `--program` specifies the DP-sr encoding to execute.
* `--log` specifies the input stream log.
* `--parallelism=1` runs the benchmark with a single parallel execution unit.
* `--t-unit=min` sets the temporal unit to minutes.
* `--verbose` should be enabled when collecting output files for plotting.

## Generate Logs

Generate logs for one or more fact counts:

```bash
python scripts/generate_logs.py --n-facts=500,1000,1500,2000
```

The script creates the files in `logs/`:

```text
logs/test__500_facts.log
logs/test__1000_facts.log
logs/test__1500_facts.log
logs/test__2000_facts.log
```

Each file contains 30 total timepoints, one per minute, starting from `2020-05-26T12:00:00`. All facts are generated at timepoint 10 (`2020-05-26T12:10:00`) and always have this form:

```text
b(1); b(2); ... b(N);
```

`N` is the fact count requested for that generated log.

## Run DP-sr

Run the complete benchmark with:

```bash
python scripts/run_10_runs.py --n-facts=500,1000,1500,2000
```

For every input size, `scripts/run_10_runs.py` executes both `test_with_future_constructs.idlvsr` and `test_without_future_constructs.idlvsr` 10 times, producing 20 executions per input size.

Outputs are saved automatically with this structure:

```text
dp-sr_output/
  run_01/
    with_future_atom_output/
      out__500_facts.txt
      out__1000_facts.txt
      out__1500_facts.txt
      out__2000_facts.txt
    without_future_atom_output/
      out__500_facts.txt
      out__1000_facts.txt
      out__1500_facts.txt
      out__2000_facts.txt
  run_02/
    ...
  ...
  run_10/
    ...
```

The script uses the provided pre-release JAR, the files in `logs/`, parallelism `1`, and `min` as the time unit.

## Generate Plots

Generate the plots with:

```bash
python scripts/generate_plots.py --n-facts=500,1000,1500,2000
```

The script reads the `run_01` through `run_10` directories and, separately for each encoding and input size, averages the processing-time latency at every timepoint over the 10 runs:

```text
dp-sr_output/run_XX/with_future_atom_output/
dp-sr_output/run_XX/without_future_atom_output/
```

Default outputs:

```text
plots results/plot__500_facts.png
plots results/plot__1000_facts.png
plots results/plot__1500_facts.png
plots results/plot__2000_facts.png
```