# blender_lenticular
An add-on for Blender 4.2.0 + to generate and visually test lenticular ('3D') prints.

This add-on allows the user to automatically generate lenticular prints (those ribbed plastic-covered images that look different from different angles).

Upon installation, an n-menu sidebard called 'Lenticular' is added. The workflow from here is as follows:
 - Press 'Load images' to select two images of identical resolution.
 - Select a desired band width for the image to be divided into, and click 'Update banding pattern' to create the core image.
 - Use the bars underneath to select various properties of the lenticular lens, like the lens radius, lens thickness, and material IOR.
 - Press 'Create lens' to dploy the lens, automatically sized to the original image.

It's highly recommended to work form an empty scene, and not to manually change render settings, since refraction in EEVEE is a fragile state.
