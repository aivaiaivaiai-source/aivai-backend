# RT-DETR diverse car benchmark (offline)

- Model: `PekingU/rtdetr_r18vd_coco_o365` (Apache-2.0)
- Processed: **45** photos, all `car_present=true`

## Gate metrics (car present only)

| Verdict | Count | Share |
|---------|------:|------:|
| ✅ correct | 42 | 93.3% |
| ⚠️ miss | 2 | 4.4% |
| ❌ wrong | 1 | 2.2% |

- **Hit rate:** 93.3%
- **Wrong-object rate:** 2.2%
- Mean latency: **454 ms**/photo

## By tag

- **car_close**: correct 18/20, miss 1, wrong 1
- **car_far**: correct 16/17, miss 1, wrong 0
- **dark**: correct 4/4, miss 0, wrong 0
- **edge_crop**: correct 36/39, miss 2, wrong 1
- **horizontal**: correct 28/31, miss 2, wrong 1
- **listing**: correct 5/5, miss 0, wrong 0
- **multi_car**: correct 37/40, miss 2, wrong 1
- **vertical**: correct 14/14, miss 0, wrong 0

## Per image

- `coco_162858` [edge_crop, multi_car, vertical] → **correct** (car conf=0.93 iou=0.90 area=8%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_162858_000000162858.jpg`
- `coco_54967` [car_far, edge_crop, multi_car, vertical] → **correct** (car conf=0.93 iou=0.93 area=1%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_54967_000000054967.jpg`
- `coco_266981` [car_far, edge_crop, multi_car, vertical] → **correct** (car conf=0.36 iou=0.78 area=1%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_266981_000000266981.jpg`
- `coco_93154` [car_far, edge_crop, multi_car, vertical] → **correct** (car conf=0.93 iou=0.90 area=1%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_93154_000000093154.jpg`
- `coco_361142` [edge_crop, multi_car, vertical] → **correct** (car conf=0.96 iou=0.97 area=7%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_361142_000000361142.jpg`
- `coco_521141` [car_far, edge_crop, multi_car, vertical] → **correct** (car conf=0.92 iou=0.93 area=1%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_521141_000000521141.jpg`
- `coco_336232` [car_close, edge_crop, horizontal, multi_car] → **correct** (car conf=0.93 iou=0.88 area=23%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_336232_000000336232.jpg`
- `coco_460147` [car_close, edge_crop, horizontal, multi_car] → **correct** (car conf=0.67 iou=0.93 area=4%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_460147_000000460147.jpg`
- `coco_52412` [car_close, edge_crop, horizontal, multi_car] → **wrong** (wrong vehicle iou=0.00; top non-veh?) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_52412_000000052412.jpg`
- `coco_210273` [car_close, edge_crop, horizontal, multi_car] → **miss** (weak overlap iou=0.16) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_210273_000000210273.jpg`
- `coco_373353` [car_close, edge_crop, horizontal, multi_car] → **correct** (car conf=0.81 iou=0.92 area=3%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_373353_000000373353.jpg`
- `coco_350023` [edge_crop, horizontal, multi_car] → **correct** (car conf=0.74 iou=0.90 area=0%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_350023_000000350023.jpg`
- `coco_400367` [car_far, dark, horizontal, multi_car] → **correct** (car conf=0.94 iou=0.91 area=6%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_400367_000000400367.jpg`
- `coco_121242` [car_far, edge_crop, horizontal, multi_car] → **miss** (weak overlap iou=0.43) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_121242_000000121242.jpg`
- `coco_263594` [car_close, edge_crop, horizontal, multi_car] → **correct** (car conf=0.96 iou=0.95 area=32%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_263594_000000263594.jpg`
- `coco_466156` [car_close, edge_crop, horizontal, multi_car] → **correct** (car conf=0.67 iou=0.89 area=99%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_466156_000000466156.jpg`
- `coco_172330` [car_close, edge_crop, horizontal, multi_car] → **correct** (car conf=0.97 iou=0.98 area=58%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_172330_000000172330.jpg`
- `coco_183246` [car_close, edge_crop, horizontal, multi_car] → **correct** (car conf=0.60 iou=0.79 area=2%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_183246_000000183246.jpg`
- `coco_167122` [car_close, dark, edge_crop, horizontal, multi_car] → **correct** (car conf=0.64 iou=0.79 area=58%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_167122_000000167122.jpg`
- `coco_78823` [car_close, edge_crop, horizontal, multi_car] → **correct** (car conf=0.90 iou=0.97 area=48%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_78823_000000078823.jpg`
- `coco_322864` [car_close, edge_crop, multi_car, vertical] → **correct** (car conf=0.80 iou=0.97 area=35%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_322864_000000322864.jpg`
- `coco_383289` [car_close, edge_crop, horizontal, multi_car] → **correct** (car conf=0.75 iou=0.94 area=35%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_383289_000000383289.jpg`
- `coco_442456` [car_close, edge_crop, horizontal, multi_car] → **correct** (car conf=0.52 iou=0.96 area=33%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_442456_000000442456.jpg`
- `coco_542625` [car_close, edge_crop, horizontal, multi_car] → **correct** (car conf=0.95 iou=0.98 area=29%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_542625_000000542625.jpg`
- `coco_55150` [car_close, edge_crop, horizontal, multi_car] → **correct** (car conf=0.71 iou=0.90 area=32%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_55150_000000055150.jpg`
- `coco_526392` [car_close, edge_crop, horizontal, multi_car] → **correct** (car conf=0.92 iou=0.93 area=28%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_526392_000000526392.jpg`
- `coco_9891` [car_close, edge_crop, horizontal, multi_car] → **correct** (car conf=0.87 iou=0.72 area=20%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_9891_000000009891.jpg`
- `coco_454661` [car_close, dark, edge_crop, horizontal, multi_car] → **correct** (car conf=0.97 iou=0.98 area=25%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_454661_000000454661.jpg`
- `coco_58539` [car_close, edge_crop, horizontal, multi_car] → **correct** (car conf=0.96 iou=0.97 area=23%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_58539_000000058539.jpg`
- `coco_412531` [car_far, dark, edge_crop, horizontal, multi_car] → **correct** (car conf=0.78 iou=0.97 area=6%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_412531_000000412531.jpg`
- `coco_39484` [car_far, edge_crop, horizontal, multi_car] → **correct** (car conf=0.90 iou=0.94 area=6%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_39484_000000039484.jpg`
- `coco_191013` [car_far, edge_crop, multi_car, vertical] → **correct** (car conf=0.94 iou=0.95 area=5%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_191013_000000191013.jpg`
- `coco_192670` [car_far, edge_crop, horizontal, multi_car] → **correct** (car conf=0.61 iou=0.88 area=6%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_192670_000000192670.jpg`
- `coco_165039` [car_far, edge_crop, horizontal, multi_car] → **correct** (car conf=0.93 iou=0.95 area=5%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_165039_000000165039.jpg`
- `coco_499181` [car_far, edge_crop, horizontal, multi_car] → **correct** (car conf=0.94 iou=0.94 area=5%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_499181_000000499181.jpg`
- `coco_553511` [car_far, edge_crop, horizontal, multi_car] → **correct** (car conf=0.93 iou=0.95 area=5%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_553511_000000553511.jpg`
- `coco_301376` [car_far, edge_crop, multi_car, vertical] → **correct** (car conf=0.89 iou=0.92 area=5%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_301376_000000301376.jpg`
- `coco_67616` [car_far, edge_crop, horizontal, multi_car] → **correct** (car conf=0.91 iou=0.97 area=5%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_67616_000000067616.jpg`
- `coco_504415` [car_far, edge_crop, horizontal, multi_car] → **correct** (car conf=0.95 iou=0.88 area=5%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_504415_000000504415.jpg`
- `coco_424162` [car_far, edge_crop, horizontal, multi_car] → **correct** (car conf=0.92 iou=0.93 area=5%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\coco_424162_000000424162.jpg`
- `listing_39_397b7426-0e0a-4014-81cd-ec487fcaeabb.jpg` [listing, vertical] → **correct** (car conf=0.97 area=28%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\listing_39_397b7426-0e0a-4014-81cd-ec487fcaeabb.jpg_listing_397b7426-0e0a-4014-81cd-ec487fcaeabb.jpg`
- `listing_38_60e6038a-053f-43a8-96c2-f02101271713.jpg` [listing, vertical] → **correct** (car conf=0.96 area=44%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\listing_38_60e6038a-053f-43a8-96c2-f02101271713.jpg_listing_60e6038a-053f-43a8-96c2-f02101271713.jpg`
- `listing_26_5d4d1448-88c3-4f7e-8713-a7130760af74.jpg` [listing, vertical] → **correct** (car conf=0.97 area=39%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\listing_26_5d4d1448-88c3-4f7e-8713-a7130760af74.jpg_listing_5d4d1448-88c3-4f7e-8713-a7130760af74.jpg`
- `listing_30_569ea9ba-6e10-4261-a35f-31c05e2bbb23.jpg` [listing, vertical] → **correct** (car conf=0.96 area=44%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\listing_30_569ea9ba-6e10-4261-a35f-31c05e2bbb23.jpg_listing_569ea9ba-6e10-4261-a35f-31c05e2bbb23.jpg`
- `listing_27_ed7cb0fa-991c-4142-85c6-68ad3a13547c.jpg` [listing, vertical] → **correct** (car conf=0.97 area=28%) — `tools\focus_bbox_poc\output\diverse_benchmark\overlays\listing_27_ed7cb0fa-991c-4142-85c6-68ad3a13547c.jpg_listing_ed7cb0fa-991c-4142-85c6-68ad3a13547c.jpg`