"""Product data science checks, thin by design.

Six modules, each backing one skill:

  power       MDE, sample size and duration, two-proportion and continuous
  trust       sample ratio mismatch and exposure-versus-eligibility
  variance    CUPED against a pre-period covariate
  sequential  always-valid confidence sequences and group-sequential bounds
  shrink      empirical Bayes shrinkage toward the prior store
  priors      the prior store and the metric registry on disk

Every function takes and returns arrays or DataFrames, never a database
connection. Each module runs as a script: python -m gallop.<module> --help
"""

__version__ = "0.0.1"
