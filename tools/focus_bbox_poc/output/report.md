# RT-DETR car POC (offline)

- Model: `PekingU/rtdetr_r18vd_coco_o365` (Apache-2.0)
- Processed: **18** reachable car photos (manifest 34)

## Verdicts (auto rules)

| Verdict | Count | Share |
|---------|------:|------:|
| ✅ correct | 13 | 72% |
| ⚠️ miss | 5 | 28% |
| ❌ wrong | 0 | 0% |

- Mean latency: **603 ms**/photo

## Overlays

See `tools/focus_bbox_poc/output/overlays/` — green = primary vehicle bbox.

## Per image

- listing **39** `397b7426-0e0a-4014-81cd-ec487fcaeabb.jpg` → **correct** (car conf=0.97 area=28%) — `tools\focus_bbox_poc\output\overlays\39_397b7426-0e0a-4014-81cd-ec487fcaeabb.jpg`
- listing **38** `60e6038a-053f-43a8-96c2-f02101271713.jpg` → **correct** (car conf=0.96 area=44%) — `tools\focus_bbox_poc\output\overlays\38_60e6038a-053f-43a8-96c2-f02101271713.jpg`
- listing **37** `d88cce19-b0f3-48a7-a42c-450f42177c59.jpg` → **miss** (нет vehicle; top=person) — `tools\focus_bbox_poc\output\overlays\37_d88cce19-b0f3-48a7-a42c-450f42177c59.jpg`
- listing **36** `636e3bdf-5408-4ff4-967d-81d588827b04.jpg` → **miss** (нет vehicle; top=person) — `tools\focus_bbox_poc\output\overlays\36_636e3bdf-5408-4ff4-967d-81d588827b04.jpg`
- listing **29** `6624e7a7-a98b-4833-9c26-c5464da7fe15.jpg` → **miss** (нет vehicle; top=person) — `tools\focus_bbox_poc\output\overlays\29_6624e7a7-a98b-4833-9c26-c5464da7fe15.jpg`
- listing **28** `7b094cfe-7f5c-45e1-a1d2-91b62f2a878f.jpg` → **miss** (нет vehicle; top=person) — `tools\focus_bbox_poc\output\overlays\28_7b094cfe-7f5c-45e1-a1d2-91b62f2a878f.jpg`
- listing **26** `5d4d1448-88c3-4f7e-8713-a7130760af74.jpg` → **correct** (car conf=0.97 area=39%) — `tools\focus_bbox_poc\output\overlays\26_5d4d1448-88c3-4f7e-8713-a7130760af74.jpg`
- listing **35** `71c05d58-7045-4968-a868-ee3a06e00fe1.jpg` → **correct** (car conf=0.96 area=44%) — `tools\focus_bbox_poc\output\overlays\35_71c05d58-7045-4968-a868-ee3a06e00fe1.jpg`
- listing **34** `506dbdc7-f45b-40ba-bd40-5dda832f39fe.jpg` → **correct** (car conf=0.97 area=28%) — `tools\focus_bbox_poc\output\overlays\34_506dbdc7-f45b-40ba-bd40-5dda832f39fe.jpg`
- listing **33** `812d21cd-3cdc-4873-a95e-16ac02a60863.jpg` → **correct** (car conf=0.97 area=28%) — `tools\focus_bbox_poc\output\overlays\33_812d21cd-3cdc-4873-a95e-16ac02a60863.jpg`
- listing **32** `77045449-1eaf-473d-a98c-9f04259864cd.jpg` → **correct** (car conf=0.97 area=28%) — `tools\focus_bbox_poc\output\overlays\32_77045449-1eaf-473d-a98c-9f04259864cd.jpg`
- listing **31** `d4751be6-fbd1-40c1-8571-8f0999f61c2d.jpg` → **correct** (car conf=0.97 area=28%) — `tools\focus_bbox_poc\output\overlays\31_d4751be6-fbd1-40c1-8571-8f0999f61c2d.jpg`
- listing **30** `569ea9ba-6e10-4261-a35f-31c05e2bbb23.jpg` → **correct** (car conf=0.96 area=44%) — `tools\focus_bbox_poc\output\overlays\30_569ea9ba-6e10-4261-a35f-31c05e2bbb23.jpg`
- listing **30** `c2304556-8a7e-4f74-a8ac-93fc77b6e77c.jpg` → **correct** (car conf=0.96 area=44%) — `tools\focus_bbox_poc\output\overlays\30_c2304556-8a7e-4f74-a8ac-93fc77b6e77c.jpg`
- listing **27** `ed7cb0fa-991c-4142-85c6-68ad3a13547c.jpg` → **correct** (car conf=0.97 area=28%) — `tools\focus_bbox_poc\output\overlays\27_ed7cb0fa-991c-4142-85c6-68ad3a13547c.jpg`
- listing **25** `db3273bf-9d1e-466a-a2c9-4a04cc162260.jpg` → **correct** (car conf=0.96 area=44%) — `tools\focus_bbox_poc\output\overlays\25_db3273bf-9d1e-466a-a2c9-4a04cc162260.jpg`
- listing **24** `9f3bf53a-ee3d-488c-b316-674e586b669b.jpg` → **miss** (нет vehicle; top=person) — `tools\focus_bbox_poc\output\overlays\24_9f3bf53a-ee3d-488c-b316-674e586b669b.jpg`
- listing **23** `2a49837b-39b1-482f-bb59-f60cd325575e.jpg` → **correct** (car conf=0.97 area=9%) — `tools\focus_bbox_poc\output\overlays\23_2a49837b-39b1-482f-bb59-f60cd325575e.jpg`