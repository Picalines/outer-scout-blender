# Outer Scout Blender

A frontend for the [Outer Scout](https://github.com/Picalines/outer-scout) mod. This addon allows you to make cinematic shots in Outer Wilds and import them into Blender!

![the Outer Scout thumbnail](https://github.com/Picalines/outer-scout/raw/master/thumbnail.png)

## Basic usage example

### 1. Open Blender and Outer Wilds at the same time

> [!NOTE]
> The mod makes the game work in the background without a pause. This is necessary so that the two programs can interact at any time

### 2. Create Outer Scout scene

Get to the desired location in Outer Wilds and click "Create Scene" in the scene properties tab

<p>
  <img alt="the create button" src="https://github.com/Picalines/outer-scout-blender/assets/42614422/0fba14eb-fc42-4353-8798-07067efe14a2" width="30%" align="middle">
  <img alt="desired location" src="https://github.com/Picalines/outer-scout-blender/assets/42614422/c0e87174-a125-4261-8f08-2f1c6197bf8e" width="65%" align="middle">
</p>

### 3. Import the planet model

> [!IMPORTANT]
> See more in the [asset extraction guide](#extracting-game-assets). You **will not** be able to do this without prior preparation

Planet models are only needed for convenient positioning of your objects - they shouldn't be on the final render of the scene

<p>
  <img alt="import button" src="https://github.com/Picalines/outer-scout-blender/assets/42614422/3e25224c-0e7c-4b24-99c4-96e39f8d7d97" width="30%" align="middle">
  <img alt="imported body" src="https://github.com/Picalines/outer-scout-blender/assets/42614422/3d34221d-cee7-4d97-af6a-fe66a5b1ac1d" width="65%" align="middle">
</p>

### 4. Make a camera

Put the camera in Blender and animate it. In addition to position and rotation, you can animate its `focal length`, `lens shift`, `clip start/end` and `sensor size`. You can try adding camera shake using the [camera shakify addon](https://github.com/EatTheFuture/camera_shakify)

<p>
  <img alt="camera configuration" src="https://github.com/Picalines/outer-scout-blender/assets/42614422/dcfa8e15-fc74-4b4d-b74b-df7997b08cd1" width="30%" align="middle">
  <img alt="camera animation" src="https://github.com/Picalines/outer-scout-blender/assets/42614422/fc927fa3-e618-4e49-9908-08cf64502d40" width="65%" align="middle">
</p>

> [!TIP]
> A file path that starts with `//` is relative to your `.blend` file. No need to open the file dialog!

### 5. Record the footage

Click the record button in the scene properties tab. After recording, all configured cameras will receive a background with the recorded video

<p>
  <img alt="the record button" src="https://github.com/Picalines/outer-scout-blender/assets/42614422/84b6f263-5388-4fac-92ae-81bac78ba259" width="30%" align="middle">
  <img alt="imported background" src="https://github.com/Picalines/outer-scout-blender/assets/42614422/8d197ab5-4006-4e3d-8d3b-1b282d949cbc" width="65%" align="middle">
</p>

<video src="https://github.com/Picalines/outer-scout-blender/assets/42614422/93856a82-1a20-4105-a615-c5c9b7fc0900"></video>

### 6. Setup compositor

The main idea of the mod and addon is to render blender models *on top* of the game's footages. To do this, click on the button and add the generated node group to the compositor tree

After that, you can do anything with your scene - you can even add effects on the footages of the game using the compositing nodes, or pull them into some editing program. You can make complex scenes with [multiple cameras](https://docs.blender.org/manual/en/latest/animation/markers.html#bind-camera-to-markers), and the addon will generate the necessary nodes for you

<p>
  <img alt="generate nodes button" src="https://github.com/Picalines/outer-scout-blender/assets/42614422/eaa4259d-dd77-4747-ba66-77a586b640fd" width="30%" align="middle">
  <img alt="compositing tab" src="https://github.com/Picalines/outer-scout-blender/assets/42614422/a657ecc9-d0ec-4591-97d9-d040f1cda91b" width="65%" align="middle">
</p>

<video src="https://github.com/Picalines/outer-scout-blender/assets/42614422/5d9a02ae-21e3-46d0-a6f2-16b3b79f7906"></video>

## Requirements

- Outer Wilds patch 15
- Blender 4.2 (tested in 4.3!)
- [Outer Scout mod](https://outerwildsmods.com/mods/outerscout/) (available in the [mod manager](https://outerwildsmods.com/mod-manager/)!)
- [FFmpeg](https://ffmpeg.org/about.html) for video recording. See the [mod's requirements](https://github.com/Picalines/outer-scout/blob/master/README.md#requirements) for more details
- [AssetStudio](https://github.com/Perfare/AssetStudio) for planet model extraction

## Installation

- Go to the [Releases tab](https://github.com/Picalines/outer-scout-blender/releases) and download the `outer_scout.zip` file of the latest version
- Open Blender, `Edit > Preferences > Get Extensions`
- Click on the arrow in the upper right corner, `Install from Disk...`
- Select the archive you downloaded earlier

See the [asset extraction section](#extracting-game-assets) to learn more about the addon settings

## Additional Features

### Game Object Replay

Use this feature to add interaction between game objects and your blender models:
1. Create an Empty in the Blender, and give it the name of the Unity object from Outer Wilds <ins>in the Outer Scout panel</ins>. The easiest way to find out the name of an object is using [Unity Explorer](https://outerwildsmods.com/mods/unityexplorer/)
2. Set the `Unity Object Mode` to `Existing`. In this mode, the mod will not create a new empty `UnityEngine.GameObject`, but search for an existing one
3. Specify the path to the file where the mod will record information about this object on each frame

After that, the `Transform Mode` property will appear, which tells the mod what to do after the next recording starts:
- In `Record` mode, the mod will capture the transformation parameters of the object on each frame of the animation, and then import them as key frames of the blender
- In `Replay` mode, the mod, on the contrary, imports the key frames of the blender into the game and assigns them to the object on each frame of the animation

*Yes, it's a bit complicated*, but the final algorithm is like this:
- Create an object in `Record` mode and hit the "record" button in the scene properties tab
- The mod *automatically* sets all `Record` objects to `Replay`
- Now you can animate your blender models based on the position of something from the game! *Dreams come true!*

<p>
  <img alt="game object config" src="https://github.com/Picalines/outer-scout-blender/assets/42614422/5968963d-4ded-436c-b41e-9e7958c81da6" width="30%" align="middle">
  <img alt="imported keyframes" src="https://github.com/Picalines/outer-scout-blender/assets/42614422/8693ddd5-11de-4017-a481-33cfc5a7f4dc" width="65%" align="middle">
</p>

<video src="https://github.com/Picalines/outer-scout-blender/assets/42614422/4a864760-80dd-45ce-a10a-99b70b194d76"></video>

### HDRI recording

You can select the `Equirectangular` type in the camera settings. In this case, the mod will record something like a 360 video from the point of that camera, which is suitable for creating [HDRI](https://docs.blender.org/manual/en/latest/render/lights/world.html) in a Blender

The "Generate HDRI nodes" button generates the desired node group to be added to the world shader. There can only be one HDRI camera on one scene

<p>
  <img alt="equirectangular camera" src="https://github.com/Picalines/outer-scout-blender/assets/42614422/726cb775-7dcd-410f-9d31-68b2e367b74d" width="30%" align="middle">
  <img alt="suzanne with hdri" src="https://github.com/Picalines/outer-scout-blender/assets/42614422/5cf63c0a-b382-4430-812a-f9f67906eab0" width="65%" align="middle">
</p>

### Depth recording

The mod can record several textures from one camera at once. In this way, you can get both a color channel and a depth channel at the same time. The latter is used in the generated compositing nodes to put the blender object "[behind](https://docs.blender.org/manual/en/latest/compositing/types/color/mix/z_combine.html#z-combine-node)" the game object

> [!WARNING]
> This feature works well only when your object is blocked by something from the foreground. Most likely, I incorrectly implemented the conversion of the Unity depth to Blender
>
> The result depends on the [clip planes](https://docs.blender.org/manual/en/latest/render/cameras.html#:~:text=it%20off%2Dcenter.-,Clip%20Start%20and%20End,-The%20interval%20in). The greater the distance, the worse

<p>
  <img alt="depth config" src="https://github.com/Picalines/outer-scout-blender/assets/42614422/7f0a3c4f-e225-417f-b528-7f66713a2ffc" width="30%" align="middle">
  <img alt="cropped render" src="https://github.com/Picalines/outer-scout-blender/assets/42614422/8ce9d119-0253-444d-84b2-4fb7e55785d0" width="65%" align="middle">
</p>

### Miscellaneous

#### `Sidebar > View > Outer Scout`

- Toggle the planet model visibility
- Warp the player to a position in the game corresponding to the position of the 3D cursor
- Reposition the scene using the 3D cursor

#### Planet sectors

The planets in the game are divided into separate sectors by points of interest to optimize their loading time. When creating a scene, you can stand in the right place in the game, and by default the addon imports only those sectors in which the player is located

This saves performance, especially on large planets with many separate enclosed rooms - inaccessible locations will be skipped. If desired, you still have the option to import the entire planet, or select a planet not according to the player's position (see the [asset extraction guide](##extracting-game-assets) for details)

#### Planet model animation

You can try to animate the rotation of the planet object, rather than the camera itself - then you will be able to make an orbit flight! *Just don't read [the code](https://github.com/Picalines/outer-scout-blender/blob/aa85ec6b886e7feecec7d7a8a4e9ff652deb775b/operators/record.py#L259) of this thing*

## Extracting game assets

In order to import planet models into Blender you need to extract mesh assets from the game

> [!TIP]
> <p>You can watch the video version on <a href="https://youtu.be/utD7gLyEBK8">YouTube</a>! Thanks @ShVanes for making it!</p>
> <a href="https://youtu.be/utD7gLyEBK8">
>  <img src="https://img.youtube.com/vi/utD7gLyEBK8/mqdefault.jpg" alt="drawing" width="33%"/>
> </a>
> <p>Please don't ask questions in the comments, as I may not see them - <a href="https://github.com/Picalines/outer-scout-blender/issues/new">Create an issue on GitHub</a></p>

Here're the steps:

1. Open the [AssetStudio](https://github.com/Perfare/AssetStudio)

2. Click `File > Load Folder`

3. Select your Outer Wilds's data folder (`OuterWilds_Data`). For Steam users: `Properties... > Installed Files > Browse...`

4. `Options > Export options`, set the `Group exported assets by` option to `container path`

<details>
  <summary>Other export options (optional)</summary>
  <img alt="other export options" src="https://github.com/Picalines/outer-scout-blender/assets/42614422/d3edfb8c-ef36-4061-b47c-0ac8e09c6eb4" width="40%">
</details>

> [!IMPORTANT]
> There are two folders with planet assets:
>  1. `bodies`: static low detailed `.fbx` meshes. They contain basic structure of the planet, but they're not useful for the human artists
>  2. `extracted`: dynamic for high detailed `.obj` meshes. They're the ones you want to see in your viewport
>
> I **highly** recommend you to name them that way, so it'll be easier to troubleshoot your folders
>
> <p>
>   <img alt="asset folders" src="https://github.com/user-attachments/assets/eb73ea00-dddb-4372-992c-4d544e5fe240" width="55%">
> </p>

5. `Filter type > Mesh`

6. `Export > Filtered assets` to the `extracted` assets folder

7. Open the `bodies` folder. Notice how AssetStudio has put all the files in the GameObject subfolder

> [!IMPORTANT]
> Set the *Bodies Folder* to the `GameObject` subfolder (`Edit > Preferences > Add-ons > Outer Scout > AssetFolders`)

8. Select the planets of interest, and then `Model > Export selected objects (split)` to the `bodies` folder
    - You should put all planets in one *bodies* folder - the addon will only search for `.fbx` and `.blend` files in there by the name. You don't need to change these paths more than once after installation
    - Each planet subtree must have object with `_Body` postfix within. You *can't* select the `SolarSystemRoot`, because each planet should be in a separate `.fbx` file
    - AssetStudio will emit the texture `.png` files along side with `.fbx`, but they're not required for this addon.

<img alt="export planets" src="https://github.com/Picalines/outer-scout-blender/assets/42614422/2fef80dc-38b5-4923-bbe8-0ae2574604f8" width="40%">

9. Close the AssetStudio, open Outer Wilds and Blender at the same time

10. In Outer Wilds, **go** to the planet you want to import. The addon will later "talk" to your game to find out about `.obj`'s it needs to import. You can pause the game, it doesn't matter

11. In Blender, open the `Properties > Scene > Outer Scout` panel and press the `Import` button. Keep the default options, it doesn't matter at the moment

12. If it's the first time you import the `X` planet, the addon will launch another Blender instance that'll generate a `bodies/X.blend` file for you
    - Look for the console window, in which the addon'll print the import progress
    - Your main Blender window will freeze with the "not responding" message - don't close it, it's waiting until the generation is done
   
13. If everything went okay, the `X` planet model will appear in your Blender scene. That means you now have the `bodies/X.blend` file, and you <ins>don't need to open AssetStudio or Outer Wilds to import the `X` planet anymore</ins>. Congratulations!
