# NMSDK Settings Panel

As part of the NMSDK plugin for blender, as settings panel available on the left-hand side of the screen is available in Object Mode.
This panel provides a number of functions which are useful in the import and export processes.

## Update Tools:

This section provides a button which, when pressed, will update an older format exportable scene to the newest format. This simply renames the main scene and makes a few other little changes that are easy enough to do yourself, but this button will make it easier!

## Scene Tools:

This section provides tool which can be used to modify the current scene. Currently the options are:

 - Collision visibility.
  This button toggles the visibility of collisions in the scene. This is useful for scenes with many collisions where you want to hide all of them to see the model more clearly.

## Default values:

A number of default values can be set. These are written to a `.json` file so that they are persistent across session.
These values are used for the export process and can be set manually there too, but if you are going to be exporting multiple files all in a separate group, it is useful to set the default value here to save yoruself time later.
The current default values that can be set are:

 - Export Directory:
  This is the directory that would be relative to the PCBANKS folder in the games' files where the model is to be exported to.
 - Group name:
  This is the name of the subfolder of the Export Directory where the scene and all other files will be written to. If this is empty it will default to the name of the scene.

The above two settings mean that your exported filepath will be `<Export Directory>/<Group Name>`.

## Animation controls:

This section provides a number of controls relating to animation playback and loading.
For models with less than 10 animations, all the animations will be loaded automatically unless the "Load all animations" import setting is unchecked.

When a model with animations is loaded the list of available animations to play will be displayed in a drop-down menu, with convenient 'Play', 'Pause' and 'Stop' buttons.
For models with extra animations to be loaded. A further drop-down menu is displayed which lists all the possible animations the scene contains and gives the option to load them one-by-one.
NMSDK has this behaviour due to the fact that for scene with large numbers of nodes and animations, it takes prohibitively long to import all the animations (not to mention the blend file will get very large!).

For models that are to be exported, this panel is useful for playing all the actions that are part of a single animation all at once, as well as being able to set the idle animation.
