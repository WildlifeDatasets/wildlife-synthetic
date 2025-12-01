# Data and labels

This page describes what the WildLife Synthetic pipeline produces for each frame and how these outputs map to the three main downstream tasks:

- individual identification (re-identification),
- pose estimation,
- instance segmentation.

The goal is to make it clear **what is stored for each image** and how the same underlying data can be reused across tasks.

---

## 1. Real vs synthetic data

The pipeline can generate **synthetic** images directly in Unity and can also be used to align annotations with **real** camera-trap images (for example, in the CzechLynx dataset).

In practice, you will see two main sources:

- **Real images**
  - Captured by camera traps in the field.
  - Annotated manually (identities, masks, pose on a subset).

- **Synthetic images**
  - Rendered from Unity using the 3D model and environments.
  - Annotated automatically with keypoints, identity labels, and (optionally) masks.

The metadata format is shared so that downstream code can handle both real and synthetic samples in a unified way. A field such as `source` or `is_synthetic` can be used to distinguish them.

---

## 2. Common image-level fields

Every image in the metadata file has a set of **image-level attributes**.  
The exact field names can vary between projects, but conceptually you can expect:

- `image_id` — unique identifier for the image.
- `file_name` — relative path to the image file, e.g. `images/scene0/scene0_000123.jpg`.
- `width`, `height` — image resolution in pixels.
- `scene_id` — identifier of the Unity scene (for synthetic) or camera-trap site (for real).
- `timestamp` — simulated or real capture time, if available.
- `source` — e.g. `real` or `synthetic`.

In addition, the shared metadata file encodes, for each downstream task, whether the record is used and in which split (train, validation, test).  
This allows the same underlying data package to be filtered into task-specific subsets without maintaining separate annotation files for each task.

---

## 3. Pose annotations

For pose estimation, each image can include **2D keypoint annotations** for each visible individual.

### 3.1 Keypoint layout

A fixed keypoint layout is used, typically:

- head, neck, spine points,
- shoulders, elbows, wrists (front legs),
- hips, knees, ankles (hind legs),
- tail base and additional tail points.

For CzechLynx, a 20-keypoint layout is used, but the exact list can be adapted for other species.  
Keypoints are defined in 3D on the rig and projected into image coordinates in Unity.

### 3.2 Storage format

Keypoints are usually stored in a COCO-compatible format.  
Conceptually, each annotation entry includes:

- `image_id` — link to the image,
- `category_id` — class label (e.g., `1` for lynx),
- `keypoints` — flattened list `[x1, y1, v1, x2, y2, v2, ...]`,
- `num_keypoints` — number of visible keypoints,
- optionally `id` and `bbox`.

The visibility flag `v` typically follows the COCO convention:

- `0` – not labeled (or not in image),
- `1` – labeled but not visible (occluded),
- `2` – labeled and visible.

A simplified example:

```json
{
  "image_id": 123,
  "category_id": 1,
  "keypoints": [320, 180, 2, 340, 190, 2, 360, 200, 1, ...],
  "num_keypoints": 20
}
```

For real images, only a subset is annotated with pose due to the manual effort.  
For synthetic images, keypoints can be exported for every frame.

---

## 4. Identity labels (re-identification)

For individual identification, each image that is suitable for re-ID includes an **identity label**.

At minimum, the following information is stored:

- `individual_id` — unique identifier for the individual.
- `identity_source` — whether the identity comes from:
  - expert-based matching (real images), or
  - texture assignment (synthetic images).
- `side` or `viewpoint` (optional) — e.g., left side, right side, frontal.

In the synthetic case, `individual_id` is derived from the **texture** applied to the 3D model.  
A single 3D mesh with different textures represents different individuals; the pipeline keeps track of which texture was active when each frame was captured.

For real images, `individual_id` is derived from expert-based manual identification using flank, leg, or back patterns, and only images with clearly visible patterns are included in the re-ID subset.

---

## 5. Segmentation masks

For instance segmentation, the dataset can provide **pixel-wise masks** of the animal’s body.

There are two main storage options:

1. **Separate mask images**  
   - Stored in a parallel folder structure, e.g. `masks/scene0/scene0_000123.png`.
   - Each pixel value indicates foreground vs background (binary masks).

2. **Run-length encoding (RLE) in COCO format**  
   - Masks are encoded as compressed RLE strings in the annotation file.
   - This is more compact for large datasets and is directly compatible with many training libraries.

A typical COCO-style annotation entry for segmentation includes:

- `image_id` — link to the image,
- `category_id` — class label (lynx),
- `segmentation` — RLE or polygon,
- `area` — area of the mask in pixels,
- `bbox` — bounding box covering the mask.

In the synthetic case, masks can be generated directly from the 3D rendering passes.  
In the real case, masks are usually drawn manually in a labeling tool (e.g., CVAT) and then exported.

---

## 6. Bounding boxes

Bounding boxes can be derived from either:

- the segmentation masks, or
- the projected 3D bounds of the mesh.

They are typically stored as:

- `bbox`: `[x_min, y_min, width, height]`.

Bounding boxes are used by:

- object detectors,
- some re-ID pipelines (for cropping around the animal),
- and evaluation scripts that require bounding boxes even when masks are available.

---

## 7. Task membership and splits

Since all tasks share the same underlying data package, the metadata file indicates **which tasks use each record** and in which splits.

Conceptually, each image (or annotation) can have flags like:

- `use_for_reid`: `true` / `false`
- `use_for_pose`: `true` / `false`
- `use_for_segmentation`: `true` / `false`
- `split_reid`: `"train"`, `"val"`, `"test"` (or `null` if unused)
- `split_pose`: `"train"`, `"val"`, `"test"` (or `null`)
- `split_segmentation`: `"train"`, `"val"`, `"test"` (or `null`)

The exact field names may differ in your implementation, but the idea is:

- There is a **single metadata file**.
- For each image/annotation, it encodes:
  - whether the sample is used by a given task,
  - and, if so, in which split (train/val/test).

This design avoids maintaining separate metadata files per task while still allowing clean, task-specific subsets to be extracted.

---

## 8. Summary

In summary, each sample produced by the pipeline can provide:

- an RGB image,
- 2D keypoints (pose),
- an identity label,
- a segmentation mask and bounding box,
- scene and camera metadata,
- and task/split flags for re-ID, pose, and segmentation.

Downstream scripts can then:

- filter the dataset by task and split,
- convert the annotations into standard formats (e.g., COCO for pose and segmentation),
- and mix real and synthetic data in a controlled way.

The later sections of the documentation describe how these labels are produced in Unity (for synthetic images) and how they align with the real CzechLynx dataset.