# v0.4.0 model provenance

Four models were converted on an x86_64 VM from official
[RKNN Model Zoo](https://github.com/airockchip/rknn_model_zoo) downloads
checked on 2026-11-06. DeepLabV3 FP was skipped as described below.
All four conversions succeeded on their first attempt.

The conversion environment remained fixed: rknn-toolkit2 2.3.2,
torch 2.3.1+cpu, onnx 1.17.0, onnxruntime 1.19.2, and setuptools 80.9.0.
The target was RK3588. No source graphs were edited.

## Official recipes

- **YOLOv8n-seg FP:** the nano ONNX download is listed in the
  [segmentation README](https://github.com/airockchip/rknn_model_zoo/blob/main/examples/yolov8_seg/README.md);
  the download script defaults to the small variant. The shared
  [conversion recipe](https://github.com/airockchip/rknn_model_zoo/blob/main/examples/yolov8_seg/python/convert.py)
  uses mean `[0,0,0]`, std `[255,255,255]`; quantization was disabled.
- **PP-YOLOE-s FP:** official
  [download](https://github.com/airockchip/rknn_model_zoo/blob/main/examples/ppyoloe/model/download_model.sh)
  and [recipe](https://github.com/airockchip/rknn_model_zoo/blob/main/examples/ppyoloe/python/convert.py),
  with the same mean/std and quantization disabled.
- **YOLOv8s-seg INT8:** official
  [download](https://github.com/airockchip/rknn_model_zoo/blob/main/examples/yolov8_seg/model/download_model.sh)
  and the shared segmentation recipe above, with quantization enabled.
- **YOLOv8n-pose INT8:** official
  [download](https://github.com/airockchip/rknn_model_zoo/blob/main/examples/yolov8_pose/model/download_model.sh)
  and [two-step hybrid recipe](https://github.com/airockchip/rknn_model_zoo/blob/main/examples/yolov8_pose/python/convert.py).
  The Zoo recipe retains FP16 ranges inside the INT8 model. The three
  `custom_hybrid` ranges start at
  `/model.22/cv4.0/cv4.0.0/act/Mul_output_0`,
  `/model.22/cv4.1/cv4.1.0/act/Mul_output_0`, and
  `/model.22/cv4.2/cv4.2.0/act/Mul_output_0`, and all end at
  `/model.22/Concat_6_output_0`. Both hybrid stages were used, with
  `proposal=False`; the model is not entirely INT8.

Both INT8 models use mean `[0,0,0]`, std `[255,255,255]`, and the Zoo's
[20-image COCO calibration list](https://github.com/airockchip/rknn_model_zoo/blob/main/datasets/COCO/coco_subset_20.txt).
Local calibration filenames and order were checked against that list.
No accuracy evaluation is claimed.

## Source and artifact hashes

All ONNX files came directly from the official examples' filez links and
passed the ONNX checker. They were not cross-checked against board copies.
RKNN files were given clean public filenames before transfer and benchmarking.
Their hashes were checked on the board and against the returned reports.

| ONNX source | SHA-256 |
| --- | --- |
| `yolov8n-seg.onnx` | `1818ae7f4899c559f66e66f1d987a2cd516c3ceed2db8718dc77d647edb29d73` |
| `ppyoloe_s.onnx` | `af72d05b33723f6d18f9784f6bba8e593a5554f465f1800d7ad1ba1e33e38b8a` |
| `yolov8n-pose.onnx` | `308495ebe4416b40adf376485252a7b8ba7933a169368b31e74e0f977ded8663` |
| `yolov8s-seg.onnx` | `bc55660d348db236a7e796892a91aa47939a1222bb4bfb92a0bf7a265ff9ddfb` |

| RKNN artifact | SHA-256 |
| --- | --- |
| `yolov8n-seg_rk3588_fp.rknn` | `8da41b4e72a556d0a0a0497b5d49f7e492519e9623a03c3babe49cc98cdaa37d` |
| `ppyoloe_s_rk3588_fp.rknn` | `2ee9a68d9ae0807ed76e0238345bc4f363c5834611fe45702c8a04861e6f2bc2` |
| `yolov8n-pose_rk3588_int8.rknn` | `e644c5d06b3875ee055b5c18a59626c15d1467f2adba48c0742814aac9b7a253` |
| `yolov8s-seg_rk3588_int8.rknn` | `f0af5adfd87e62b7dac6db891a9f9e71587846f9f25d4a94e22940452726d2bc` |

## Skipped target

**DeepLabV3 FP:** the official
[download script](https://github.com/airockchip/rknn_model_zoo/blob/main/examples/deeplabv3/model/download_model.sh)
provides `deeplab-v3-plus-mobilenet-v2.pb`, and its
[converter](https://github.com/airockchip/rknn_model_zoo/blob/main/examples/deeplabv3/python/convert.py)
uses `load_tensorflow`. It does not provide an ONNX download/conversion
recipe for this task's fixed ONNX workflow. No conversion or benchmark was
attempted, and no substitute model or export recipe was used.

## Measurement

The existing protocol is unchanged: one sacrificial priming process, then
three independent sessions, each with ten warmup and fifty measured runs.
Published latency is the median across sessions; the verdict is the worst
session's. Core assignment remains the runtime default.

Reports were imported with `rkbench add` after SoC/runtime/driver validation.
The [leaderboard](LEADERBOARD.md) is generated from
[data/leaderboard.json](../data/leaderboard.json); existing entries were retained.

The local handoff retains conversion scripts, recipe snapshots, full logs,
SHA-256 manifests, and conversion notes in `work/`, with the four returned
report JSON files in `work/reports_rk3588/`. Model binaries are not committed.
