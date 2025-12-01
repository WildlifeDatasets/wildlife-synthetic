# Unity project layout

This page explains how the Unity project is organized and where to find the pieces that control the synthetic generation pipeline: scenes, scripts, configuration, and prefabs.  
The goal is to help you navigate the project so you know **what to touch** when you want to change behavior or adapt the pipeline to another species.

---

## 1. Top-level structure

Once the synthetic assets are copied into your HDRP project and imported, the **Project** window will contain several new folders under `Assets/`.  
The exact names may differ slightly, but you can expect something like:

- `Assets/Scenes/` – demo scenes and main entry points.
- `Assets/SyntheticGeneration-Assets/` – scripts, configuration files, and support assets.
- `Assets/BookOfTheDead/` (or similar) – environment assets used to build photorealistic scenes.
- `Assets/Models/` – 3D models for the animal and other scene objects (names may vary).
- `Assets/Materials/`, `Assets/Textures/`, `Assets/Animations/` – materials, textures, and animation clips.

You do **not** need to edit all of these folders. For most users, the important ones are:

- **Scenes** – to choose which environment and camera setup to use.
- **SyntheticGeneration-Assets/Scripts** – to adjust global parameters and behavior.
- **Models / Prefabs** – to swap the animal model or update its components.

> _Optional image:_  
> `![Project window with key folders highlighted](assets/images/unity_project/project_overview.png)`

---

## 2. Scenes

The scenes define:

- the **environment** (terrain, vegetation, snow, logs, etc.),
- the **camera** placement (to mimic a camera trap),
- the **waypoints** and helper objects used by the simulation,
- and the **animal** instance placed in the scene.

Typical scene types include:

- A **main menu** or hub scene (optional), where you can start simulations and adjust basic settings from a UI.
- One or more **lynx scenes** that correspond to the forest and snow environments used in the CzechLynx experiments.

To explore a scene:

1. In the Project window, open `Assets/Scenes/`.
2. Double-click a scene such as `LynxForest.unity` (name may differ).
3. In the Scene view, you should see:
   - the terrain and vegetation,
   - a `Main Camera` or similar camera object,
   - an animal object (lynx) with attached components,
   - waypoint objects placed along the path.

These scenes are the starting point for running the simulation and for adapting the pipeline to other species.

> _Optional image:_  
> `![Example lynx scene](assets/images/unity_project/lynx_scene.png)`

---

## 3. Core scripts and components

The behavior of the simulation is controlled by a small set of scripts.  
You will typically find them under something like:

- `Assets/SyntheticGeneration-Assets/Scripts/`

The exact class names may differ, but the roles are usually:

- **Global configuration**
  - A script such as `GlobalVariables.cs` that holds:
    - number of frames to simulate,
    - capture interval (every *N*-th frame),
    - random seed(s),
    - output directories,
    - probabilities for texture changes and auxiliary animations.

- **Agent / animal controller**
  - A script attached to the animal object (for example, `AnimalModelAgent`).
  - Handles:
    - movement along waypoints,
    - switching between animations (walk, sit, idle),
    - triggering capture events at specific times.

- **Camera capture**
  - A script on the main camera (for example, `CameraCapture`).
  - Responsible for:
    - capturing RGB frames,
    - reading keypoint positions,
    - applying visibility checks,
    - writing images and annotations to disk.

- **Mesh / bounds helper**
  - A script such as `GetMeshPosition` attached to the animal.
  - Used to:
    - query mesh bounds,
    - compute bounding boxes,
    - support visibility checks and mask generation.

The important thing is not the exact filenames, but **where they are attached**:

- The **animal GameObject** has:
  - the agent script,
  - animation controller,
  - mesh-related helpers.

- The **main camera** has:
  - the capture script,
  - references to keypoints and other metadata fields.

---

## 4. Global configuration

Most high-level settings are centralized in a script similar to `GlobalVariables.cs`.  
This script is usually found in the scripts folder and referenced by multiple components.

Common parameters include:

- `TotalFrames` – total number of frames in a simulation run.
- `CaptureInterval` – capture every `N`-th frame.
- `OutputPath` – root folder where images and annotations are written.
- `TextureChangeProbability` – how often to switch individuals.
- `AuxAnimationProbability` – how often to trigger non-walk animations.
- Seeds for random number generators.

To adjust these:

1. Open `GlobalVariables.cs` in your code editor.
2. Look for clearly labeled fields at the top of the class.
3. Edit the default values, or expose them as public fields and change them from the Inspector.

These settings control how much data is produced and how diverse it is, without requiring changes to the scene itself.

---

## 5. Animal prefab and hierarchy

The animal in each scene is usually based on a **prefab**.  
You can examine its hierarchy to understand where key components live:

- Root object – overall position and rotation.
- **SkinnedMeshRenderer** – the actual 3D mesh and material.
- **Armature / bones** – used for animation and pose.
- **Keypoint objects** – small empty GameObjects attached to the bones; these represent joint locations.
- Agent / helper scripts – attached at the root or relevant child objects.

To see this:

1. Select the animal object in the **Hierarchy**.
2. Inspect the **Inspector** panel:
   - Check which scripts are attached.
   - Check references such as:
     - `Keypoints` array (assigned to the camera capture script),
     - `MeshRenderer` references used by bounding box helpers.

When adapting to another species, you will usually:

- replace the mesh and armature,
- re-create or reposition keypoint empties,
- and update references in the camera and agent components.

The detailed steps for that are covered in the “Animal assets” section, but this page gives you the context of where things are in the project.

---

## 6. Output location and file structure

The Unity project writes output files (images and annotations) to a directory configured by the capture or global variables scripts.

Typical structure:

- `data/`
  - `synthetic/`
    - `images/`
      - `scene0/scene0_000001.jpg`
      - `scene0/scene0_000002.jpg`
      - …
    - `annotations/`
      - JSON files with keypoints, identities, masks, etc.

The exact path is defined in the script (`GlobalVariables.cs` or `CameraCapture.cs`).  
Make sure that:

- the path is valid on your system,
- and you have write permissions for that folder.

Later, Python utilities or other tools can read from this location to build COCO-style annotation files or merge per-frame metadata.

> _Optional image:_  
> `![Output folder structure](assets/images/unity_project/output_structure.png)`

---

## 7. How everything connects

Putting it all together:

- **Scenes** define the environment, camera, and waypoints.  
- **Animal prefab** defines the model, rig, keypoints, and animations.  
- **Scripts** on the animal and camera implement the simulation loop and capture logic.  
- **Global configuration** sets how long the simulation runs and what variability to introduce.  
- **Output paths** and file formats determine how the data are written to disk.

Once you are comfortable with this layout, the next step is to dig into the **Animal assets** pages, which describe in more detail how the model, keypoints, textures, and animations are set up and how to adapt them to another species.