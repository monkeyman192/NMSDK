### Creating a procedurally generate-able scene

Creating procedurally generated scenes using NMSDK is simple.
For every scene (Ie. `Reference` node which has no *Reference Path* property set), you can specify that a scene is proc-gen by setting the *Is a proc-gen scene?* property to `True`.

Once this property has been set, a new panel will appear with [descriptor settings](./node_docs.md#descriptor-node)

For nodes that you wish to always appear, you can leave *Proc type* as `Always` and ignore the *Proc prefix* value

![desc_always](/../../images/desc_always.png)

If you wish for a node to be selected from a set, select the *Proc type* `Random` and specify the prefix in *Proc prefix*. All objects with the same *Proc prefix* value will form a pool from which objects are to be selected from. Note that if an object is not selected, none of its children will be either.

![desc_random](/../../images/desc_random.png)

In the above example, we have `NMS_CONSTRUCTBIGGUNGUN` and `ref_mount` with *Proc type* as `Always`, meaning they will always appear in the scene. The 5 `NMS_LIGHTSPRITE` instances all have *Proc type* as `Random` and *Proc prefix* as `LIGHT`, meaning in the final scene, only one of them will appear randomly. Their final node names in the produced scene will also be `_LIGHT_LIGHTSPRITE`.

#### Tips and things to note:

- Only nodes with the same parent will create a well-formed proc-gen scene. If you have two nodes with the same *Proc prefix* and different parents, they are not part of the same selection pool
- You should avoid giving a child of an object the same *Proc prefix* as its parent. You might make blender implode (or crash, I don't know...)
- If you are particularly diligent you can add the *Proc prefix* to the name of the node in blender. As long as you have the same *Proc prefix* in the descriptor panel it will still work fine. Eg. Node name = `_GRP_MOUNT`, and *Proc prefix* = `GRP` will work fine and it will allow you to see what is grouped together without having to click on the object.