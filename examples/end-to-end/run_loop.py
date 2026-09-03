"""One question through the whole loop, on synthetic data.

A question arrives; routing sends it to the causation bucket;
designing-experiments sizes it from a seeded prior store; the experiment
"runs" (simulated with a known true effect); reading-experiments runs the
trust gate and the readout; writing-readouts files the knowledge entry and
appends the effect to the prior store. The store on disk is different at the
end than at the start, which is the loop closing.

Deterministic (seeded), no configuration, no warehouse. Outputs land in
examples/end-to-end/output/.

Run:  python examples/end-to-end/run_loop.py
Open in Jupyter/VS Code: the # %% markers make each stage a cell.
"""

# %% ---------------------------------------------------------------- setup

from pathlib import Path

import numpy as np

from gallop import power, priors, sequential, shrink, trust, variance

OUT = Path(__file__).resolve().parent / "output"
OUT.mkdir(exist_ok=True)
STORE = OUT / "priors.jsonl"
REGISTRY = OUT / "metrics.jsonl"
STORE.unlink(missing_ok=True)
REGISTRY.unlink(missing_ok=True)
rng = np.random.default_rng(11)

RULE = "=" * 74


def stage(title):
    print(f"\n{RULE}\n{title}\n{RULE}")


# %% ----------------------------------------------- the world before the test

stage("0 · The world: a registry with one trusted metric, a store with history")

REGISTRY.write_text(
    '{"name": "activation_rate", '
    '"definition": "users with >=1 core action within 7 days of signup / signups; '
    'excludes internal accounts and bots; UTC days; user counted once", '
    '"source": "warehouse.marts.user_activation", "unit_of_analysis": "user", '
    '"direction": "increase_good", "role": "primary", '
    '"gaming": "widen the qualifying action list, or day-6 nudges inside the window; '
    'guardrail: week-4 retention of activated users", "status": "trusted"}\n')
print(priors.read_registry(REGISTRY, status="trusted")[["name", "status"]].to_string(index=False))

past = [0.0021, -0.0004, 0.0034, 0.0009, -0.0012, 0.0026, 0.0005, 0.0018]
for i, eff in enumerate(past):
    priors.append(STORE, {
        "id": f"2026-{i + 1:02d}-signup-test", "metric": "activation_rate",
        "date": f"2026-{i + 1:02d}-10", "surface": "signup", "design": "experiment",
        "effect": eff, "unit": "pp", "se": 0.0012, "n_per_arm": 30_000,
        "decision": "ship" if eff > 0.0015 else "no-ship",
    })
records_before = len(STORE.read_text().strip().splitlines())
print(f"prior store seeded with {records_before} past readouts")

# %% --------------------------------------------------------------- routing

stage("1 · routing-questions: a question arrives")

print("""Q: "Does the simplified signup form increase activation?"
lookup     no knowledge-repo entry answers it; the store holds a prior
kill rule  the PM ships or reverts the form on the answer: fundable
the gate   activation_rate is trusted in the registry: pass
type       a change question, decided once
assignment we control the flag: route to designing-experiments""")

# %% ---------------------------------------------------------------- design

stage("2 · designing-experiments: size it from the store, not from a wish")

BASELINE, UNITS_PER_DAY = 0.12, 6_000
store_df = priors.read(STORE, metric="activation_rate")
effects = store_df["effect"].to_numpy(float)
biggest = float(np.abs(effects).max())
days = power.duration(biggest, UNITS_PER_DAY, baseline_rate=BASELINE)
n_per_arm = int(UNITS_PER_DAY * days / 2)
print(f"store: {len(effects)} readouts, effects mean {effects.mean() * 100:+.2f}pp, "
      f"|max| {biggest * 100:.2f}pp")
print(f"MDE target = largest effect the metric has produced: {biggest * 100:.2f}pp")
print(f"duration at {UNITS_PER_DAY:,}/day: {days:.0f} days -> n {n_per_arm:,} per arm")
print("plan: unit=user, no interference (single-player surface), exposure event")
print("logged in both arms, PM will peek daily so the design is always-valid,")
print("decision rule: ship if the always-valid interval excludes zero")

# %% ------------------------------------------------- the experiment "runs"

stage("3 · The experiment runs (simulated, true effect +0.30pp)")

TRUE_EFFECT = 0.0030
x = rng.beta(2, 14, 2 * n_per_arm)  # pre-period propensity, for CUPED
arm = np.array(["control"] * n_per_arm + ["treatment"] * n_per_arm)
y = rng.binomial(1, np.clip(x + (arm == "treatment") * TRUE_EFFECT, 0, 1)).astype(float)
assigned = {"control": n_per_arm, "treatment": n_per_arm - int(rng.integers(0, 80))}
exposed = {k: int(v * 0.985) for k, v in assigned.items()}
print(f"{2 * n_per_arm:,} units simulated; true effect {TRUE_EFFECT * 100:+.2f}pp")

# %% --------------------------------------------------------------- reading

stage("4 · reading-experiments: the trust gate, then the number")

s = trust.srm(assigned)
e = trust.exposure_check(assigned, exposed)
print(f"SRM      p {s['p']:.3f}  {s['verdict']}")
print(f"exposure pooled {e['pooled_rate']:.1%}  {e['verdict']}")
assert not s["srm"] and not e["differential"], "trust gate failed; no result exists"

r = variance.cuped(y, x, arm, control="control")
sd_adj = r["se_adjusted"] * np.sqrt(min(r["n_control"], r["n_treatment"]) / 2)
av = sequential.always_valid_ci(0.0, r["effect_adjusted"], sd_adj,
                                min(r["n_control"], r["n_treatment"]), tau2=1e-4)
lo, hi = av["ci"]
print(f"effect   raw {r['effect_raw'] * 100:+.3f}pp -> cuped {r['effect_adjusted'] * 100:+.3f}pp "
      f"(se {r['se_adjusted'] * 100:.3f}pp, variance reduction {r['variance_reduction']:.0%})")
print(f"always-valid 95% CI [{lo * 100:+.3f}pp, {hi * 100:+.3f}pp]  "
      f"significant: {av['significant']}")

sh = shrink.from_store(r["effect_adjusted"], r["se_adjusted"], store_df,
                       "activation_rate", "pp")
print(f"shrunk toward the prior ({sh['n_priors']} readouts): "
      f"{sh['effect_shrunk'] * 100:+.3f}pp (weight on data {sh['weight_on_data']:.2f})")

decision = "ship" if lo > 0 else "no-ship"
print(f"decision rule: ship if the always-valid CI excludes zero  ->  {decision.upper()}")

# %% --------------------------------------------------------------- writing

stage("5 · writing-readouts: the belief, the entry, the store append")

belief = (f"Cutting fields from the signup form is worth about "
          f"{sh['effect_shrunk'] * 100:.1f}pp on activation; held under autumn "
          f"traffic mix; expires if the signup flow is redesigned.")
entry = OUT / "knowledge-entry.md"
entry.write_text(f"""# Does the simplified signup form increase activation?

2026-09 · surface: signup · prior store id: 2026-09-signup-simplify · settled

**Decision unblocked.** {decision} the simplified form (PM call, per the
pre-registered rule).

**Method.** Experimentation: we controlled the flag; user-randomised,
always-valid design because the dashboard was watched daily.

**The number.** {sh['effect_shrunk'] * 100:+.2f}pp shrunk
(raw {r['effect_adjusted'] * 100:+.2f}pp, always-valid CI
[{lo * 100:+.2f}pp, {hi * 100:+.2f}pp], n {n_per_arm:,}/arm).

**The belief.**
> {belief}

**Expires when.** The signup flow is redesigned.

**What we would do differently.** Log the pre-period covariate at a finer
grain; rho was modest and most of the CUPED benefit went unclaimed.

**Cost.** {days:.0f} days of the signup surface.
""")
print(f"knowledge entry written: {entry.relative_to(OUT.parent)}")

priors.append(STORE, {
    "id": "2026-09-signup-simplify", "metric": "activation_rate",
    "date": "2026-09-03", "surface": "signup", "design": "experiment",
    "effect": round(sh["effect_shrunk"], 6), "unit": "pp",
    "se": round(r["se_adjusted"], 6), "n_per_arm": n_per_arm,
    "decision": decision, "conditions": "autumn traffic mix, pre-redesign flow",
    "expires_on": "signup flow redesign",
})
records_after = len(STORE.read_text().strip().splitlines())
print(f"prior store: {records_before} records -> {records_after}")
assert records_after == records_before + 1

stage("The loop is closed")
print("The store the next question reads is not the store this one read.")
print(f"True effect was {TRUE_EFFECT * 100:+.2f}pp; the store now carries "
      f"{sh['effect_shrunk'] * 100:+.2f}pp,")
print("shrunk, with its se, so the next test on this surface starts smaller.")
