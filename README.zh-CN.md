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

## 跑分榜 — RK3588

<!-- LEADERBOARD:BEGIN -->
Board: rk3588 (Rockchip RK3588) · runtime 2.3.2 · driver 0.9.8

| 模型 | 任务 | 输入 | 精度 | p50 (ms) | p95 (ms) | FPS (p50) | 判定 | CPU 回退 | RSS Δ (MB) | 模型大小 (MB) |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| MobileNetV2 | classify | 1x224x224x3 | INT8 | 4.14 | 4.65 | 241.3 | MIXED | 1.1% | 16.2 | 3.97 |
| MobileNetV2 | classify | 1x224x224x3 | FP | 8.63 | 8.89 | 115.9 | NPU_ONLY | 0% | 23.9 | 7.31 |
| ResNet50-v2 | classify | 1x224x224x3 | INT8 | 13.54 | 15.26 | 73.8 | MIXED | 0.63% | 60.2 | 25.46 |
| ResNet50-v2 | classify | 1x224x224x3 | FP | 25.4 | 29.34 | 39.4 | NPU_ONLY | 0% | 110.1 | 49.92 |
| YOLOv8n | detect | 1x640x640x3 | INT8 | 19.17 | 19.76 | 52.2 | NPU_ONLY | 0% | 22.8 | 4.13 |
| YOLOv5s ReLU | detect | 1x640x640x3 | INT8 | 20.52 | 22.3 | 48.7 | NPU_ONLY | 0% | 30.8 | 8 |
| YOLO11n | detect | 1x640x640x3 | INT8 | 31.2 | 31.69 | 32.1 | NPU_ONLY | 0% | 22.9 | 4.05 |
| YOLOv8n | detect | 1x640x640x3 | FP | 37.5 | 38.58 | 26.7 | NPU_ONLY | 0% | 47.4 | 7.25 |
| YOLOv5s ReLU | detect | 1x640x640x3 | FP | 37.8 | 38.58 | 26.5 | NPU_ONLY | 0% | 52.8 | 15.56 |
| YOLO11n | detect | 1x640x640x3 | FP | 43.67 | 49.79 | 22.9 | NPU_ONLY | 0% | 46.1 | 6.71 |
| PP-YOLOE-s | detect | 1x640x640x3 | FP | 67.71 | 70.44 | 14.8 | NPU_ONLY | 0% | 91.6 | 17.08 |
| YOLOv10s | detect | 1x640x640x3 | FP | 88.09 | 90.49 | 11.4 | NPU_ONLY | 0% | 78.3 | 15.81 |
| YOLOv8n-obb | detect-obb | 1x640x640x3 | FP | 37.65 | 38.26 | 26.6 | NPU_ONLY | 0% | 44.8 | 7.3 |
| RetinaFace Mobile320 | face-detect | 1x320x320x3 | FP | 6.43 | 6.68 | 155.6 | MIXED | 4.05% | 12.9 | 1.49 |
| PP-OCRv4-Det | ocr-detect | 1x480x480x3 | INT8 | 31.39 | 39.99 | 31.9 | NPU_ONLY | 0% | 54.1 | 2.51 |
| PP-OCRv4-Det | ocr-detect | 1x480x480x3 | FP | 47.86 | 49.99 | 20.9 | NPU_ONLY | 0% | 38 | 3.75 |
| PP-OCRv4-Rec | ocr-recognize | 1x48x320x3 | INT8 | 14.16 | 16.96 | 70.6 | MIXED | 2.61% | 18.2 | 4.18 |
| PP-OCRv4-Rec | ocr-recognize | 1x48x320x3 | FP | 22.68 | 26.45 | 44.1 | MIXED | 2.58% | 23.3 | 6.74 |
| YOLOv8n-pose | pose | 1x640x640x3 | INT8 | 31.64 | 32.71 | 31.6 | NPU_ONLY | 0% | 28.4 | 4.98 |
| YOLOv8n-pose | pose | 1x640x640x3 | FP | 49.73 | 51.27 | 20.1 | NPU_ONLY | 0% | 47.6 | 8.17 |
| YOLOv8s-seg | segment | 1x640x640x3 | INT8 | 43.84 | 45.44 | 22.8 | NPU_ONLY | 0% | 47.1 | 12.69 |
| YOLOv8n-seg | segment | 1x640x640x3 | FP | 46.74 | 57.36 | 21.4 | NPU_ONLY | 0% | 50.7 | 7.92 |
| YOLOv8s-seg | segment | 1x640x640x3 | FP | 104.53 | 113.08 | 9.6 | NPU_ONLY | 0% | 112.1 | 24.46 |
<!-- LEADERBOARD:END -->

完整榜单与测量说明：

[docs/LEADERBOARD.md](docs/LEADERBOARD.md)

唯一数据源（榜单由命令生成，请勿手改数字）：

[data/leaderboard.json](data/leaderboard.json)

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
PYTHONPATH=src python3 -m rkbench table --from data/leaderboard.json \
  --out docs/LEADERBOARD.md --readme README.md --readme-zh README.zh-CN.md
```

`add` 会校验 SoC / runtime / 驱动与榜单环境一致，不一致拒绝入榜——榜单永不混排。

## 投稿入榜

在你的板子上跑 `rkbench run`，把 JSON 报告贴到 bench-report issue 即可申请入榜；
新板卡开新分榜。详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

不做：精度/mAP 评测、功耗测量、模型转换、任何非公开模型。
