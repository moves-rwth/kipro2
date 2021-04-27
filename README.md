# kipro2: Bounded Model Checking and k-Induction for Probabilistic Programs

This is the implementation `kipro2` to our paper _"Latticed k-Induction with an Application to Probabilistic Programs"_ in Computer Aided Verification 2021 by Batz et al.
The [PDF file](latticed_k_induction_cav21.pdf) is available in this repository.

---
As part of our CAV submission, we provide a Docker image to play with.
Download at TODO URL.
Start via
```
docker image load -i kipro2.tar.gz
docker run -it kipro2
```
---

kipro2 can do bounded model checking and k-induction on probabilistic programs in parallel.
It can try to prove inductiveness or try to refute properties like `wp[C](f) <= g` for arbitrary initial program states.

## Contents

 1. Usage: How to reproduce our benchmarks and run your own code.
 2. How to build our Docker image.
 3. Installation on your own machine.
 4. Architecture of the code.
 5. How to work with the code.
 6. Benchmarks in detail.
 7. Accepted syntax.
 8. License.

## 1. Usage

### Benchmarks

Go to the _Benchmarks_ section below to read how our benchmarks work in more detail.
To just reproduce the results from our paper, run one of
```bash
bash benchmark.sh --timeout=300  # 5 minute timeout per input, takes about 35min total
bash benchmark.sh                # 15 minute timeout (default)
```

### Example: Verifying Runtime Upper Bounds

Let's look at the first geometric loop example (`benchmarks/cav21/geo1.pgcl`).

```
// ARGS: --post c --pre "c+1" --checker both --assert-inductive 2

nat c;
nat f;

while(f=1){
   {f := 0}[0.5]{c := c+1}
}
```

You can verify inductiveness of the pre-expectation bound `c+1` for the _probabilistic weakest pre-expectation transformer_ the post-expectation `c` by running
```
poetry run kipro2 benchmarks/cav21/geo1.pgcl
```
The output contains "Property is 2-inductive". Success!

Let's look at the program itself in more detail.
The first line in the program is a comment that is interpreted by kipro2 to use as default arguments to the program.
We could also have executed `poetry run kipro2 benchmarks/cav21/geo1.pgcl --post c --pre "c+1" --assert-inductive 2` without the `// ARGS:` comment.
The `--assert-inductive 2` is used to assert after execution that the result is correct.

The first two actual code lines declare to natural number variables `c`, `f`.
While `f=1`, the loop does a coin flip (with probability ½) and either sets `f` to `0` or increments `c` by one.

So what we ask kipro2 is: Prove (using k-induction) or refute (using bounded model checking) that `wp[program](c) <= c+1`.
You can read it as: If we observe `c` after the program's termination, is `c+1` a valid upper bound for the state before execution?
The question is one over _all initial states_ with arbitrary values for the variables.
This property is 2-inductive, so the answer is yes!

### Example: Refutation of Weakest Pre-expectation Bounds

As a second example, we refute a bound on the geometric loop that is not valid: `c+0.999999999999`.
```
poetry run kipro2 benchmarks/cav21/geo2.pgcl
```

```
// ARGS: --post c --pre "c+0.999999999999" --checker both

nat c;
nat f;

while(f=1){
   {f := 0}[0.5]{c := c+1}
}
```

kipro2 refutes the property in the comment (`wp[geo2](c) <= c+0.999999999999`) after about a second with `k = 46`.

The output might be a bit ugly since it is the result of running both the bouded model checking engine and the induction engine in parallel (`--checker both`).
We can run the tool again, but now with `--checker bmc` to only run the bounded model checker:
```
poetry run kipro2 benchmarks/cav21/geo2.pgcl --checker bmc
```
There's even a counter-example for the initial state that violates the property:
```
kipro2: SAT. Model:
f := 1
c := 1648
```

### More Examples

You can find two more examples for **runtime bounds** in [EXAMPLES.md](EXAMPLES.md).

## 2. CAV Artifact Docker Image

You can experiment with kipro2 in a convenient Docker image, as was provided for the CAV submission.
The output of `poetry run kipro2_benchmark run geo` (just the `geo` benchmarks) is already provided in `benchmarks/geo.log` along with the `stats_` directories as an example.

Build the Docker image: `docker build -t kipro2 -f cav_artifact/Dockerfile .`
To load a docker image: `docker image load -i kipro2.tar`.

More information can be found in [`cav_artifact/README.md`](cav_artifact/README.md).

## 3. Installation

This project uses git submodules.
You may need to run `git submodule init && git submodule update`.

We use [poetry](https://github.com/python-poetry/poetry) for dependency management.
See [here](https://python-poetry.org/docs/) for installation instructions for poetry.

Just execute `poetry install` to hack on this project locally.

We used [z3](https://github.com/Z3Prover/z3) for our experiments.
If you do not have z3 installed, you might want to run `poetry run pysmt-install --z3` to install z3 using `pysmt`'s installer.

## 4. Architecture

kipro2 is a Python 3 application using [pysmt](https://github.com/pysmt/pysmt) and [Probably](https://github.com/Philipp15b/probably).
Probably is a library built at MOVES for kipro2 to parse and work with pGCL programs and expectations.
Its internals are [quite extensively documented](https://philipp15b.github.io/probably/), so if there are questions about the input language of kipro2, you might want to look there.
You can find probably's source code in `.venv/src/probably` after installation.

By default (`--checker both`), kipro2 runs both the bounded model checker engine (`--checker bmc`) and the k-induction engine (`--checker kind`) in parallel.
Both run in separate threads.
For debugging, it might be useful to just use one engine at a time.

## 5. Development

**Typechecking:** Run `mypy` with `make mypy`.

**Tests:** Run tests with `make test` ([`pytest`](https://docs.pytest.org/en/latest/)).
Tests also produce a coverage report. It can be found in the generated `htmlcov` directory.

**Lint:** Run `pylint` with `make lint`.

**Formatting:** We use the [`yapf`](https://github.com/google/yapf) formatter: `yapf --recursive -i kipro2/` and `isort kipro2/`.

## 6. Benchmarks

There is a benchmark script along with a set of example programs to run.
You can access the script (and view its help) via: `poetry run kipro2_benchmark` or with `python benchmarks/benchmark.py`.

Benchmarks are executed with a default memory limit of about 8 GB and a timeout of 15 minutes.
Use the `--memory MB_LIMIT` and `--timeout SECONDS_LIMIT` flags to change these defaults.

Note: The benchmarks use the [timeout](https://github.com/pshved/timeout) script which is only available on Linux.

**Show a list of benchmark commands to be run:**
```
poetry run kipro2_benchmark list [FILTER]
```
where `[FILTER]` is an optional regular expression to filter to a subset of the benchmarks.

**Running benchmarks:**
```
poetry run kipro2_benchmark run [FILTER]
```

This script will run the benchmarks in sequence.

The full benchmark set takes quite a while to run.
Use a filter like `geo` to run just `geo1`, `geo2` and `geo3` benchmarks.
They terminate in a few seconds.
Or attach something like `--timeout 60` for a timeout of 60 seconds.

A new directory `benchmarks/stats_TIMESTAMP/` will be created automatically and results (using `--stats-path`) wil be written into it for each benchmark.
For each set, there will be two subdirectories, `one_loop_examples` and `cav21`.

**Viewing benchmark results:**

You can view the generated `.json` files manually, or create a table using the `python3 benchmarks/tabulate.py` script (adjusting the path accordingly):
```bash
poetry shell
python3 benchmarks/tabulate.py --help
python3 benchmarks/tabulate.py benchmarks/stats_TIMESTAMP/one_loop_examples
python3 benchmarks/tabulate.py benchmarks/stats_TIMESTAMP/cav21
```

The `tabulate.py` script also supports output as a LaTeX table with `--latex` and different time formats (see `--help`).

The resulting table will contain input parameters such as `pre` and `post`, as well as the number of formulae computed (`num_formulae`) and the time needed for it (`compute_formulae_time`).
Total SAT check time is listed in column `sat_check_time`.
`status` indicates the two statuses of the BMC engine and the k-induction engine.
Usually, if one engine terminates with either `refuted` or `inductive` respectively, kipro2 will terminate.
The other engine may be marked as `started` only.
This is intentional.
Finally, `total_time` indicates the total time needed for kipro2 to terminate (excluding Python startup time).

## 7. Accepted Syntax

Parsing of pGCL programs and expectations is done by the [probably](https://philipp15b.github.io/probably/) library.
There are many examples in the `benchmarks` directory.

An excerpt from the [Lark](https://github.com/lark-parser/lark) grammar for pGCL programs used in the probably library:
```
declaration: "bool" var                  -> bool
            | "nat" var bounds?           -> nat
            | "const" var ":=" expression -> const

bounds: "[" expression "," expression "]"

instruction: "skip"                                      -> skip
           | "while" "(" expression ")" block            -> while
           | "if" "(" expression ")" block "else"? block -> if
           | var ":=" rvalue                             -> assign
           | block "[" expression "]" block              -> choice
           | "tick" "(" expression ")"                   -> tick

rvalue: "unif" "(" expression "," expression ")" -> uniform
      | expression

literal: "true"  -> true
       | "false" -> false
       | INT     -> nat
       | FLOAT   -> float
       | "∞"     -> infinity
       | "\infty" -> infinity
```

Expressions in programs and expectations can be built from the following operators, grouped by precedence:

1. `||`, `&`
2. `<=`, `<`, `=`
3. `+`, `-`
4. `*`, `:`
5. `/`
6. `not `, `( ... )`, `[ ... ]`, `literal`, `var`

Whitespace is generally ignored.

## 8. License

We provide kipro2 under the Apache-2.0 license (see `LICENSE` file).
The [timeout](https://github.com/pshved/timeout) script is included as a git submodule and some modified files of [pysmt](https://github.com/pysmt/pysmt) are included.
Both are licensed under Apache-2.0, as are our derivatives, which are found in `kipro2/pysmt_extensions`.
