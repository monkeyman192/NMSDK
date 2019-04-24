![NMSDK](docs/images/nmsdk_splash.png)

# NMS Custom Model Importer (NMSDK)
## Experimental branch

NMSDK is a blender plugin designed to allow the models to be added to No Man's Sky.

### Requirements:
 - Blender is a free, open-souce 3D modelling program which can be downloaded [here](https://www.blender.org/download/).
 - [MBINCompiler](https://github.com/monkeyman192/MBINCompiler) which is used to convert the *exml* files produced into *mbin* files the game can read.

### Installation:
The best way to install NMSDK is to clone the github repo using your favorite git client directly into the Blender addon cache, (generally) located at `C:\Users\<user name>\AppData\Roaming\Blender Foundation\Blender\2.78\scripts\addons`.
By cloning the repo into this folder any time there is an update you can simply pull the most recent branch and the plugin will automatically be updated in blender (you will need to close to have changes applied).
You also shouldn't need to actually install the plugin, it shoudl be visible in the list once the source code has been copied to the directory above.

 - First, ensure you also have a recent copy of [MBINCompiler](https://github.com/monkeyman192/MBINCompiler/releases) placed in the `NMSDK` folder.
 - Open Blender, then navigate to the Add-on settings (File > User Preferences). Select the option to "Install from File", and select the `NMSDK.py` file in the root blender directory.
 - You're done and can now start on importing a model into the game!
 
 ### Usage:
The first thing you should always do when adding a new model to the game is to create an empty node in blender at the origin called `NMS_SCENE`. It is this object that **everything you want imported into the game MUST be a child of**. This it to provide a reference point for all objects and to allow for NMSDK to construct the correct hierarchy of objects, as well as to allow for custom UI elements to be generated.

If you are familiar with the blender interface, you will notice that there are a number of extra panels under the `Object` properties. These panels are what allow you to customise your data and specify how they should be expected to behave in NMS.

For a far more detailed set of instructions, see the [documentation](/docs/NMSDK-tutorial.docx) (**Note: Currently outdated**)

#### Credits:
 - Primarily coded and maintained by monkeyman192.
 - All functionality for extracting data from blender provided by Gregkwaste.
 - Thanks to GmrLeon for their assistance in converting structs to python for the entity construction.
 - And Big thanks to MsrSgtShooterPerson for the fantastic banner!
