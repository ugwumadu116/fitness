# v2 pipeline (2026-10-04) — outfit + real back view

1. Outfit: gpt-image-1 `images/edits` on the source photo (input_fidelity=high) → `A/B/C.png`;
   then the same endpoint on each result asking for a back view → `Ab/Bb/Cb.png`. Key: OpenAI key in AiProjects/.env.
2. `h3d_mv.py N` — Hunyuan3D-2.1 `/shape_generation` with front as image + mv_front, back as mv_back → `N-mesh.glb`.
3. `joints2d.py A B C` — 2D joints from the silhouette (largest blob; crotch searched in the top 75%).
4. `make_atlas.py N` — [front | back] atlas, body colours bled into the background.
5. `N=A OUT=.../models/lab/A.glb blender -b -P bl_build2.py` — decimate, UV-project front/back aligned on torso centre, Mixamo-named rig, auto weights, GLB.
Preview any GLB: `index.html?model=models/lab/A.glb&cycle&bare`; side-by-side at `lab.html`.
