# Image Generation Prompts

Prompts for the `generate_design_image` tool (FUTURE-011). Versioned here to iterate independently from code.

---

## sketch-from-photo-v2 ← active

**Use case:** Transform a bonsai photo into a hand-drawn design sketch for `design-plan.md` wiki pages.

**Trigger:** User uploads a photo and the design plan agent generates a visual reference sketch.

**Key improvement over v1:** Structural fidelity enforced explicitly — trunk must match the real tree exactly, no redesign, no idealization.

### Positive prompt

```
Transform the input image of the bonsai tree into a clean hand-drawn bonsai design sketch, similar to a traditional bonsai concept drawing made by an experienced bonsai artist.

The most important requirement is structural fidelity. Preserve the exact real trunk line from the input image as the main visual anchor. Do not redesign, straighten, rotate, beautify, or replace the trunk with a generic ideal bonsai shape. Keep the same trunk path, bends, angles, thickness changes, deadwood position, root base, and relationship between the trunk and the pot. The final drawing must clearly match the original tree's real structure.

Preserve the tree's main identity: trunk movement, primary branch placement, overall silhouette, visual balance, root base, deadwood features, foliage distribution, and pot position from the input image. Interpret the image as a bonsai design sketch, but do not invent a new bonsai design.

Convert the photograph into a black-and-white ink drawing on a plain white background. Use expressive organic pen lines, natural line-weight variation, subtle cross-hatching, and a slightly loose handmade sketchbook style. The drawing should look like a bonsai artist documenting and planning the actual tree.

Prioritize the trunk and primary branches over all other details. The trunk must be the clearest, strongest, and most continuous element in the drawing. Use selective hatching to show bark texture, age, deadwood, exposed roots, and movement, but avoid excessive shading.

Simplify the foliage into clean stylized bonsai foliage pads, while keeping each foliage mass in approximately the same position and proportion as in the input image. Use compact cloud-like pine foliage pads with only a few short irregular needle strokes to suggest texture. Avoid large radial needle bursts, excessive individual needles, realistic botanical foliage, or overly decorative generic pads.

Reduce internal branch clutter and unnecessary secondary branches. Keep only the primary structural branches needed to understand the bonsai design. Do not add extra crossing branches or decorative branch lines that are not present or not structurally necessary.

Keep the composition centered and readable. Include the bonsai pot as a simple complete outlined container with minimal detail, preserving its position, scale, and relationship to the tree. Leave generous white space around the tree.

The final image should look like an artistic bonsai styling concept sketch of the actual input tree: faithful, structural, elegant, minimal, handmade, and expressive.
```

### Negative prompt

```
Color, watercolor, oil painting, photorealism, realistic photographic texture, full background, garden scenery, table, hands, tools, labels, annotations, signatures, stamps, text, logo, decorative frame, digital painting effects, 3D rendering, smooth vector illustration, cartoon style, anime style, heavy black fills, excessive shading, grayscale gradients, cluttered composition, multiple trees, distorted pot, missing trunk, unrealistic branch layout, redesigned trunk, generic idealized bonsai shape, excessive needle detail, overly detailed individual needles, overly polished vector art.
```

### Notes

- Output saved to `gallery/design-references/` (per FUTURE-011 Opción A).
- Gemini Imagen API: pass the user's bonsai photo as input image alongside this prompt.
- Iteration candidates: adjust foliage pad style per species (needle clusters for conifers, rounded pads for broadleaf).

---

## sketch-from-photo-v1 ← superseded by v2

**Superseded because:** did not explicitly enforce structural fidelity; model tended to idealize or replace the trunk with a generic bonsai shape.

### Positive prompt

```
Transform the input image of the bonsai tree into a clean hand-drawn bonsai design sketch, similar to a traditional bonsai concept drawing.

Preserve the real tree's main structure, trunk movement, branch placement, silhouette, visual balance, and pot position from the input image. Convert the photograph into a black-and-white ink drawing on a plain white background. Use expressive, organic pen lines with a slightly loose sketchbook style, as if drawn by a bonsai artist planning the tree's future design.

Emphasize the trunk's curves, deadwood features, bark texture, exposed roots, and main branch directions. Simplify the foliage into stylized needle clusters and compact bonsai foliage pads, using fine hatch marks and short irregular strokes rather than realistic photographic detail. The drawing should look like an artistic bonsai styling sketch, not a photorealistic rendering.

Keep the composition centered. Include the bonsai pot as a simple outlined container with minimal detail. Use only black ink lines, subtle cross-hatching, and natural line-weight variation. Leave generous white space around the tree. The result should feel elegant, handmade, minimal, and suitable for bonsai design visualization.

Avoid color, shading gradients, realistic photo texture, background objects, heavy shadows, excessive detail, digital painting effects, cartoon style, 3D rendering, or overly polished vector art.
```

### Negative prompt

```
Color, watercolor, oil painting, photorealistic, realistic bark photo texture, full background, garden, table, hands, tools, labels, annotations, text, logo, frame, digital painting, 3D render, smooth vector illustration, cartoon, anime, heavy black fills, excessive shading, cluttered composition, multiple trees, distorted pot, missing trunk, unrealistic branch layout.
```

# last

Transform the input image of the bonsai tree into a clean hand-drawn bonsai design sketch, similar to a traditional bonsai concept drawing made by an experienced bonsai artist.

The most important requirement is structural fidelity. Preserve the exact real trunk line from the input image as the main visual anchor. Do not redesign, straighten, rotate, beautify, or replace the trunk with a generic ideal bonsai shape. Keep the same trunk path, bends, angles, thickness changes, deadwood position, root base, and relationship between the trunk and the pot. The final drawing must clearly match the original tree’s real structure.

Preserve the tree’s main identity: trunk movement, primary branch placement, overall silhouette, visual balance, root base, deadwood features, foliage distribution, and pot position from the input image. Interpret the image as a bonsai design sketch, but do not invent a new bonsai design.

Convert the photograph into a black-and-white ink drawing on a plain white background. Use expressive organic pen lines, natural line-weight variation, subtle cross-hatching, and a slightly loose handmade sketchbook style. The drawing should look like a bonsai artist documenting and planning the actual tree.

Prioritize the trunk and primary branches over all other details. The trunk must be the clearest, strongest, and most continuous element in the drawing. Use selective hatching to show bark texture, age, deadwood, exposed roots, and movement, but avoid excessive shading.

Simplify the foliage into clean stylized bonsai foliage pads, while keeping each foliage mass in approximately the same position and proportion as in the input image. Use compact cloud-like pine foliage pads with only a few short irregular needle strokes to suggest texture. Avoid large radial needle bursts, excessive individual needles, realistic botanical foliage, or overly decorative generic pads.

Reduce internal branch clutter and unnecessary secondary branches. Keep only the primary structural branches needed to understand the bonsai design. Do not add extra crossing branches or decorative branch lines that are not present or not structurally necessary.

Keep the composition centered and readable. Include the bonsai pot as a simple complete outlined container with minimal detail, preserving its position, scale, and relationship to the tree. Leave generous white space around the tree.

The final image should look like an artistic bonsai styling concept sketch of the actual input tree: faithful, structural, elegant, minimal, handmade, and expressive.

Do not use color, watercolor, oil painting, photorealism, realistic photographic texture, full background, garden scenery, table, hands, tools, labels, annotations, signatures, stamps, text, logo, decorative frame, digital painting effects, 3D rendering, smooth vector illustration, cartoon style, anime style, heavy black fills, excessive shading, grayscale gradients, cluttered composition, multiple trees, distorted pot, missing trunk, unrealistic branch layout, redesigned trunk, generic idealized bonsai shape, excessive needle detail, overly detailed individual needles, or overly polished vector art.