# ShopReady Check: user guide

Check your 3D product model against store rules before the store rejects it. ShopReady Check reads your model, tests it against the published rules of Shopify, Amazon and a general web glTF profile, and explains each result. It does not change your model.

> Store rules change. We check the official pages every quarter, but the store's own review always decides.

Shopify and Amazon are trademarks of their owners. ShopReady Check is not affiliated with or endorsed by them.

## Contents

1. Install
2. Supported Blender versions
3. Your first check
4. The panels
5. The rules, store by store
6. Files it reads
7. Languages
8. Privacy and Security
9. FAQ

## 1. Install

1. Download the zip. Do not unzip it.
2. In Blender, open **Edit > Preferences > Get Extensions**.
3. Open the small dropdown at the top right of that window and choose **Install from Disk**.
4. Pick the zip file.
5. Close Preferences. In the 3D Viewport, press **N** to open the sidebar. Click the **ShopReady** tab.

To remove it, open **Edit > Preferences > Add-ons**, find ShopReady and disable or remove it. The tab goes away cleanly.


## 2. Supported Blender versions

Blender 4.2 LTS and newer, including the 5.x series. Older versions are not supported.

## 3. Your first check

1. Select your product in the 3D Viewport.
2. Open the **ShopReady** tab. Under **Target**, choose the store.
3. Optional: type the product's real size in centimetres.
4. Click **Check model**.
5. Read **Results**. Fix what is marked Fail first.


## 4. The panels

### Target

| Control | What it does |
|---|---|
| **Product** | What counts as the product. **Selected objects** (default), **Active collection** or **Whole scene**. Only mesh objects count for geometry. Cameras, lights and empties in scope are reported, not counted. |
| **Store** | The profile to check against. Built in: Shopify, Amazon, Web glTF. The line under it shows the date the rules were last checked. |
| **Reload profiles** (refresh icon) | Reads the profile files again. Use it after you edit a profile file by hand. A profile with an error is skipped and the error is shown in the panel. |
| **Real size (cm)**: W, D, H | Optional. The product's true width, depth and height. If you fill it in, each dimension more than 2% off fails. If it is empty, the add-on only warns when the largest side is under 1 cm or over 10 m. |
| **Check model** | Runs every rule of the chosen store on your scope. Your scene is not changed. Modifiers are evaluated in memory only. The model is read in glTF axes (Y up). |


### Results

- The header counts fails, warnings, manual items and passes.
- A banner gives the verdict, such as "Ready for Shopify" or "2 things to fix before Shopify accepts this model". Three outcomes: ready, ready with warnings, or things to fix.
- Rows are listed as Fail, Warn, Manual, Pass. Each row shows the rule, what was measured, the limit, and a short reason.
- **Select** (arrow icon): selects the objects, or the exact faces, behind the row. For example the n-gons, or the faces outside the 0 to 1 UV square.
- **Info** (i icon): opens the rule's official source page in your browser.
- **Show passed (n)**: shows or hides the rows that passed.
- **Manual rows** are tick boxes for things no script can judge. Tick them when you have checked by eye. The ticks are saved in the .blend file.

## 5. The rules, store by store

Each rule has a source and the date we checked it. Severity means:

- **Fail**: the store is likely to reject the file.
- **Warn**: the store may accept it, but you risk a slow load or a bad look.
- **Manual**: you check it by eye.

### Shopify (rules checked 2026-11-15)

Sources: Shopify's product media types page (https://help.shopify.com/en/manual/products/product-media/product-media-types) and its 3D model standards checklist (https://help.shopify.com/en/partners/resources/creating-3d-models/3d-model-standards-checklist).

| Rule | Severity | Limit | Source |
|---|---|---|---|
| File format | Fail | GLB or USDZ | Product media types |
| File size | Fail | Pass up to 4 MiB. Warn up to 15 MB. Fail above 500 MB. (Shopify auto-optimizes files over 15 MB.) | Product media types |
| One mesh | Warn | 1 mesh object | Standards checklist |
| One material | Warn | 1 material | Standards checklist |
| Real-world size | Fail | Within 2% of your Real size. Without it: warn if under 1 cm or over 10 m | Standards checklist |
| Transforms applied | Fail | Rotation 0, scale 1 on all objects | Standards checklist |
| Origin at the base | Fail | Base on the floor and centred, within 1 mm | Standards checklist |
| Texture size | Warn | Up to 2048 px (1024 px is shown as a tip) | Standards checklist |
| Texture format | Warn | JPG, unless the texture has transparency | Standards checklist |
| PBR material | Warn | Image textures only. Lists procedural nodes that will not export | Standards checklist |
| Packed ORM texture | Warn | Occlusion, roughness and metalness in one image | Standards checklist |
| One UV map | Warn | Exactly 1 UV map | Standards checklist |
| UVs inside 0 to 1 | Fail | All UVs in the square | Standards checklist |
| No overlapping UVs | Warn | Sampled on a 256 grid | Standards checklist |
| No n-gons | Fail | No face with more than 4 sides | Standards checklist |
| Clean edges | Warn | No open or tangled edges | Standards checklist |
| Normals face outward | Warn | No flipped normals | Our own check |
| No zero-area faces | Warn | None | Our own check |
| Edges bevelled | Manual | Tick when done | Standards checklist |
| UVs unwrapped by hand with natural seams | Manual | Tick when done | Standards checklist |
| No visible Z-fighting | Manual | Tick when done | Standards checklist |
| Colours match the product photos | Manual | Tick when done | Standards checklist |

### Amazon (rules checked 2026-11-16)

Source: Amazon Seller Central, 3D model technical requirements (https://sellercentral.amazon.com/help/hub/reference/external/G7RGSNQFZ2BAG7K3). The file size advice and the validator come from the Khronos glTF Validator page (https://github.khronos.org/glTF-Validator/).

| Rule | Severity | Limit |
|---|---|---|
| File format | Fail | GLB or glTF |
| Triangles | Fail | Up to 200,000 |
| Texture size | Fail | Square, power of two, 2048 to 4096 px |
| Texture format | Fail | PNG or JPG inside the file |
| PBR material | Fail | Every material has base colour and metallic-roughness (Principled BSDF) |
| No extras | Fail | No modifiers, animation, cameras or lights. Each is its own row |
| glTF extensions | Fail | Only KHR_materials_sheen, KHR_materials_transmission, KHR_materials_clearcoat, KHR_materials_ior, KHR_materials_volume, KHR_draco_mesh_compression, KHR_interactivity |
| Placement | Warn | On the floor and centred, within 1 mm. Wall and ceiling products differ |
| Single-sided materials | Warn | No double-sided materials |
| File size | Warn | Under 5 MB. This is advice from third parties, not Amazon's page |
| Run the Khronos glTF Validator | Manual | Tick when your file has no validator errors |

### Web glTF (rules checked 2026-11-06)

A generic profile for your own site or a model viewer. Sources: the Khronos glTF 2.0 specification (https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html) and, for the last two rules, Shopify's standards checklist.

| Rule | Severity | Limit |
|---|---|---|
| File format | Fail | GLB |
| File size | Warn | Under 5 MB |
| Texture size | Warn | Up to 2048 px |
| Draco compression | Warn | Mesh is Draco compressed |
| One material | Warn | 1 material |
| Origin at the base | Warn | Base on the floor and centred, within 1 mm |

Some rules are only fully measured on the exported file, such as file size, format and glTF extensions. In Blender, file size is shown as an estimate.


## 6. Files it reads

It reads your own scene and the image files your materials use, to measure their size and format. It never writes or changes files. Manual tick boxes and settings are saved inside your .blend file when you save.

## 7. Languages

The interface follows Blender's language: English, Spanish, German, French, Italian and Portuguese. To change it, go to **Edit > Preferences > Interface > Language**.

## 8. Privacy and Security

- It has no network code: no internet access, no licence key, no tracking, no accounts.
- It collects no personal data.
- The only links are the rule sources. They open in your own browser when you click the info icon.
- To report a vulnerability, read [SECURITY.md](../SECURITY.md).

## 9. FAQ

**Does it change my model?**
No. It only reads your scene. Modifiers are evaluated in memory.

**Does a PASS mean Shopify or Amazon will accept my file?**
No. Store rules change. We check the official pages every quarter, but the store's own review always decides.

**Why does it say my model is the wrong size?**
You entered a real size, and one side is more than 2% off. Check the units in your scene, or the real size you typed.

**Why is the origin a problem?**
In AR the product sits at the origin. If the base is above or below it, the product floats or sinks.

**Can I use it on a team or a client's computer?**
It is free software under the GPL-3.0-or-later licence. It needs no licence key and no network.

**Where do I get help?**
Open an issue at https://github.com/Facilo-es/shopready-check/issues.

## Licence

GPL-3.0-or-later. Publisher: Facilo (https://facilo.es). Source: https://github.com/Facilo-es/shopready-check.
