# Validation cohort inventories

This directory contains lightweight manifests and source registries for
external validation. It does not contain a locked benchmark or hidden scoring
labels.

`source_registry_v1.json` records product-specific wavelength, frame, LSF,
reader and reference-quality prerequisites before targets are selected or
downloaded. Its `instrument_gate_status` fields deliberately fail closed:
ingestion or catalogue availability alone does not make a product eligible for
the main atmospheric-parameter accuracy statistics.

Future cohort manifests must group all aliases, releases, visits and
cross-instrument observations of one star under one `target_id`. A star already
used for method development cannot enter a later holdout through a different
file or catalogue alias. Numerical holdout labels should live in a separate
scoring input and must not appear in routine fitting or blinded-review output.
