# XSL DR2 matched separate-arm sample

This directory contains the UVB, VIS, and NIR spectra for three XSL DR2 stars
that are also present as merged XSL DR3 products in the parent data directory:

- X0379 / HD 119802 / K3V;
- X0646 / HD 175058 / A5IV;
- X0900 / HD 110885 / F3V (reference parameters require additional review).

The files are unmodified public ESO Phase-3 products. They were selected by
querying the ESO `ivoa.ObsCore` collection `XSL`, downloaded through the
corresponding DataLink `#this` URLs, and checked against both the FITS headers
and the SHA-256 values in `xsl_dr2_checksums.sha256`. `manifest.json` records
the stable ESO archive identifier for every arm.

Each FITS binary table contains `WAVE` in nm and `FLUX`/`ERR` in
erg cm^-2 s^-1 Angstrom^-1. The wavelengths are in air and each arm has been
placed separately in the stellar rest frame. All selected files have
`LOSS_COR=true` and `REST_COR=true`.

These products must remain separate-arm data. Do not automatically stitch,
renormalize, or force them onto a common radial-velocity correction. In
particular, `REST_VAL` differs substantially between some arms (by 17.35 km/s
between X0379 UVB and VIS), which is precisely one of the systematics this
sample is intended to expose. Use the `WMIN_*` and quality keywords from each
header and apply explicit dichroic, telluric, and edge masks.

Spyctres does not yet register a product-specific XSL DR2 reader. That reader
should preserve the per-arm `SPEC_RES`, `LOSS_COR`, `REST_VAL`, `BARY_COR`,
`SNR`, `WMIN_*`, and quality flags rather than passing these files through a
generic X-SHOOTER profile. Until it is implemented, use Astropy for inspection
and do not use these spectra in a production fit through an inferred reader.

Verify the local copies with:

```bash
cd examples/data/xsl_dr2
sha256sum -c xsl_dr2_checksums.sha256
```

Please cite Gonneau et al. (2020) and acknowledge the ESO Science Archive when
using these files. See the entries in the repository-level `references.json`.
