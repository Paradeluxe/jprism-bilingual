# Snapshot 2026-11-19 (pre 10-model rebuild)

Taken before adding Qwen3-8B / Qwen3.5-9B to the analysis.

Contents
- manuscript/            main docx, methods docx, results_Nov18.md, methods_Nov18.md
- manuscript/sections/   one md per manuscript section
- figures/               all rendered figures (README + print + results)
- stats/                 experiment/stats_mixed/results/*.csv (all model fits and summaries)
- data/                  experiment/stats_mixed/data/*.csv (item-level analysis inputs)
- raw_manifest.txt       sha256 of every PROBE300 raw json (files stay in experiment/RESULT/PROBE300)
- SHA256SUMS.txt         sha256 of every file in this snapshot

Restore: copy the file back over its original path (paths mirror the repo).
Verify:  Get-FileHash -Algorithm SHA256 <file>  and compare with SHA256SUMS.txt.
