# Installation & setup

This page describes how to set up the environment for running the WildLife Synthetic pipeline.  
The instructions assume that you start from an empty Unity HDRP project and then bring in the synthetic generation assets from the public repository.

---

## 1. Prerequisites

Before you start, you should have:

- **Unity Hub** installed.
- **Unity 2022.2.9f1** available in Unity Hub. The project was developed and tested with this version, and using a different version can cause shader or rendering issues.
- A machine running Windows, Linux, or macOS with enough GPU memory to render scenes at your chosen resolution. Rendering without a GPU is possible but slow.
- **Git**, or the ability to download a GitHub repository as a ZIP file.
- Optionally, **Python 3.9+** if you plan to use helper scripts to merge annotations or convert them to other formats.

You do not need to install any additional C# tooling; Unity takes care of that.

---

## 2. Obtain the synthetic generation project

The Unity-specific assets and scripts are stored in the `Synthetic-animal-pose-generation` repository.  
You can either clone it with Git or download it as a ZIP.

To clone with Git:

```bash
git clone https://github.com/strakaj/Synthetic-animal-pose-generation.git
```

After this step, you should have a directory:

```text
Synthetic-animal-pose-generation/
  Assets/
  Packages/
  ProjectSettings/
  ...
```

For the setup described here, we will only copy selected content from the `Assets/` folder into your own HDRP project rather than opening this repository as a standalone Unity project.

---

## 3. Create a new HDRP Unity project

The synthetic scenes are built on top of HDRP (High Definition Render Pipeline).  
If you already have an HDRP project that you want to use, you can skip to the next section. Otherwise:

1. Open **Unity Hub**.
2. Click **New project**.
3. Select a **3D HDRP** template.
4. Choose **Unity version 2022.2.9f1**.
5. Enter a project name (for example, `WildLifeSyntheticLynx`) and choose a location.
6. Click **Create project** and wait until Unity finishes initializing the project.

When Unity opens, you should see an empty HDRP scene with the default camera and lighting.  
This project will be the base into which you import the synthetic assets and scenes.

---

## 4. Install required Unity assets

The synthetic environments use several publicly available Unity assets to provide terrain, snow, and vegetation.  
These are typically installed via the Unity Package Manager from your Unity account’s asset library.

1. In Unity, open **Window → Package Manager**.
2. Switch to the **My Assets** tab (or the equivalent Asset Store listing).
3. Search for and import the following packages into your project:
   - **Terrain Texture**
   - **Snow Materials**
   - **Book Of The Dead**

For each asset:

- Click **Download** (if it is not yet downloaded).
- Click **Import** and confirm the default import settings.

When all three are imported, your project contains the terrain textures, snow shaders/materials, and Book Of The Dead environment assets that the synthetic scenes rely on.

---

## 5. Copy the synthetic generation assets into your project

Next, you bring the synthetic generation scripts, scenes, and configuration into your HDRP project.

1. Open your file browser.
2. Navigate to the HDRP project you just created. You should see folders such as:

   ```text
   <YourUnityProject>/
     Assets/
     Packages/
     ProjectSettings/
   ```
3.	In another window, open the cloned repository:
```text
Synthetic-animal-pose-generation/
  Assets/
  ...
```
4. Copy the **contents** of `Synthetic-animal-pose-generation/Assets/` into the `Assets/` folder of your Unity project.  
   You can either copy the folders one by one (for example, `Scripts/`, `Scenes/`, `SyntheticGeneration-Assets/`) or copy everything under `Assets/` at once.

During this copy, Unity might later report that some terrain-related files already exist (for example, `_TerrainAutoUpgrade` content).  
In that case, allow overwriting. These files are part of the terrain material upgrade process and are safe to replace.

5. Return to Unity. Unity will detect the new files and start importing them.  
   Wait until the progress bar in the bottom-right corner disappears.

After the import finishes, open the **Project** window and verify that you can see:

- A folder such as `SyntheticGeneration-Assets` with configuration scripts.
- Several scenes related to synthetic generation (lynx demo scenes, test scenes, or a main menu).
- C# scripts that implement the agent behavior, camera capture, and global configuration.

---

## 6. Ensure materials are converted to HDRP

If your project started from a non-HDRP template or if some materials appear pink or incorrect, you should run HDRP’s material conversion.

1. In Unity, open `Window → Rendering → HDRP Wizard`.
2. In the wizard, look for an action similar to:

   ```text
   Convert All Built-in Materials to HDRP
   ```
3. Run the conversion and wait until Unity finishes updating materials and shaders.

This step ensures that all materials, including those from the synthetic generation assets and the imported Book Of The Dead environment, render correctly under HDRP.

---

## 7. Check that the synthetic scenes open correctly

At this point, the project should contain the synthetic scenes and scripts.  
To verify that everything is in place:

1. In the **Project** window, locate the folder that contains the synthetic scenes.  
   This is often something like `Assets/Scenes/` or a specific folder inside the imported assets.
2. Double-click one of the prepared lynx scenes (for example, a forest scene used in the paper).
3. Wait for the scene to load in the **Scene** view.

In the editor, you should now see:

- A forest environment or similar outdoor scene  
- A camera placed at roughly the height of a camera trap  
- A placeholder lynx model (or other animal model) in the scene  
- One or more scripts attached that control the agent and capture process  

If the scene opens without errors in the Console and renders correctly in the **Game** view, the basic setup is complete.

## 8. What to do next

Once the Unity project opens the synthetic scenes without errors, you are ready to generate data.

Recommended next steps:

- Follow the **Quickstart (lynx)** guide to run a short simulation and confirm that images and annotations are being written to disk.  
- Read the **Pipeline overview** to see how waypoints, stop points, textures, and animations interact during a simulation.  
- Explore the **Animal assets** and **Environments** sections to understand how the 3D model, keypoints, textures, and scene variants are configured.

After you successfully run the quickstart, you can start changing parameters, adding new scenes, or adapting the pipeline to a different species.