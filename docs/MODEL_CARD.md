# Model card

Purpose: choose a human-annotation batch from user-supplied vectors. Algorithm: standardized 3-nearest-neighbor vote entropy with greedy diversity. Learned state: seed feature means/scales and the labeled exemplars. No pretrained model or generative AI is used.

Intended users: engineers exploring small active-learning workflows. Non-goals: ticket routing, numeric drift detection, automated labeling, high-stakes decisions, representative sampling, or calibrated probabilities.

Evaluation: thirteen software regression tests and an original six-seed/eight-candidate shape fixture. The fixture has no hidden oracle labels and cannot support a learning-curve or accuracy claim. No production benchmark has been run. Before operational adoption, compare multiple randomized seed splits and budgets against random sampling on a legally sourced dataset with a locked holdout; inspect per-class results and annotation disagreement.

Limitations: k is fixed to three; poor features and seed bias propagate into selection. Add-one smoothing reduces extreme vote scores but does not calibrate them. Distant outliers can be confidently mischaracterized, or disproportionately selected by diversity. Pool labels must remain unknown to the algorithm; manually applying predicted scores as labels would invalidate the human-labeling workflow. No fairness assessment or annotation-cost model is included.
