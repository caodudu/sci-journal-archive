# Biomedical And Cross-Biology Subset Filter

Last updated: 2026-06-18

## Current Rule

The biomedical/cross-biology subset is selected from JCR/Web of Science subject categories, not from journal-title keywords.

For the active 2025 dataset, each record has a JCR `Category` value such as:

```text
ONCOLOGY|Q1|1/322
BIOTECHNOLOGY & APPLIED MICROBIOLOGY|Q3|95/174
MEDICINE, GENERAL & INTERNAL|Q1|1/325
```

The filter takes the category name before the first `|`, normalizes it to uppercase, and marks a journal as biomedical when at least one category is in the whitelist below.

The `biomed_reason` field stores the matched category, for example:

```text
category: BIOTECHNOLOGY & APPLIED MICROBIOLOGY
```

Loose keyword fallback is disabled by default. The current scope is intentionally broad: biomedical, life sciences, bioinformatics/computational biology, systems-biology-adjacent categories, biomaterials, and biology-related interdisciplinary categories are included.

## Current 2025 Counts

```text
All 2025 SCIE: 8,841
All 2025 ESCI: 7,736

Biomedical SCIE: 3,990
Biomedical ESCI: 1,908
Biomedical/cross-biology total: rerun `scripts/build_biomed_subset.py` after category edits.
```

## Category Whitelist

```text
ALLERGY
ANATOMY & MORPHOLOGY
ANDROLOGY
ANESTHESIOLOGY
AUDIOLOGY & SPEECH-LANGUAGE PATHOLOGY
BIOCHEMICAL RESEARCH METHODS
BIOCHEMISTRY & MOLECULAR BIOLOGY
BIOLOGY
BIOPHYSICS
BIOTECHNOLOGY & APPLIED MICROBIOLOGY
ECOLOGY
ENTOMOLOGY
CARDIAC & CARDIOVASCULAR SYSTEMS
CELL & TISSUE ENGINEERING
CELL BIOLOGY
CLINICAL NEUROLOGY
CRITICAL CARE MEDICINE
DENTISTRY, ORAL SURGERY & MEDICINE
DERMATOLOGY
DEVELOPMENTAL BIOLOGY
EMERGENCY MEDICINE
ENDOCRINOLOGY & METABOLISM
ENGINEERING, BIOMEDICAL
EVOLUTIONARY BIOLOGY
FISHERIES
FOOD SCIENCE & TECHNOLOGY
MARINE & FRESHWATER BIOLOGY
MATERIALS SCIENCE, BIOMATERIALS
MATHEMATICAL & COMPUTATIONAL BIOLOGY
GASTROENTEROLOGY & HEPATOLOGY
GENETICS & HEREDITY
GERIATRICS & GERONTOLOGY
HEALTH CARE SCIENCES & SERVICES
HEALTH POLICY & SERVICES
HEMATOLOGY
IMMUNOLOGY
INFECTIOUS DISEASES
INTEGRATIVE & COMPLEMENTARY MEDICINE
MEDICAL ETHICS
MEDICAL INFORMATICS
MEDICAL LABORATORY TECHNOLOGY
MEDICINE, GENERAL & INTERNAL
MEDICINE, LEGAL
MEDICINE, RESEARCH & EXPERIMENTAL
MICROBIOLOGY
MULTIDISCIPLINARY SCIENCES
MYCOLOGY
NEUROIMAGING
NEUROSCIENCES
NURSING
NUTRITION & DIETETICS
OBSTETRICS & GYNECOLOGY
ONCOLOGY
OPHTHALMOLOGY
ORTHOPEDICS
OTORHINOLARYNGOLOGY
PARASITOLOGY
PATHOLOGY
PEDIATRICS
PERIPHERAL VASCULAR DISEASE
PHARMACOLOGY & PHARMACY
PHYSIOLOGY
PLANT SCIENCES
PRIMARY HEALTH CARE
PSYCHIATRY
PUBLIC, ENVIRONMENTAL & OCCUPATIONAL HEALTH
RADIOLOGY, NUCLEAR MEDICINE & MEDICAL IMAGING
REHABILITATION
REPRODUCTIVE BIOLOGY
RESPIRATORY SYSTEM
RHEUMATOLOGY
SPORT SCIENCES
SUBSTANCE ABUSE
SURGERY
TOXICOLOGY
TRANSPLANTATION
TROPICAL MEDICINE
UROLOGY & NEPHROLOGY
VETERINARY SCIENCES
VIROLOGY
ZOOLOGY
```

## Code

- Category whitelist: `scripts/common.py`
- Filter implementation: `scripts/build_biomed_subset.py`

## Review Notes

This is still a policy choice. Some adjacent areas may need discussion:

- `AGRONOMY` and agriculture-related categories remain under review.
- Include or exclude `PSYCHOLOGY` categories depending on whether behavioral medicine is in scope.
- Include or exclude `FOOD SCIENCE & TECHNOLOGY` depending on nutrition/public-health scope.
