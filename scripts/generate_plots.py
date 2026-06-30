from pathlib import Path
import argparse
from collections import defaultdict
import re


MAX_TIMEPOINTS = 30
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_DIR = SCRIPT_DIR.parent
DEFAULT_OUTPUT_DIR = REPO_DIR / "plots results"

TITLE_SIZE = 20
AXIS_LABEL_SIZE = 18
TICK_LABEL_SIZE = 12.5
LEGEND_SIZE = 16

SUPPORTED_EXTENSIONS = {".txt", ".log", ".out"}
DP_SR_OUTPUT_DIR = "dp-sr_output"
WITH_FUTURE_DIR = "with_future_atom_output"
WITHOUT_FUTURE_DIR = "without_future_atom_output"

RUN_DIR_RE = re.compile(r"run[_-]?(\d+)$", re.IGNORECASE)

TIMEPOINT_RE = re.compile(
    r"TIME POINT:\s*([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2})(?::[0-9]{2})?"
)
TIME_SPENT_RE = re.compile(
    r"time spent1?:\s*([0-9]+(?:[,.][0-9]+)?)\s*s"
)
FACTS_RE = re.compile(r"(?:^|[_-])(\d+)_facts(?:$|[_-])")


def parse_n_facts(value: str) -> list[int]:
    facts = []

    for raw_item in value.split(","):
        item = raw_item.strip()

        if not item:
            continue

        try:
            n_facts = int(item)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(
                f"Invalid fact count '{item}'. Use comma-separated integers."
            ) from exc

        if n_facts <= 0:
            raise argparse.ArgumentTypeError(
                f"Invalid fact count '{item}'. Values must be positive integers."
            )

        if n_facts not in facts:
            facts.append(n_facts)

    if not facts:
        raise argparse.ArgumentTypeError("At least one fact count is required.")

    return facts


def parse_fact_count_from_name(path: Path) -> int | None:
    match = FACTS_RE.search(path.stem)

    if not match:
        return None

    return int(match.group(1))


def find_run_file(folder: Path, n_facts: int) -> Path:
    expected = folder / f"out__{n_facts}_facts.txt"

    if expected.is_file():
        return expected

    matches = sorted(
        path
        for path in folder.iterdir()
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
        and parse_fact_count_from_name(path) == n_facts
    )

    if not matches:
        raise FileNotFoundError(
            f"Missing output for {n_facts} facts in {folder}. "
            f"Expected {expected.name}."
        )

    if len(matches) > 1:
        names = ", ".join(path.name for path in matches)
        raise RuntimeError(
            f"Ambiguous output for {n_facts} facts in {folder}: {names}."
        )

    return matches[0]


def find_run_dirs(dp_sr_output_dir: Path) -> list[Path]:
    run_dirs = sorted(
        path
        for path in dp_sr_output_dir.iterdir()
        if path.is_dir()
        and RUN_DIR_RE.match(path.name)
        and (path / WITH_FUTURE_DIR).is_dir()
        and (path / WITHOUT_FUTURE_DIR).is_dir()
    )

    if not run_dirs:
        raise FileNotFoundError(
            f"No run directories found in {dp_sr_output_dir}. "
            f"Expected directories such as run_01, run_02, ..., run_10."
        )

    return run_dirs


def load_runs(input_path: Path, n_facts_values: list[int]) -> dict[int, tuple[list[Path], list[Path]]]:
    dp_sr_output_dir = input_path / DP_SR_OUTPUT_DIR

    if not dp_sr_output_dir.is_dir():
        raise FileNotFoundError(
            f"Missing directory: {dp_sr_output_dir}. "
            f"--input-path must be the directory containing {DP_SR_OUTPUT_DIR}."
        )

    run_dirs = find_run_dirs(dp_sr_output_dir)
    runs = {}

    for n_facts in n_facts_values:
        with_future_files = []
        without_future_files = []

        for run_dir in run_dirs:
            with_future_dir = run_dir / WITH_FUTURE_DIR
            without_future_dir = run_dir / WITHOUT_FUTURE_DIR

            with_future_files.append(
                find_run_file(with_future_dir, n_facts)
            )

            without_future_files.append(
                find_run_file(without_future_dir, n_facts)
            )

        runs[n_facts] = (
            with_future_files,
            without_future_files,
        )

    return runs


def parse_latency_by_timepoint(path: Path, max_timepoints: int = MAX_TIMEPOINTS):
    latencies = defaultdict(float)

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if "time spent" not in line or "TIME POINT:" not in line:
                continue

            tp_match = TIMEPOINT_RE.search(line)
            time_match = TIME_SPENT_RE.search(line)

            if not tp_match or not time_match:
                continue

            timepoint = tp_match.group(1)
            value = float(time_match.group(1).replace(",", "."))
            latencies[timepoint] += value

    labels = sorted(latencies.keys())[:max_timepoints]
    values = [latencies[label] for label in labels]

    if len(values) < max_timepoints:
        values.extend([0.0] * (max_timepoints - len(values)))

    return values


def average_latency_by_timepoint(files: list[Path], max_timepoints: int = MAX_TIMEPOINTS):
    sums = [0.0] * max_timepoints

    for path in files:
        values = parse_latency_by_timepoint(path, max_timepoints)

        for index, value in enumerate(values):
            sums[index] += value

    averages = [
        value / len(files)
        for value in sums
    ]

    return list(range(max_timepoints)), averages


def format_axis(ax, max_timepoints: int = MAX_TIMEPOINTS):
    ax.set_xlim(0, max_timepoints - 1)
    ax.set_xticks(range(max_timepoints))
    ax.set_xlabel("timepoint", fontsize=AXIS_LABEL_SIZE)
    ax.set_ylabel("Average Processing-Time Latency (s)", fontsize=AXIS_LABEL_SIZE)
    ax.tick_params(axis="both", labelsize=TICK_LABEL_SIZE)
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=LEGEND_SIZE)


def add_comparison_plot(
    ax,
    n_facts: int,
    with_future_files: list[Path],
    without_future_files: list[Path],
):
    x_with, y_with = average_latency_by_timepoint(with_future_files)
    x_without, y_without = average_latency_by_timepoint(without_future_files)

    ax.plot(
        x_with,
        y_with,
        marker="o",
        markerfacecolor="none",
        linewidth=1.2,
        label="With future constructs",
    )

    ax.plot(
        x_without,
        y_without,
        marker="s",
        markerfacecolor="none",
        linewidth=1.2,
        label="Without future constructs",
    )

    ax.set_title(
        f"Encoding comparison: input facts = {n_facts}",
        fontsize=TITLE_SIZE,
        pad=12,
    )
    format_axis(ax)


def plot_one(
    n_facts: int,
    with_future_files: list[Path],
    without_future_files: list[Path],
    output_dir: Path,
):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(11.5, 5.5))

    add_comparison_plot(
        ax,
        n_facts,
        with_future_files,
        without_future_files,
    )

    fig.tight_layout(pad=1.2)

    output_path = output_dir / f"plot__{n_facts}_facts.png"
    fig.savefig(output_path, dpi=200, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate average latency plots comparing executions with and without "
            "future constructs."
        )
    )

    parser.add_argument(
        "--n-facts",
        required=True,
        type=parse_n_facts,
        help="Comma-separated fact counts, e.g. --n-facts=500,1000,1500,2000.",
    )

    args = parser.parse_args()

    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    runs = load_runs(REPO_DIR, args.n_facts)
    generated = []

    for n_facts, (with_future_files, without_future_files) in runs.items():
        print(
            f"{n_facts} facts: averaging "
            f"{len(with_future_files)} runs with future constructs and "
            f"{len(without_future_files)} runs without future constructs"
        )

        generated.append(
            plot_one(
                n_facts,
                with_future_files,
                without_future_files,
                DEFAULT_OUTPUT_DIR,
            )
        )

    print("Generated plots:")
    for path in generated:
        print(path)


if __name__ == "__main__":
    main()