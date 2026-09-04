"""Product data science checks, thin by design.

Seven modules, each backing one skill:

  power       MDE, sample size and duration, two-proportion and continuous
  trust       sample ratio mismatch and exposure-versus-eligibility
  variance    CUPED against a pre-period covariate
  sequential  always-valid confidence sequences and group-sequential bounds
  shrink      empirical Bayes shrinkage toward the prior store
  priors      the prior store and the metric registry on disk
  validate    out-of-time validation, lift over the base rate, calibration, Qini, MASE

Every function takes and returns arrays or DataFrames, never a database
connection. Each module runs as a script: python -m gallop.<module> --help
"""

__version__ = "0.2.0"
