---
name: Bench report
about: Submit a measured model (or a new board) for the leaderboard
labels: bench-report
---

Thanks for contributing a measurement — measured reports are how this
leaderboard grows.

- Model (public models only — please name the source):
- Task:
- Board / SoC:
- OS / kernel:
- librknnrt / driver versions:

Attach `report.json` produced by:

```sh
PYTHONPATH=src python3 -m rkbench run model.rknn --name "Model" --task detect --soc rk3588 --json report.json
```

Reports contain the model file name and SHA-256, board model string, OS and
kernel versions only — no paths, serial numbers, MACs or IPs. A report whose
SoC / runtime / driver differs from an existing board table starts a new
board table rather than mixing into it.
