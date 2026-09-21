# BioFlow Scientific Recommendation Benchmark v1

This package adds a curated regression benchmark without changing BioFlow runtime code.

## Run

From the BioFlow project root with the virtual environment activated:

```powershell
python .\tests\benchmark_v1\run_benchmark.py
```

The runner validates 17 representative scenarios spanning bacterial WGS, AMR, MAG reconstruction, metagenomic viral analysis, virome host prediction and vOTU clustering, amplicon ASV/taxonomy/differential abundance, bulk RNA-seq, eukaryotic genome analysis, metatranscriptomics, and broad metagenomic taxonomy.

It also performs global registry/operation/tool-I/O consistency checks and reruns known BioFlow validators when they are present.

Outputs are written to `tests/benchmark_v1/results/` as Markdown, CSV, and JSON.

Important: v1 is a curated internal scientific-content benchmark. For a manuscript, the next validation layer should use external expert annotation and/or literature-derived blinded cases rather than claiming this panel is an independent gold standard.
