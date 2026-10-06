Synthetic demonstration: cross-site cell-state classification

This manuscript is fictitious software-test material, not a scientific study or publication.

## Abstract

Differences between sites complicate cell-state classification beyond the training environment. We evaluated calibration using synthetic paired observations from 40 donors distributed across 4 sites. Held-out-site macro-F1 increased from 0.72 without calibration to 0.78 with calibration, but remained below the within-site macro-F1 of 0.85. These synthetic findings suggest that calibration can reduce some site effects while leaving a residual gap in performance at unseen sites. Independent biological validation is required.

## Introduction

Reliable cell-state classification depends on models that remain useful beyond their training environment. Differences in sample handling and instrumentation can change measured expression without changing biological labels. Classifiers may therefore learn site-specific measurement patterns rather than the biological states they are intended to distinguish [1].

Domain adaptation methods seek to reduce differences between training and deployment distributions. Previous methodological descriptions motivate evaluating adaptation using grouped observations rather than randomly mixed observations [1]. Improvements under random splits, however, do not establish performance at unseen sites. We therefore use site-level separation to evaluate calibration, without claiming novelty of the algorithm.

Here, we asked whether calibration could reduce the discrepancy between within-site and unseen-site classification in a controlled synthetic setting. We compared calibrated and uncalibrated classifiers using site-level holdout evaluation and examined the remaining performance gap. Because all observations were simulated, this evaluation cannot establish clinical or biological utility.

## Results

Calibration improved classification at held-out sites: mean macro-F1 increased from 0.72 without calibration to 0.78 with calibration. The corresponding within-site macro-F1 was 0.85, leaving a residual performance gap at previously unseen sites.

Calibration reduced the synthetic offset in feature distributions, but classification improvements varied across the predefined cell states. Rare states continued to have lower recall than common states. Preservation of disease-related expression changes was not assessed.

## Discussion

These findings support a limited conclusion: reducing site offsets can improve classification in a controlled simulation. Whether the procedure transfers to biological cohorts remains unresolved. When technical and biological variation are confounded, calibration may remove meaningful signals; this possibility was not tested here.

The remaining gap between within-site and unseen-site performance illustrates the importance of grouped holdout evaluation. Even after calibration, performance within sites exceeded performance at unseen sites. Before deployment, further validation should examine independent datasets, quantify uncertainty and assess preservation of biological contrasts. The current experiment cannot support clinical recommendations.

Calibration improved classification across synthetic sites but left a residual generalization gap. The findings motivate biological validation and caution against treating within-site accuracy as evidence of robust deployment performance.

## Methods

We generated synthetic paired observations for 40 donors, assigning 10 donors to each of 4 sites. Each donor contributed 100 observations with predefined state labels. We introduced site offsets before calibration; no patient data were used. Calibration centered each feature using estimates obtained only from the training sites.

We fitted the classifier without access to labels from the held-out site and repeated the evaluation with each site excluded in turn. All observations from a donor remained in the same partition. Model selection used a validation partition drawn from the training sites. We report mean macro-F1 across held-out sites and a separate within-site evaluation. We did not estimate uncertainty intervals or test statistical significance.

## References

[1] Example, A. Synthetic reference used for software testing. This placeholder is not a real bibliographic record.

## Data Availability

This is synthetic software-test text. No real study dataset exists.

## Code Availability

The demonstration is included in the JournalPort software test examples.
