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

See more in the [asset extraction guide](##extracting-game-assets)

<p>
  <img alt="import button" src="https://github.com/Picalines/outer-scout-blender/assets/42614422/3e25224c-0e7c-4b24-99c4-96e39f8d7d97" width="30%" align="middle">
  <img alt="imported body" src="https://github.com/Picalines/outer-scout-blender/assets/42614422/3d34221d-cee7-4d97-af6a-fe66a5b1ac1d" width="65%" align="middle">
</p>

### 4. Make a camera

Put the camera in Blender and animate it

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

## Requirements

### Extracting game assets

TODO!

In order to import planet meshes into Blender you firstly need to extract mesh assets from the game. I've tested this with AssetStudio, maybe some newer program would also do.

- Open AssetStudio
- `File > Load Folder`
- Select your Outer Wilds's data folder (`OuterWilds_Data`)
- `Options > Export options`, set the `Group exported assets by` option to `container path`
- `Filter type > Mesh`
- `Export > Filtered assets`
