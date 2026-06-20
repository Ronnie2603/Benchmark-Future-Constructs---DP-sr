# Benchmark Future Constructs - DP-sr

This repository compares two versions of the same DP-sr benchmark:

- `encodings/test_with_future_constructs.idlvsr`: encoding that uses future constructs.
- `encodings/test_without_future_constructs.idlvsr`: equivalent encoding without future constructs.
- `scripts/generate_logs.py`: generates deterministic input logs.
- `scripts/generate_plots.py`: generates one PNG comparison plot for each fact count.
- `logs/`: generated input logs used for the comparison.
- `plots results/`: default directory for generated plot PNGs. Already containing comparison plots.

## Setup

Install the Python dependencies:

```bash
python -m pip install -r requirement.txt
```

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

Each file contains 30 total timepoints, one per minute, starting from
`2020-05-26T12:00:00`. All facts are generated at timepoint 10
(`2020-05-26T12:10:00`) and always have this form:

```text
b(1); b(2); ... b(N);
```

`N` is the fact count requested for that generated log.

## Run DP-sr

Run DP-sr on the generated logs with both encoding versions:

- `encodings/test_with_future_constructs.idlvsr`
- `encodings/test_without_future_constructs.idlvsr`

Run DP-sr with verbose output enabled, for example by using the `--verbose` option. This ensures that the output files include the per-time-point latency lines used by the plotting script, such as `TIME POINT` and `time spent1`, allowing it to produce one curve for the execution with future constructs and one curve for the execution without future constructs.

Save those DP-sr output files in a directory named exactly `dp-sr_output/` with this structure:

```text
dp-sr_output/
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
```

The number in each file name must match at least one of the values passed to `--n-facts`.

## Generate Plots

Generate the plots with:

```bash
python scripts/generate_plots.py --n-facts=500,1000,1500,2000 --input-path .
```

`--input-path` must point to the directory that contains `dp-sr_output/`.
The script then reads:

```text
<input-path>/dp-sr_output/with_future_atom_output/
<input-path>/dp-sr_output/without_future_atom_output/
```

Default outputs:

```text
plots results/plot__500_facts.png
plots results/plot__1000_facts.png
plots results/plot__1500_facts.png
plots results/plot__2000_facts.png
```

Change the destination directory with:

```bash
python scripts/generate_plots.py \
  --n-facts=500,1000 \
  --input-path path/containing/dp-sr_output \
  --output-dir path/to/plots
```