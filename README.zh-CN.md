# rk-bench

**在 RK3588 上到底该选哪个模型？实际能跑多快？**

rk-bench 是公开 RKNN 模型在 Rockchip 板卡上的实测跑分榜。所有数字都在真机上
按同一套冻结协议测出，工具零依赖、可自行复跑：不抄厂商表格、不用墙钟计时、
不猜数。延迟取自 NPU 运行时自身的 PERF_RUN 硬件计数；每个模型同时给出
CPU 回退判定——「跑得快」但一半算子偷偷在 CPU 上跑的模型，在这里藏不住。

```sh
PYTHONPATH=src python3 -m rkbench run yolov8n.rknn --name YOLOv8n --task detect \
  --soc rk3588 --json report.json
```

## 测量口径

- 板卡：RK3588（Ubuntu 22.04 / 内核 6.1.118），rknpu 驱动 0.9.8，librknnrt 2.3.2。
  板子常态负载约 16——正因如此才用硬件计数而非墙钟。
- 协议：预热 10 次 + 正式 50 次，按模型自身输入形状造零输入，默认 NPU 核分配。
- CPU 回退：解析 PERF_DETAIL 逐层账；Input/Output 结构性算子不算回退。
  回退占比 <1% 且无单算子 ≥100µs → `NPU_ONLY`；1%–20% → `MIXED`；
  >20% → `CPU_HEAVY`；测不了 → `UNKNOWN`。阈值与姊妹项目 RK Edge Doctor 一致：
  它管单个模型的深度诊断，rk-bench 管横向选型榜单；今后模型健康数据以本仓为唯一真源。
- 内存：模型文件大小；进程 RSS 增量（加载+跑一次，3 个独立进程取中位）；
  PERF_DETAIL 逐层 RW 合计（每帧）。
- 隐私：报告只记模型文件名与 SHA-256，绝不记路径与板卡序列号。

## 用法

```sh
PYTHONPATH=src python3 -m rkbench run model.rknn --name YOLOv8n --task detect --soc rk3588 --json report.json
PYTHONPATH=src python3 -m rkbench add report.json --into data/leaderboard.json
PYTHONPATH=src python3 -m rkbench table --from data/leaderboard.json --out docs/LEADERBOARD.md --readme README.md
```

`add` 会校验 SoC / runtime / 驱动与榜单环境一致，不一致拒绝入榜——榜单永不混排。

## 投稿入榜

在你的板子上跑 `rkbench run`，把 JSON 报告贴到 bench-report issue 即可申请入榜；
新板卡开新分榜。详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

不做：精度/mAP 评测、功耗测量、模型转换、任何非公开模型。
