from pathlib import Path
from datetime import datetime, timedelta
import argparse


TOTAL_TIMEPOINTS = 30
FACT_TIMEPOINT = 10
SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPT_DIR.parent / "logs"
START = datetime(2020, 5, 26, 12, 0, 0)


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


def build_facts_line(n_facts: int) -> str:
    return " ".join(f"b({idx});" for idx in range(1, n_facts + 1))


def write_log(n_facts: int) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"test__{n_facts}_facts.log"
    facts_line = build_facts_line(n_facts)

    with open(output_path, "w", buffering=1024 * 1024, encoding="utf-8") as f:
        for timepoint in range(TOTAL_TIMEPOINTS):
            timestamp = START + timedelta(minutes=timepoint)
            line = timestamp.strftime("%Y-%m-%dT%H:%M:%S")

            if timepoint == FACT_TIMEPOINT:
                line = f"{line} {facts_line}"

            f.write(line + "\n")

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate deterministic DP-sr input logs with b(X) facts.",
        add_help=False,
    )
    parser.add_argument(
        "--n-facts",
        required=True,
        type=parse_n_facts,
        help="Comma-separated fact counts, e.g. --n-facts=500,1000.",
    )

    args = parser.parse_args()

    for n_facts in args.n_facts:
        output_path = write_log(n_facts)
        print(
            f"{output_path} -> {n_facts} facts at timepoint {FACT_TIMEPOINT} "
            f"over {TOTAL_TIMEPOINTS} timepoints"
        )


if __name__ == "__main__":
    main()
