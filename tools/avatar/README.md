# Joel's 3D body — how models/joel.glb was made

1. `1_image_to_mesh.py` — sends `source-front.jpg` (Gemini, full body, A-pose, plain grey) to the free
   Hugging Face Space `tencent/Hunyuan3D-2.1` (`/shape_generation`; the textured `/generation_all` needs
   more ZeroGPU quota than the free tier gives). Output: an untextured `white_mesh.glb`.
2. Texture atlas (2048×1620): left half = the front photo, right half = a mirrored copy with the face
   painted over as hair/skin and the white tee/pockets painted shirt-olive, then body colours bled
   into the grey background so silhouette edges don't pick up grey.
3. `3_rig_and_export.py` (Blender 5, `blender -b -P`) — decimate to ~29k tris, smooth shade, project UVs
   (front-facing faces → left half, back-facing → right half), build a Mixamo-named skeleton from joint
   positions read off the photo (depth = centre of the mesh slice), automatic weights, export GLB (~1.3 MB).

Paths inside the scripts point at the scratchpad used at the time; swap them for a re-run.
The photo's silhouette bounds (x 136–1504, y 177–2523 px) and joint pixels are specific to this image.
