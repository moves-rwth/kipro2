from pathlib import Path
from typing import List, Optional, Dict
import attr
import pickle
import click
import sys
import pandas as pd
import math

# make kipro2's types available
sys.path.insert(0, str(Path(__file__).parent.parent))

from kipro2.utils.statistics import Statistics


@attr.s
class Stats:
    name: str = attr.ib()
    bmc: Optional[Statistics] = attr.ib()
    kind: Optional[Statistics] = attr.ib()


def read_stats(base: Path) -> List[Stats]:
    files = base.glob("*.pickle")
    stats = []
    for file in files:
        with open(file, 'rb') as f:
            stats.append(pickle.load(f))
    by_name: Dict[str, List[Statistics]] = dict()
    for stat in stats:
        by_name.setdefault(stat.args["name"], []).append(stat)
    res = []
    for name, stats in by_name.items():
        bmc = next((stat for stat in stats if stat.args["checker"] == "bmc"),
                   None)
        kind = next((stat for stat in stats if stat.args["checker"] == "kind"),
                    None)
        res.append(Stats(name, bmc, kind))
    res.sort(key=lambda stat: stat.name)
    return res


def make_table(stats: List[Stats]) -> pd.DataFrame:
    records = []
    for stat in stats:
        if not (stat.bmc is not None and stat.kind is not None):
            print(f"skipping incomplete: {stat.name}", file=sys.stderr)
            continue
        statuses = [stat.bmc.status, stat.kind.status]
        if "refuted" in statuses and "sigterm" in statuses:
            status = "refuted"
        elif "inductive" in statuses and "sigterm" in statuses:
            status = "inductive"
        else:
            status = ", ".join(statuses)
        if stat.bmc.status == "refuted":
            total_time = stat.bmc.total_time.value
            k = stat.bmc.k
            sat_check_time = stat.bmc.sat_check_time.value
            compute_formulae_time = stat.bmc.compute_formulae_time.value
            num_formulae = stat.bmc.number_formulae
        elif stat.kind.status == "inductive":
            total_time = stat.kind.total_time.value
            k = stat.kind.k
            sat_check_time = stat.kind.sat_check_time.value
            compute_formulae_time = stat.kind.compute_formulae_time.value
            num_formulae = stat.kind.number_formulae
        else:
            total_time = None
            k = None
            compute_formulae_time = None
            sat_check_time = None
            num_formulae = None

        records.append({
            "name": stat.name,
            "pre": stat.bmc.args["pre"],
            "post": stat.bmc.args["post"],
            "k": k,
            "num_formulae": num_formulae,
            "compute_formulae_time": compute_formulae_time,
            "sat_check_time": sat_check_time,
            "status": status,
            "total_time": total_time,
        })
    return pd.DataFrame.from_records(records)


def format_times(path: Path, format: str, data: pd.DataFrame):
    """Format time values in the data frame according to the --time-format option."""
    if (len(data) == 0):
        return data

    convert_to_ms = format == "ms" or (format == "auto"
                                       and "one_loop_examples" in str(path))

    if convert_to_ms:
        print("Times are formatted in milliseconds.", file=sys.stderr)
        time_columns = [
            "compute_formulae_time", "sat_check_time", "total_time"
        ]

        def to_ms(value: float) -> float:
            if not pd.isna(value):
                return value * 1000
            else:
                return value

        for col in time_columns:
            data[col] = data[col].apply(to_ms)
    else:
        print("Times are formatted in seconds.", file=sys.stderr)

    print(file=sys.stderr)  # empty line


@click.command()
@click.argument("path", required=True, type=click.Path())
@click.option("--latex/--no-latex",
              default=False,
              help="Output a LaTeX table.")
@click.option(
    '--time-format',
    default="auto",
    type=click.Choice(["auto", "s", "ms"]),
    help=
    "Unit for time values. The `auto` option will format data from paths containing `one_loop_examples` in `ms`, `s` otherwise. Defaults to `auto`."
)
def main(path, latex, time_format):
    path = Path(str(path))
    stats = read_stats(path)
    table = make_table(stats)
    format_times(path, time_format, table)

    if len(table) == 0:
        print("No benchmark results for this selection of results.")
        return

    if latex:
        print(table[[
            "name", "pre", "status", "k", "num_formulae",
            "compute_formulae_time", "sat_check_time", "total_time"
        ]].to_latex(index=False,
                    bold_rows=True,
                    escape=True,
                    na_rep="/",
                    float_format="%.2f",
                    formatters={
                        "k": lambda k: str(int(k))
                        if not math.isnan(k) else "/"
                    }))
    else:
        print(table)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
