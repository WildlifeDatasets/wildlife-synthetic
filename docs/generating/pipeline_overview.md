# Pipeline overview

This page explains how the WildLife Synthetic pipeline generates labeled images from a 3D animal model and a small set of scenes.  
It focuses on the *logic* of the simulation: how the animal moves, how variability is introduced, and when frames are captured.

> **At a glance:**  
> A rigged animal moves along paths in a photorealistic scene. At random stop points, pose, camera, and appearance are changed.  
> At regular intervals, the camera captures frames, and the engine exports images together with pose keypoints, masks, identities, and metadata.

---

## 1. High-level data flow

The overall flow of the pipeline is:

1. **Inputs**
   - 3D animal model (mesh + rig + animations)
   - Library of textures (different individuals)
   - One or more Unity scenes (environments)
   - Global configuration (number of frames, capture interval, probabilities, output paths)

2. **Simulation**
   - The animal is placed in a scene and moves along a path defined by waypoints.
   - Random “stop points” are inserted along the path.
   - At stops, the pipeline may change pose, texture, environment variant, or camera viewpoint.

3. **Capture**
   - Every *N*-th frame, the pipeline checks whether the animal is sufficiently visible.
   - If the visibility check passes, an output sample is created: image + annotations + metadata.

4. **Outputs**
   - RGB images
   - 2D keypoints (pose)
   - Optional instance masks and bounding boxes
   - Identity labels (texture IDs)
   - Scene and camera metadata

A simple schematic for this is:

> _Optional image:_  
> `![High-level pipeline](assets/images/overview/pipeline_overview.png)`  
> *From inputs (model, textures, scenes) through simulation, to images and labels.*

---

## 2. Inputs and configuration

Before any simulation starts, a few key components must be in place.

### 2.1 Animal model and textures

- A **rigged 3D model** of the animal is required.  
  The rig’s bones are used for animation and for reading keypoints.
- A **set of textures** is prepared (for example, using diffusion-based text-to-texture methods).  
  Each texture corresponds to a synthetic individual.

The identity of an individual is defined purely by the active texture. The same model with different textures represents different individuals.

### 2.2 Scenes and waypoints

- One or more **photorealistic environments** are created using Unity assets such as Book Of The Dead.  
  These scenes approximate real camera-trap locations.
- In each scene, a set of **waypoints** is defined.  
  The animal moves between these waypoints during the simulation.
- Some waypoints may be placed outside the camera’s field of view so that the animal naturally enters and leaves the frame.

### 2.3 Global variables

A configuration script (for example `GlobalVariables.cs`) collects the main settings, such as:

- total number of frames to simulate,
- capture interval `N` (capture every `N`-th frame),
- probabilities for texture changes and auxiliary animations,
- output folder for images and annotations.

These parameters control the length and richness of the generated dataset without changing scene content.

---

## 3. Scenario setup

When a simulation starts, the pipeline performs a one-time setup:

1. **Select a scene**  
   One of the prepared environments is loaded. This scene contains:
   - terrain, trees, snow or grass,
   - a camera placed like a camera trap,
   - waypoints and other helper objects.

2. **Place the animal**  
   The animal model is instantiated in the scene:
   - positioned near one of the waypoints,
   - oriented along the path,
   - assigned an initial texture (individual identity).

3. **Initialize animations**  
   The main locomotion animation (walking) is activated.  
   Auxiliary animations (e.g., sitting, idle, head turn) are also available and can be triggered later.

After this setup, the pipeline enters the simulation loop.

> _Optional image:_  
> `![Example scene with waypoints and camera](assets/images/pipeline/scene_with_waypoints.png)`  
> *A lynx scene showing the camera, waypoints, and the animal’s path.*

---

## 4. Simulation loop

The simulation loop updates the scene frame by frame.  
For each frame, a few core steps are performed:

1. **Move the animal along the path.**  
2. **Decide whether a “stop” is reached and apply changes.**  
3. **Decide whether to capture the current frame.**

### 4.1 Movement along waypoints

The animal moves along a path defined by the waypoints in the scene:

- Waypoints are visited in a fixed or random order.
- The animal’s transform is updated so its position interpolates smoothly between waypoints.
- The walking animation provides realistic leg motion.

The effect is a continuous walk through the environment, occasionally crossing the camera view.

### 4.2 Stop points and variability

To avoid monotonous motion and to introduce diversity, “stop points” are sampled along each segment between two waypoints.

When the animal reaches a stop point, the pipeline may:

- trigger an **auxiliary animation** (e.g., sit down),
- apply a **small rotation** around the vertical axis (change heading),
- change the **active texture** (switch individual),
- modify **environment details** (e.g., snow on/off, different vegetation variant),
- apply a **small camera perturbation** (slight change in angle or offset).

These changes are controlled by the global parameters (e.g., probabilities of triggering events) and are the main source of pose, appearance, and context variation.

---

## 5. Capture logic

Not every frame is turned into a dataset sample. The capture logic has two layers:

1. **Frame subsampling** – reduce redundancy by capturing only every `N`-th frame.  
2. **Visibility check** – skip frames where the animal is not sufficiently visible.

### 5.1 Frame subsampling

A simple frame counter is used:

- At each simulation step, a counter `frame_index` is incremented.
- Only when `frame_index % N == 0` is the frame considered for capture.

This is enough to avoid generating thousands of nearly identical frames without changing the animation speed.

### 5.2 Visibility check

Before a frame is saved, a visibility check is applied:

- The 3D bounds of the animal are computed (for example, from the skinned mesh).
- These bounds are projected into the camera’s image plane.
- The resulting 2D bounding box is tested:
  - Does it cover a minimum area?
  - Is most of the box inside the image?

If the animal is mostly outside the view or only a tiny portion is visible, the frame is discarded.  
This keeps the dataset focused on informative images that are suitable for training.

> _Optional image:_  
> `![Timeline of simulation with captures and skips](assets/images/pipeline/simulation_timeline.png)`  
> *Frames along the timeline; some are skipped due to subsampling or low visibility.*

---

## 6. What is exported per frame

When a frame passes both the subsampling and visibility checks, annotations are extracted from the 3D scene and written to disk together with the image.

For each accepted frame, the pipeline can export:

- **RGB image**  
  - Rendered from the main camera at a fixed resolution.
- **2D keypoints (pose)**  
  - Each anatomical landmark is defined by a 3D point attached to the rig.
  - Points are projected into image coordinates, producing `(x, y)` per keypoint and a visibility flag.
- **Segmentation mask (optional)**  
  - A separate render pass or camera produces a binary mask of the animal’s silhouette.
- **Bounding box**  
  - Derived from the projected 3D bounds or from the mask.
- **Identity label**  
  - Encoded as an integer or string based on the active texture.
- **Metadata**  
  - Scene identifier, camera parameters, frame index, current animation state, and other tags.

These outputs are typically aggregated into a JSON file or converted into a COCO-style annotation file for downstream tasks.

> _Optional image:_  
> `![Image with overlayed keypoints and bounding box](assets/images/pipeline/image_with_pose_and_box.png)`  
> *Example image with visualized keypoints and bounding box.*

---

## 7. Relation to task-specific subsets

The same pipeline configuration can produce data for different downstream tasks:

- **Individual identification**  
  - Uses images where the coat pattern is clearly visible.
  - Identity labels (derived from textures) are used to train and evaluate re-ID models.

- **Pose estimation**  
  - Uses images with 2D keypoints.
  - Real pose annotations are created on a subset of real images, while synthetic data provide dense pose coverage.

- **Instance segmentation**  
  - Uses the same images as identification, paired with binary masks.
  - Masks separate the animal from complex backgrounds.

The pipeline does not have to change per task; instead, task-specific subsets are created by filtering the outputs based on annotations and metadata.

---

## 8. Summary

In practical terms, the pipeline can be described as:

> 1. Place a rigged, textured animal in a realistic scene.  
> 2. Move it along a path, occasionally changing pose, appearance, or environment.  
> 3. At regular intervals, capture only those frames where the animal is clearly visible.  
> 4. For each captured frame, export images and annotations directly from the 3D engine.

The later sections of the documentation describe:

- how the **animal model** (rig, keypoints, textures, animations) is set up, and  
- how the **environments** and **camera-trap layout** are designed.

Together, these pieces make it possible to reproduce the lynx setup and extend the same logic to other species.