Synthetic demonstration: cross-site cell-state classification

This manuscript is fictitious software-test material, not a scientific study or publication.

# Abstract

Cross-site differences complicate cell-state classification. We evaluated a calibration procedure using synthetic paired observations from 40 donors distributed across 4 sites. The held-out-site macro-F1 was 0.72 for the uncalibrated model and 0.78 for the calibrated model. Performance remained below the within-site macro-F1 of 0.85. These synthetic findings suggest that calibration can reduce some site effects, although independent biological validation is required.

# I. Introduction

Reliable cell-state classification requires models that remain useful outside their training environment. Differences in sample handling and instrumentation can alter measured expression even when biological labels are unchanged. A classifier may consequently identify site-specific measurement patterns rather than the intended biological states [1].

Our goal was to evaluate whether calibration reduced this discrepancy in a controlled synthetic setting. We compared calibrated and uncalibrated classifiers using site-level holdout evaluation and examined the remaining performance gap. The observations below are simulated and cannot establish clinical or biological utility.

# II. Related work

Domain adaptation methods attempt to reduce differences between training and deployment distributions. Previous methodological descriptions motivate evaluating adaptation with grouped rather than randomly mixed observations [1]. However, apparent improvements under random splits do not establish performance at unseen sites. Here we therefore emphasize site-level separation and do not claim novelty of the calibration algorithm.

# III. Methods

We generated synthetic paired observations for 40 donors, with 10 donors assigned to each of 4 sites. Each donor contributed 100 observations with predefined state labels. Site offsets were introduced before calibration. No patient data were used. The calibration procedure centered each feature using estimates obtained from the training sites only.

The classifier was fit without access to labels from the held-out site. We repeated the evaluation with each site excluded in turn, keeping all observations from a donor in the same partition. Model selection was performed using a training-site validation partition. We report the mean macro-F1 across held-out sites and a separate within-site evaluation. We did not estimate uncertainty intervals or perform statistical significance testing.

# IV. Results

The mean held-out-site macro-F1 increased from 0.72 without calibration to 0.78 with calibration. The corresponding within-site macro-F1 was 0.85. The calibrated classifier therefore retained a performance gap when evaluated at previously unseen sites.

Calibration reduced the synthetic offset in the feature distributions. However, improvement was uneven across the predefined cell states. Rare states continued to show lower recall than common states. We did not assess whether the calibration procedure preserved disease-related expression changes.

# V. Discussion

The synthetic comparison supports a limited conclusion: reducing site offsets can improve classification in this controlled simulation. It does not demonstrate that the same procedure will transfer to biological cohorts. Calibration may remove meaningful signals when technical and biological variation are confounded, which was not tested here.

The evaluation also illustrates why grouped holdout design matters. Within-site performance exceeded performance on unseen sites even after calibration. Additional validation should examine independent datasets, uncertainty estimates and preservation of biological contrasts before deployment. The current experiment cannot support clinical recommendations.

# VI. Conclusion

Calibration improved classification across synthetic sites while leaving a residual generalization gap. These findings motivate biological validation of the approach and caution against interpreting within-site accuracy as evidence of robust deployment performance.

# References

[1] Example, A. Synthetic reference used for software testing. This placeholder is not a real bibliographic record.

# Data Availability

This is synthetic software-test text. No real study dataset exists.

# Code Availability

The demonstration is included in the JournalPort software test examples.
