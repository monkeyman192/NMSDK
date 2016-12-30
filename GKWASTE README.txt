With the overhaul of how the nodes are all handeled, here are the details of how to call it from blender:

Firstly, all the different nodes are their own classes, subclassed from an Object class (that doesn't need to be worried about)

The classes are (with correct case):
Locator(Name, *Transform, *Attachment)
Mesh(Name, *Transform, Vertices, Indexes, Material, UVs, *Normals, *Tangents)
Collision(Name, *Transform, CType, **kwargs)
Model(Name, *Transform)
Reference(Name, *Transform, *Scenegraph)

At the moment Locator and Reference don't get their information from anywhere. If you have a way to give it to them their data (eg. a boolean value for locator to tell it whether it has an entity, and a path string for Reference to give it the path if we think this is the best way to do it) let me know and I can easily fix upi their structure to happily receive their data.

The first Object that needs to be made is the Model Object. Every other Object will be a child of this Object.
You add an Object as a child by calling the add_child(~) method on any of the Objects (it is a method on the Object class, so all the subclasses have it obviously)

Of all the parameters given, Name is the only required one. All the others have default values, but most of the time this value is undesirable or will lead to unexpected results.

Hopefully these changes won't affect your code too much and it will be easy to migrate it over. Let me know if you have any problems/questions.

I also changed it to delete all exml files and leave just the mbins for both size reasons and so that if you want an exml file you will need to decompile it from the mbin and then it will look nice.