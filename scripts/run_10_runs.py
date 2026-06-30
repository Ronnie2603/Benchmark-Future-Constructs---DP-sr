from pathlib import Path
import argparse
import subprocess


RUNS = 10
PARALLELISM = 1
T_UNIT = "min"
JAVA_COMMAND = "java"


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_DIR = SCRIPT_DIR.parent

DEFAULT_JAR = REPO_DIR / "DP-sr-v1.1.0-pre-release.jar"
DEFAULT_LOGS_DIR = REPO_DIR / "logs"
DEFAULT_OUTPUT_DIR = REPO_DIR / "dp-sr_output"

DEFAULT_WITH_FUTURE_PROGRAM = (
    REPO_DIR / "encodings" / "test_with_future_constructs.idlvsr"
)
DEFAULT_WITHOUT_FUTURE_PROGRAM = (
    REPO_DIR / "encodings" / "test_without_future_constructs.idlvsr"
)

WITH_FUTURE_DIR = "with_future_atom_output"
WITHOUT_FUTURE_DIR = "without_future_atom_output"


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


def require_file(path: Path, description: str):
    if not path.is_file():
        raise FileNotFoundError(f"Missing {description}: {path}")


def to_repo_relative(path: Path) -> str:
    """
    DP-sr/Flink may incorrectly concatenate absolute paths with the working
    directory. For this reason, files inside the repository are passed as
    paths relative to REPO_DIR.
    """
    resolved_path = path.resolve()
    resolved_repo = REPO_DIR.resolve()

    try:
        return str(resolved_path.relative_to(resolved_repo))
    except ValueError:
        return str(resolved_path)


def run_dp_sr(
    java_command: str,
    jar_path: Path,
    program_path: Path,
    log_path: Path,
    output_path: Path,
    parallelism: int,
    t_unit: str,
):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        java_command,
        "-jar",
        to_repo_relative(jar_path),
        f"--program={to_repo_relative(program_path)}",
        f"--log={to_repo_relative(log_path)}",
        f"--parallelism={parallelism}",
        f"--t-unit={t_unit}",
        "--verbose",
    ]

    print("Running:", " ".join(command))
    print("Output:", output_path)

    with open(output_path, "w", encoding="utf-8") as out:
        result = subprocess.run(
            command,
            stdout=out,
            stderr=subprocess.STDOUT,
            check=False,
            cwd=REPO_DIR,
        )

    if result.returncode != 0:
        print(f"\nDP-sr failed with exit code {result.returncode}")
        print(f"Check output file: {output_path}")
        print("\nLast lines of the output:")

        try:
            lines = output_path.read_text(
                encoding="utf-8",
                errors="replace",
            ).splitlines()

            for line in lines[-50:]:
                print(line)

        except Exception as exc:
            print(f"Could not read output file: {exc}")

        raise SystemExit(result.returncode)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Run the DP-sr benchmark 10 times for each fact count, "
            "both with and without future constructs."
        )
    )

    parser.add_argument(
        "--n-facts",
        required=True,
        type=parse_n_facts,
        help="Comma-separated fact counts, e.g. --n-facts=500,1000,1500,2000.",
    )

    args = parser.parse_args()

    require_file(DEFAULT_JAR, "DP-sr jar")
    require_file(DEFAULT_WITH_FUTURE_PROGRAM, "with-future encoding")
    require_file(DEFAULT_WITHOUT_FUTURE_PROGRAM, "without-future encoding")

    for run_index in range(1, RUNS + 1):
        run_dir = DEFAULT_OUTPUT_DIR / f"run_{run_index:02d}"

        for n_facts in args.n_facts:
            log_path = DEFAULT_LOGS_DIR / f"test__{n_facts}_facts.log"
            require_file(log_path, "input log")

            with_future_output = (
                run_dir
                / WITH_FUTURE_DIR
                / f"out__{n_facts}_facts.txt"
            )

            without_future_output = (
                run_dir
                / WITHOUT_FUTURE_DIR
                / f"out__{n_facts}_facts.txt"
            )

            run_dp_sr(
                java_command=JAVA_COMMAND,
                jar_path=DEFAULT_JAR,
                program_path=DEFAULT_WITH_FUTURE_PROGRAM,
                log_path=log_path,
                output_path=with_future_output,
                parallelism=PARALLELISM,
                t_unit=T_UNIT,
            )

            run_dp_sr(
                java_command=JAVA_COMMAND,
                jar_path=DEFAULT_JAR,
                program_path=DEFAULT_WITHOUT_FUTURE_PROGRAM,
                log_path=log_path,
                output_path=without_future_output,
                parallelism=PARALLELISM,
                t_unit=T_UNIT,
            )

    print("Completed benchmark runs.")
    print(f"Runs: {RUNS}")
    print(f"Output directory: {DEFAULT_OUTPUT_DIR}")


if __name__ == "__main__":
    main()