# Two More Examples for kipro2

Here we present two more examples for kipro2 in addition to the ones presented in [README.md](README.md).
The examples below are for the expected runtime transformer `ert`.

## Example: Verifying Runtime Upper Bounds

This is from `benchmarks/one_loop_examples/ber.imp.pgcl`, an adaptation of the `ber` example from [Bounded Expectations: Resource Analysis for Probabilistic Programs](https://dl.acm.org/doi/abs/10.1145/3192366.3192394) by Ngo et al.
```
// ARGS: --ert --post 0 --pre "2*(n-x)" --assert-inductive 1
nat x;
nat n;
nat r;
while (x < n) {
    r := 1 : 1/2 + 0 : 1/2;
    x := x + r;
    tick(1);
}
```

You can verify inductiveness of the pre-expectation bound `2*(n-x)` for the _probabilistic expected runtime transformer_ `ert` for the post-expectation `0` by running
```
poetry run kipro2 benchmarks/one_loop_examples/ber.imp.pgcl
```
The output contains "Property is 1-inductive". Success!

The first three actual code lines declare natural number variables `x`, `n`, `r`.
While `x < n`, the loop continues to choose `r` from a Binomial distribution (1 or 0 each with probability ½).
We then add `r` to `x`.
`tick(1)` increments the runtime counter, so we count each loop execution as taking one step.
<small>(`tick` statements are ignored when not in `--ert` mode.)</small>

So what we ask kipro2 is: Prove (using k-induction) or refute (using bounded model checking) that `ert[program](0) <= 2*(n-x)`.
You can read it as: If there's zero steps after the program (post-expectation), is it sufficient to have `2*(n-x)` steps left at the start of the program?
The question is one over _all initial states_ with arbitrary values for the variables.
This property is 1-inductive, so the answer is yes!

## Example: Refutation of Runtime Upper Bounds

Example 1 of our paper _"Latticed k-Induction with an Application to Probabilistic Programs"_ is a simplified version of the _Bounded Retransmission Protocol_ (BRP):

```
// ARGS: --post "totalFailed" --pre "totalFailed + 1" --checker both

nat toSend;     # The number of total packages to send
nat sent;       # Number of packages sent
nat maxFailed;  # The maximal number of retransmission tries
nat failed;     # The number of failed retransmission tries
while ( sent < toSend && fail < maxFail) {
    { fail := 0 ; sent := sent + 1 } [ 0.9 ] { fail := fail + 1 ; totalFail := totalFail + 1 }
}
```
The program models a simplified version of the bounded retransmission protocol, which attempts to transmit `toSend` packages via an unreliable channel (that fails with probability `0.1`) allowing for at most `maxFail` retransmissions per package.

kipro2 refutes the property in the comment (`wp[brp5](totalFailed) <= totalFailed + 1`) after about 15 seconds with `k = 13`.
Just run `poetry run kipro2 benchmarks/cav21/brp5.pgcl`.

The output might be a bit ugly since it is the result of running both the bouded model checking engine and the induction engine in parallel (`--checker both`).
We can run the tool again, but now with `--checker bmc` to only run the bounded model checker:
```
poetry run kipro2 benchmarks/cav21/brp5.pgcl --checker bmc
```
There's even a counter-example for the initial state that violates the property:
```
kipro2: SAT. Model:
maxFailed := 2
totalFailed := 1
failed := 0
sent := 6042
toSend := 6052
```
