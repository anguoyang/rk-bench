---
name: Bug report
about: rkbench measured wrong, crashed, or misjudged a model
labels: bug
---

**Attach your bench report first** — most diagnosis is impossible without it:

```sh
PYTHONPATH=src python3 -m rkbench run model.rknn --name "Model" --task detect --soc rk3588 --json report.json
```

- Board / SoC:
- OS / kernel:
- librknnrt version (in the report JSON):
- rkbench version (`rkbench --version`):

**What happened**

**What you expected**

**Relevant output (paste the lines)**
