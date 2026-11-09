## Random Sampling Method

`TRUNCATED_EMPIRICAL_RESAMPLING`: uniformly sample supported empirical rows WITH REPLACEMENT, preserving duplicate-value frequencies; caller-owned seeded NumPy Generator. Use the existing global positive pool; no time-group conditioning was selected for transformed V1. Same ordered pool/seed produces identical samples. Runtime receives positive epsilon; it does not abs() signed samples or fit a Gaussian. No extra floor alters sampled values.

Empirical sampling preserves skew, tails within support, repeated empirical mass and any multimodality without imposing an unsupported family. Absolute transformation folds signed mass and changes shape; older signed Record-029 empirical-versus-truncated-Normal comparisons do not transfer unchanged, and are not used as direct V1 model-selection evidence. No parametric fit is performed.

