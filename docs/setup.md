## Installing NMSDK

Installing NMSDK is very easy. Head to the [NMSDK Release page](https://github.com/monkeyman192/NMSDK/releases) on GitHub and download the most recently released version.

If you have had a previous version of NMSDK installed it is recommended that you remove it.
Generally the addons will be installed at `%APPDATA%\Blender Foundation\Blender\2.80\scripts\addons`. If you go to this location and there is an `nmsdk` folder. Delete it after removing the addon from within blender, then follow the following steps.
Removing the old version is particularly important if you had a very old version (pre-proper versioning), as there have been many internal changes to NMSDK since then and the old files will clash, causing odd issues.

Open Blender and open the preferences window (`Edit` > `Preferences...`), and select `Install...` (it is at the top right of the window).
Select the `.zip` file you just downloaded and blender should install it without any errors.

To make exporting easier, NMSDK will automatically convert all produced `.exml` files to `.mbin` files. For this to work, *MBINCompiler* is required. See below for instructions on downloading and installing the latest version.

### Prerequisites

#### Blender

NMSDK requires a version of blender greater than or equal to 2.80.

#### MBINCompiler

For NMSDK to work, it requires [MBINCompiler](https://github.com/monkeyman192/MBINCompiler)
to generate the *.mbin* files that are read by the game.
The easiest way to have *MBINCompiler* set up is to download the most recent
release and register *MBINCompiler* to the path so that it can be picked up
anywhere by Blender.
The most recent release of *MBINCompiler* can be found on the [MBINCompiler releases](https://github.com/monkeyman192/MBINCompiler/releases) page.

For NMSDK to be able to use *MBINCompiler*, the program needs to be registered to the path so that it can be called from anywhere on your computer.
Open the folder containing the `MBINCompiler.exe` you just downloaded, open this folder in command line, then enter `MBINCompiler.exe register`.
This will add the folder the `.exe` is in to the system path, allowing NMSDK to be able to access the program from anywhere.
