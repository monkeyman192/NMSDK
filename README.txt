NMS custom model importer pre-alpha
coded by monkeyman192 and gregkwaste

How to install:

- First, open the interactive python console in blender and enter:
 import os
 os.getcwd()
This will give you the current working directory (cwd) of blender. Place all files in this folder in that folder (or at least LOOKUPS.py, main.py and the classes folder)
- Next, open up blender with administrator rights (you will more than likely need admin rights to modify files in the blender cwd.)
- Select the model you want to export (blender script only supports a single model at the moment. This will be fixed probably tomorrow...)
- run the python script blender_script.py from within python.
- This will create a folder called TEST at the same location as your blender file. To change the name of this created folder you can change the first few options right at the bottom of the blender_script.py file

TODO:
create an entity file along side each object that is basically just empty. Or maybe ask if entity files are to be created. Maybe there is a thing in blender that could be selected to indicate an object needs an entity file?