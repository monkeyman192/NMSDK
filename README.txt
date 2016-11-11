NMS custom model importer pre-alpha
coded by monkeyman192 with inaluable help from gregkwaste

How to install:

- First, open the interactive python console in blender and enter:
 import os
 os.getcwd()
This will give you the current working directory (cwd) of blender. Place all files in this folder in that folder (or at least LOOKUPS.py, main.py and the classes folder)
- Next, open up blender with administrator rights (you will more than likely need admin rights to modify files in the blender cwd.)
- Select the model you want to export (blender script only supports a single model at the moment. This will be fixed probably tomorrow...)
- run the python script blender_script.py from within python.
- This will create a folder called TEST at the same location as your blender file. To change the name of this created folder you can change the first few options right at the bottom of the blender_script.py file

Currently not working:
- Textures. You can implement them yourself by editing the resultant material file if you want.
- blender_script.py is a bit broken. Don't think the actual verts and indexes are being done properly... :/