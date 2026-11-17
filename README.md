# ShopReady Check

Find out what an online store will say about your 3D product model before you upload it.

ShopReady Check is a Blender add-on. It reads your model and tests it against the published 3D rules of Shopify and Amazon, and against a general web glTF profile. For each rule it shows what it measured, the limit, and why the rule exists, with a link to the store's own page and the date we checked it.

## What makes it different

General mesh checkers tell you about geometry. ShopReady Check tells you what a specific store asks for: Shopify's one mesh and one material, Amazon's 200,000 triangle limit and 2K to 4K square textures, allowed glTF extensions, texture size and format, PBR texture setup, real-world size and where the base sits. Every rule cites its source.

## Install

1. Download `shopready_check-<version>.zip` from the [latest release](https://github.com/Facilo-es/shopready-check/releases/latest). Do not unzip it.
2. In Blender, open **Edit > Preferences > Get Extensions**.
3. Open the dropdown at the top right and choose **Install from Disk**, then pick the zip.
4. In the 3D Viewport, press **N** and click the **ShopReady** tab.

## Use it

1. Select your product.
2. Pick a store: Shopify, Amazon or Web glTF.
3. Optional: type the real size in centimetres.
4. Click **Check model** and read the results: Fail, Warn, Manual or Pass.

A **Select** button on a result selects the objects or faces at fault. Manual items are tick boxes saved in the .blend file. The add-on only reads your scene; it never changes it.

Full guide: [docs/guide.md](docs/guide.md).

## Good to know

- Blender 4.2 LTS and newer, including 5.x.
- Interface in English, Spanish, German, French, Italian and Portuguese.
- No network code: no internet access, no tracking, no accounts, no licence key.
- Store rules change. We check the official pages every quarter, but the store's own review always decides.

Shopify and Amazon are trademarks of their owners. ShopReady Check is not affiliated with or endorsed by them.

How it's made: Facilo builds its tools with AI coding assistants. Every release is tested automatically on Blender 4.2 LTS and 5.3 and on real sample product models, and every test export is checked with the Khronos glTF validator.

## Help

Open an issue: https://github.com/Facilo-es/shopready-check/issues. Security reports: [SECURITY.md](SECURITY.md).

## Licence

GPL-3.0-or-later. Publisher: Facilo (https://facilo.es).
