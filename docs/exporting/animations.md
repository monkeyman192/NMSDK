# Exporting animated scenes

NMSDK is able to handle scene with animations, allowing your creations to be more than just static objects, but beautiful animated constructions!

## Adding animations

To ensure your animations are ready for export with NMSDK, you must ensure a few things.
(TODO: add...)

## Chosing an animation handler

For the game to know the details of the animation(s) you added, an attached entity file **MUST** be specified as an entity controller.

![anim controller](../../images/anim_controller.png)

It is important to note that only one associated entity file may be specified as an animation controller in each scene at a time. Specifying more that one will not raise an error, but instead, only the first will be used, and any others will be ignored.