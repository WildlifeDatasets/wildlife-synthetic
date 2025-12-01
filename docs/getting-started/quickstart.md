Gotcha, let’s lock in one file at a time.
Next up: quickstart.md (a lynx-focused “run it once” guide), with image spots baked in.

Here’s a draft you can drop into docs/quickstart.md:

# Quickstart (lynx)

This page shows how to run the WildLife Synthetic pipeline for the lynx setup and generate a small batch of synthetic images with pose annotations.

If you have not installed Unity or imported the required assets yet, please see **Installation & setup** first.

---

## Before you start

You need:

- **Unity Hub** and **Unity 2022.2.9f1** installed  
- A new or existing **3D HDRP project**  
- The following Unity Asset Store packages imported into that project:
  - Terrain Texture  
  - Snow Materials  
  - Book Of The Dead  

You also need the WildLife Synthetic / Synthetic-animal-pose-generation repository downloaded.

```bash
git clone https://github.com/strakaj/Synthetic-animal-pose-generation.git
```

## 1. Add the assets to your Unity project

1. **Create or open** a 3D HDRP project in Unity 2022.2.9f1.
2. In **Unity Asset Store / Package Manager**, import:
   - Terrain Texture  
   - Snow Materials  
   - Book Of The Dead  
3. In your file browser:
   - Open the Unity project folder.
   - Copy the contents of `Synthetic-animal-pose-generation/Assets/`  
     into your project’s `Assets/` folder.
   - When asked, allow overwriting the `_TerrainAutoUpgrade` folder (this is expected).
4. Back in Unity, open **Window → Rendering → HDRP Wizard** and click  
   **Convert All Built-in Materials to HDRP**.

After import and conversion finish, Unity should show the added scenes and scripts under `Assets/`.

> _Optional image:_  
> `![Unity project with imported assets](assets/images/quickstart/unity_project_overview.png)`

---

## 2. Open the main menu or a demo scene

The project contains a simple entry point and several prepared scenes.

1. In the **Project** window, navigate to `Assets/Scenes/` (or the folder used for scenes in this repo).
2. Either:
   - Open the `main_menu` scene to control basic parameters from a menu, or  
   - Open one of the lynx demo scenes directly (for example, a forest scene matching the paper’s examples).

Once the scene is open, you should see:

- A forest environment (Book of the Dead–based),
- A lynx placeholder model,
- A camera positioned like a camera trap.

> _Optional image:_  
> `![Lynx scene in Unity](assets/images/quickstart/unity_scene_view.png)`

---

## 3. Configure basic simulation parameters

Most simulation settings are controlled by the `GlobalVariables` script.

1. In the Project window, open:

   ```text
   Assets/SyntheticGeneration-Assets/Scripts/GlobalVariables.cs
   ```
2. Adjust the parameters as needed, for example:
   - number of frames to simulate  
   - capture interval (every N-th frame)  
   - output path  
   - probabilities for texture changes and auxiliary animations  

You can start with the default values to simply confirm that everything runs.

---

## 4. Run the simulation

With a scene open and `GlobalVariables` configured:

1. Make sure the **Game** view is visible.  
2. Press **Play** in the Unity toolbar.  
3. If you opened `main_menu`, use the on-screen controls to start the simulation.  
   If you opened a scene directly, the simulation starts based on the values in `GlobalVariables.cs`.

During the run, the lynx moves along predefined paths, occasionally changes pose or texture, and the camera captures frames at the specified interval.

---

## 5. Inspect the outputs

After the simulation finishes (or after you stop it):

1. Open the output directory configured in `GlobalVariables`  
   (for example, `data/synthetic/` under your project).  
2. You should see at least:
   - an `images/` folder with rendered RGB images  
   - one or more annotation files (e.g., JSON) with keypoints and metadata  

> _Optional image:_  
> `![Example synthetic output image](assets/images/quickstart/sample_output_lynx.jpg)`  
> `![Output folder structure](assets/images/quickstart/output_folder_structure.png)`

---

## 6. Next steps

From here, you can:

- Read **Pipeline overview** to understand how waypoints, stop points, and capture logic work.  
- Check **Animal assets** (model, keypoints, textures, animations) to see how the lynx is set up.  
- Follow **Adapting to other species** if you want to plug in a different animal model.

Once the quickstart runs successfully, all other sections build on the same Unity project and output structure.