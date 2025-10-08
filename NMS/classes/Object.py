# Primary Object class.
# Each object in blender will be passed into this class. Any children are added
# as child objects.

from typing import Optional

from serialization.NMS_Structures.Structures import TkSceneNodeAttributeData, TkSceneNodeData, TkTransformData
from .TkMaterialData import TkMaterialData
from .TkPhysicsComponentData import TkPhysicsComponentData
from .List import List
from collections import OrderedDict as odict

TYPES = ['MESH', 'LOCATOR', 'COLLISION', 'MODEL', 'REFERENCE']


def jenkins_one_at_a_time(data: str) -> int:
    # https://en.wikipedia.org/wiki/Jenkins_hash_function#one_at_a_time
    hash = 0
    for char in data.upper():
        hash = (hash + ord(char)) & 0xFFFFFFFF
        hash = (hash + (hash << 10)) & 0xFFFFFFFF
        hash = (hash ^ (hash >> 6)) & 0xFFFFFFFF
    hash = (hash + (hash << 3)) & 0xFFFFFFFF
    hash = (hash ^ (hash >> 11)) & 0xFFFFFFFF
    hash = (hash + (hash << 15)) & 0xFFFFFFFF
    return hash


class Object():
    """ Structure:
    TkSceneNodeData:
        Name
        Type
        Transform (TkTransformData)
        Attributes (List of TkSceneNodeAttributeData). The specific values in
        this will depend on the Type.
        Children (List of TkSceneNodeData)
    end
    """

    def __init__(self, Name: str, **kwargs):
        # This will be given as a TkTransformData object.
        # If this isn't specified the default value will be used.
        self.Transform = kwargs.get('Transform', TkTransformData())

        self.Attributes: list[TkSceneNodeAttributeData] = []

        # just a normal list so it is easier to iterate over
        self.Children: list['Object'] = []
        # set to None by default. Every child will have this set to something
        # when it is added as a child.
        self.Parent = None

        # whether or not something is a mesh. This will be modified when the
        # object is created if required.
        self.IsMesh = False

        self.NodeData = None

        # even though these are defined for all Object's, they will only be
        # populated for the Model
        # TODO: make this wayyyy nicer
        # this is a list of all the MESH objects or collisions of type MESH so
        # that we can easily access it.
        self.Meshes = odict()
        self.mesh_colls = odict()
        # The list will be automatically populated when a child is added to any
        # children of this object.
        self.ListOfEntities = []    # this works similarly to the above...

        self.Name = Name
        self._Type = ""

        self.ExtraEntityData = kwargs.get('ExtraEntityData', dict())

        # Get the original node data info
        orig_node_data = kwargs.get('orig_node_data', dict())
        # We nest the actual data under the key 'data' and keep the index also
        self.orig_node_data = orig_node_data.get('data', dict())
        self.orig_node_idx = orig_node_data.get('idx', 0)

        if isinstance(self.ExtraEntityData, str):
            self.EntityData = None
            # this will be the path or name of the file. If just name it will
            # need to be processed later...
            self.EntityPath = self.ExtraEntityData
            self._entity_path_is_abs = True
        else:
            try:
                self.EntityData = dict()
                # there should be only one key...
                entityname = list(self.ExtraEntityData.keys())[0]
                self.EntityPath = entityname
                # this can be populated with any extra stuff that needs to go
                # into the entity.
                self.EntityData[entityname] = List()
                for entity in self.ExtraEntityData[entityname]:
                    self.EntityData[entityname].append(entity)
            except IndexError:
                # in this case we are being passed an empty dictionary.
                # set the entity data to be None
                self.EntityData = None
                self.EntityPath = ''
            self._entity_path_is_abs = False

        # list of provided data streams (only applicable to Mesh type Objects)
        self.provided_streams = set()

    def give_parent(self, parent: 'Object'):
        self.Parent = parent

    def populate_meshlist(self, obj: 'Object'):
        # take the obj and pass it all the way up to the Model object and add
        # the object to it's list of meshes
        if self.Parent is not None:
            # in this case we are a child of something, so pass the object up
            # an order...
            self.Parent.populate_meshlist(obj)
        else:
            # ... until we hit the Model object who is the only object that has
            # no parent.
            if obj._Type == "COLLISION":
                self.mesh_colls[obj.Name] = obj
            else:
                self.Meshes[obj.Name] = obj
                if obj.Colours is not None:
                    self.has_vertex_colours = True

    def populate_entitylist(self, obj: 'Object'):
        if self.Parent is not None:
            self.Parent.populate_entitylist(obj)
        else:
            self.ListOfEntities.append(obj)

    def add_child(self, child: 'Object'):
        self.Children.append(child)
        child.give_parent(self)     # give the child it's parent
        if child.IsMesh:
            # if the child has mesh data, we want to pass the reference of the
            # object up to the Model object
            self.populate_meshlist(child)
        if child._Type == 'LOCATOR' or child._Type == 'MESH':
            self.populate_entitylist(child)

    def determine_included_streams(self):
        # this will search through the different possible streams and determine
        # which have been provided.
        # we will not include CHVerts as this will be given by default anyway
        # and we don't need to a semantic ID for it
        for name in ['Vertices', 'Indexes', 'UVs', 'Normals', 'Tangents',
                     'Colours']:
            if self.__dict__.get(name, None) is not None:
                self.provided_streams = self.provided_streams.union(
                    set([name]))

    def get_data(self) -> TkSceneNodeData:
        # returns the NodeData attribute
        return self.NodeData

    def construct_data(self):
        # iterate through all the children and create a TkSceneNode for every
        # child with the appropriate properties.

        # If we have been imported then we want to preserve the order of
        # nodes as they were in the original scene file.
        if self.was_imported:
            self.Children.sort(key=lambda x: x.orig_node_idx)
        # Call each child's process function
        child_nodes: list[TkSceneNodeData] = []
        for child in self.Children:
            child.construct_data()
            # this will return the self.NodeData object in the child Object
            child_nodes.append(child.get_data())
        self.NodeData = TkSceneNodeData(Name=self.Name,
                                        NameHash=self.NameHash,
                                        Type=self._Type,
                                        Transform=self.Transform,
                                        Attributes=self.Attributes,
                                        Children=child_nodes)

    def rebuild_entity(self):
        # this is used to rebuild the entity data in case something else is
        # added after the object is created
        if isinstance(self.ExtraEntityData, str):
            self.EntityData = self.ExtraEntityData
        else:
            self.EntityData = dict()
            # there should be only one key...
            entityname = list(self.ExtraEntityData.keys())[0]
            # this can be populated with any extra stuff that needs to go into
            # the entity.
            self.EntityData[entityname] = List(TkPhysicsComponentData())
            for entity in self.ExtraEntityData[entityname]:
                self.EntityData[entityname].append(entity)

    def original(
        self,
        name: str,
        fallback: str = "",
        ignore_original: bool = False
    ) -> Optional[str]:
        if ignore_original:
            return fallback
        attribs = self.orig_node_data.get('Attributes', [])
        for attr in attribs:
            if attr.get('Name', '') == name:
                return str(attr['Value'])
        return str(fallback)

    def original_attribute(self, name: str, ignore_original: bool = False) -> Optional[tuple]:
        """ Returns the value of an attibute from the original imported value,
        or None if there isn't a value. """
        # Create a short-cut in case we actually want to not use an original
        # value. We will use this when we want to re-export the geometry data
        # for an originally imported mesh.
        if ignore_original:
            return None
        attribs = self.orig_node_data.get('Attributes', [])
        for attr in attribs:
            if attr.get('Name', '') == name:
                return (attr['AltID'], attr['Value'])
        return None

    @property
    def was_imported(self) -> bool:
        """ Whether the scene the object belongs to was imported originally."""
        if self.Parent:
            return self.Parent.was_imported
        # Default to False. I don't think this should ever happen but it's
        # safer to do this in case it does.
        return False

    @property
    def NameHash(self) -> int:
        """ Returns the nameHash value for the object. """
        # If we have a name hash provided by imported data, use it:
        orig_name_hash = self.orig_node_data.get('NameHash', None)
        if orig_name_hash:
            return orig_name_hash
        return jenkins_one_at_a_time(self.Name)


class Locator(Object):
    def __init__(self, Name: str, **kwargs):
        super(Locator, self).__init__(Name, **kwargs)
        self._Type = "LOCATOR"
        self.HasAttachment = kwargs.get('HasAttachment', False)

    def create_attributes(self, data: dict, ignore_original: bool = False):
        if data is not None:
            self.Attributes = [
                TkSceneNodeAttributeData(
                    Name='ATTACHMENT', Value=str(data['ATTACHMENT'])
                )
            ]


class Light(Object):
    def __init__(self, Name: str, **kwargs):
        super(Light, self).__init__(Name, **kwargs)
        self._Type = "LIGHT"

        self.Intensity = kwargs.get('Intensity', 40000)
        self.Colour = kwargs.get('Colour', (1, 1, 1))
        self.FOV = kwargs.get('FOV', 360.0)

    def create_attributes(self, data: dict, ignore_original: bool = False):
        self.Attributes = [
            TkSceneNodeAttributeData(Name='FOV',
                                     Value=f'{self.FOV:.6f}'),
            TkSceneNodeAttributeData(Name='FALLOFF',
                                     Value='quadratic'),
            TkSceneNodeAttributeData(Name='FALLOFF_RATE',
                                     Value='2.000000'),
            TkSceneNodeAttributeData(Name='INTENSITY',
                                     Value=f'{self.Intensity:.6f}'),
            TkSceneNodeAttributeData(Name='COL_R',
                                     Value=f'{self.Colour[0]:.6f}'),
            TkSceneNodeAttributeData(Name='COL_G',
                                     Value=f'{self.Colour[1]:.6f}'),
            TkSceneNodeAttributeData(Name='COL_B',
                                     Value=f'{self.Colour[2]:.6f}'),
            # These two values will be hard-coded until they are understood
            # well enough to modify them to be anything other than their
            # default values.
            TkSceneNodeAttributeData(Name='COOKIE_IDX',
                                     Value='-1'),
            TkSceneNodeAttributeData(Name='VOLUMETRIC',
                                     Value='0.000000'),
            TkSceneNodeAttributeData(Name='MATERIAL',
                                     Value='MATERIALS/LIGHT.MATERIAL.MBIN')
        ]


class Joint(Object):
    def __init__(self, Name: str, **kwargs):
        super(Joint, self).__init__(Name, **kwargs)
        self._Type = "JOINT"
        self.JointIndex = kwargs.get("JointIndex", 1)

    def create_attributes(self, data: dict, ignore_original: bool = False):
        self.Attributes = [
            TkSceneNodeAttributeData(
                Name='JOINTINDEX',
                Value=str(self.original('JOINTINDEX', self.JointIndex)),
            )
        ]


class Emitter(Object):
    def __init__(self, Name: str, **kwargs):
        super(Emitter, self).__init__(Name, **kwargs)
        self._Type = "EMITTER"

    def create_attributes(self, data: dict, ignore_original: bool = False):
        if data is not None:
            self.Attributes = [
                TkSceneNodeAttributeData(Name='MATERIAL',
                                         Value=str(data['MATERIAL'])),
                TkSceneNodeAttributeData(Name='DATA', Value=str(data['DATA']))
            ]


class Mesh(Object):
    def __init__(self, Name: str, **kwargs):
        super(Mesh, self).__init__(Name, **kwargs)
        self._Type = "MESH"
        self.Vertices = kwargs.get('Vertices', None)
        self.Indexes = kwargs.get('Indexes', None)
        self.LodLevel = kwargs.get('LodLevel', 0)
        # This will be given as a TkMaterialData object or a string.
        self.Material = kwargs.get('Material', TkMaterialData(Name="EMPTY"))
        self.UVs = kwargs.get('UVs', None)
        self.Normals = kwargs.get('Normals', None)
        self.Tangents = kwargs.get('Tangents', None)
        self.CHVerts = kwargs.get('CHVerts', None)
        self.Colours = kwargs.get('Colours', None)
        self.np_indexes = kwargs.get('np_indexes', None)
        self.IsMesh = True
        # this will be a list of length 2 with each element being a 4-tuple.
        self.BBox = kwargs.get('BBox', None)
        self.HasAttachment = kwargs.get('HasAttachment', False)
        self.AnimData = kwargs.get('AnimData', None)    # the animation data

        # find out what streams have been provided
        self.determine_included_streams()

    def create_attributes(self, data: dict, ignore_original: bool = False):
        # data will be just the information required for the Attributes
        self.Attributes = [
            TkSceneNodeAttributeData(
                Name='BATCHSTARTPHYSI',
                Value=self.original('BATCHSTARTPHYSI', data['BATCHSTART'], ignore_original)
            ),
            TkSceneNodeAttributeData(
                Name='VERTRSTARTPHYSI',
                Value=self.original('VERTRSTARTPHYSI', data['VERTRSTART'], ignore_original)
            ),
            TkSceneNodeAttributeData(
                Name='VERTRENDPHYSICS',
                Value=self.original('VERTRENDPHYSICS', data['VERTREND'], ignore_original)
            ),
            TkSceneNodeAttributeData(
                Name='BATCHSTARTGRAPH',
                Value=self.original('BATCHSTARTGRAPH', 0, ignore_original)
            ),
            TkSceneNodeAttributeData(
                Name='BATCHCOUNT',
                Value=self.original('BATCHCOUNT', data['BATCHCOUNT'], ignore_original)
            ),
            TkSceneNodeAttributeData(
                Name='VERTRSTARTGRAPH',
                Value=self.original('VERTRSTARTGRAPH', 0, ignore_original)
            ),
            TkSceneNodeAttributeData(
                Name='VERTRENDGRAPHIC',
                Value=self.original(
                    'VERTRENDGRAPHIC',
                    data['VERTREND'] - data['VERTRSTART'],
                    ignore_original,
                )
            ),
            TkSceneNodeAttributeData(
                Name='FIRSTSKINMAT',
                Value=self.original('FIRSTSKINMAT', 0, ignore_original)
            ),
            TkSceneNodeAttributeData(
                Name='LASTSKINMAT',
                Value=self.original('LASTSKINMAT', 0, ignore_original)
            ),
            TkSceneNodeAttributeData(
                Name='LODLEVEL',
                Value=self.original('LODLEVEL', self.LodLevel, ignore_original)
            ),
            TkSceneNodeAttributeData(
                Name='BOUNDHULLST',
                Value=self.original('BOUNDHULLST', data.get('BOUNDHULLST', 0), ignore_original)
            ),
            TkSceneNodeAttributeData(
                Name='BOUNDHULLED',
                Value=self.original('BOUNDHULLED', data.get('BOUNDHULLED', 0), ignore_original)
            ),
            TkSceneNodeAttributeData(
                Name='AABBMINX',
                Value=self.original('AABBMINX', f"{data.get('AABBMINX', 0):.6f}", ignore_original)
            ),
            TkSceneNodeAttributeData(
                Name='AABBMINY',
                Value=self.original('AABBMINY', f"{data.get('AABBMINY', 0):.6f}", ignore_original)
            ),
            TkSceneNodeAttributeData(
                Name='AABBMINZ',
                Value=self.original('AABBMINZ', f"{data.get('AABBMINZ', 0):.6f}", ignore_original)
            ),
            TkSceneNodeAttributeData(
                Name='AABBMAXX',
                Value=self.original('AABBMAXX', f"{data.get('AABBMAXX', 0):.6f}", ignore_original)
            ),
            TkSceneNodeAttributeData(
                Name='AABBMAXY',
                Value=self.original('AABBMAXY', f"{data.get('AABBMAXY', 0):.6f}", ignore_original)
            ),
            TkSceneNodeAttributeData(
                Name='AABBMAXZ',
                Value=self.original('AABBMAXZ', f"{data.get('AABBMAXZ', 0):.6f}", ignore_original)
            ),
            TkSceneNodeAttributeData(
                Name='HASH',
                Value=self.original('HASH', data.get('HASH', "0"), ignore_original)
            ),
            TkSceneNodeAttributeData(
                Name='MATERIAL',
                Value=self.original('MATERIAL', data['MATERIAL'], ignore_original)
            ),
            TkSceneNodeAttributeData(
                Name='MESHLINK',
                Value=self.original('MESHLINK', self.Name + 'Shape', ignore_original)
            ),
        ]
        if self.HasAttachment:
            self.Attributes.append(
                TkSceneNodeAttributeData(Name='ATTACHMENT',
                                         Value=data['ATTACHMENT']))


class Collision(Object):
    def __init__(self, Name: str, **kwargs):
        super(Collision, self).__init__(Name, **kwargs)
        self._Type = "COLLISION"
        self.CType = kwargs.get("CollisionType", "Mesh")
        if self.CType == "Mesh":
            # We will only be passed the convex hull verts
            self.IsMesh = True
            self.Material = None
            self.Vertices = kwargs.get('Vertices', None)
            self.Indexes = kwargs.get('Indexes', None)
            self.Normals = kwargs.get('Normals', None)
            self.Tangents = kwargs.get('Tangents', None)
            self.CHVerts = kwargs.get('CHVerts', None)
            self.np_indexes = kwargs.get('np_indexes', None)
        else:
            # just give all 4 values. The required ones will be non-zero (deal
            # with later in the main file...)
            self.Width = kwargs.get('Width', 0)
            self.Height = kwargs.get('Height', 0)
            self.Depth = kwargs.get('Depth', 0)
            self.Radius = kwargs.get('Radius', 0)

    def create_attributes(self, data: dict, ignore_original: bool = False):
        self.Attributes = [TkSceneNodeAttributeData(Name="TYPE",
                                                    Value=self.CType)]
        if self.CType == 'Mesh':
            self.Attributes.append(
                TkSceneNodeAttributeData(
                    Name='BATCHSTART',
                    Value=self.original('BATCHSTART', data['BATCHSTART'])
                )
            )
            self.Attributes.append(
                TkSceneNodeAttributeData(
                    Name='BATCHCOUNT',
                    Value=self.original('BATCHCOUNT', data['BATCHCOUNT'])
                )
            )
            self.Attributes.append(
                TkSceneNodeAttributeData(
                    Name='VERTRSTART',
                    Value=self.original('VERTRSTART', data['VERTRSTART'])
                )
            )
            self.Attributes.append(
                TkSceneNodeAttributeData(
                    Name='VERTREND',
                    Value=self.original('VERTREND', data['VERTREND'])
                )
            )
            self.Attributes.append(
                TkSceneNodeAttributeData(
                    Name='FIRSTSKINMAT',
                    Value=self.original('FIRSTSKINMAT', "0")
                )
            )
            self.Attributes.append(
                TkSceneNodeAttributeData(
                    Name='LASTSKINMAT',
                    Value=self.original('LASTSKINMAT', "0")
                )
            )
            self.Attributes.append(
                TkSceneNodeAttributeData(
                    Name='BOUNDHULLST',
                    Value=self.original('BOUNDHULLST', data.get('BOUNDHULLST', "0"))
                )
            )
            self.Attributes.append(
                TkSceneNodeAttributeData(
                    Name='BOUNDHULLED',
                    Value=self.original('BOUNDHULLED', data.get('BOUNDHULLED', "0"))
                )
            )
        elif self.CType == 'Box':
            self.Attributes.append(
                TkSceneNodeAttributeData(
                    Name='WIDTH',
                    Value=f'{data["WIDTH"]:.06f}',
                )
            )
            self.Attributes.append(
                TkSceneNodeAttributeData(
                    Name='HEIGHT',
                    Value=f'{data["HEIGHT"]:.06f}',
                )
            )
            self.Attributes.append(
                TkSceneNodeAttributeData(
                    Name='DEPTH',
                    Value=f'{data["DEPTH"]:.06f}',
                )
            )
        elif self.CType == 'Sphere':
            self.Attributes.append(
                TkSceneNodeAttributeData(
                    Name='RADIUS',
                    Value=f'{data["RADIUS"]:.06f}',
                )
            )
        elif self.CType in ('Capsule', 'Cylinder'):
            self.Attributes.append(
                TkSceneNodeAttributeData(
                    Name='RADIUS',
                    Value=f'{data["RADIUS"]:.06f}',
                )
            )
            self.Attributes.append(
                TkSceneNodeAttributeData(
                    Name='HEIGHT',
                    Value=f'{data["HEIGHT"]:.06f}',
                )
            )


class Model(Object):
    def __init__(self, Name: str, **kwargs):
        super(Model, self).__init__(Name, **kwargs)
        self._Type = "MODEL"
        # Whether the object has vertex colour info
        self.has_vertex_colours = False
        self.lod_distances = kwargs.get('lod_distances', [])
        self._was_imported = self.orig_node_data != dict()

    def create_attributes(self, data: dict, ignore_original: bool = False):
        # Data will be just the information required for the Attributes.
        self.Attributes = [
            TkSceneNodeAttributeData(Name='GEOMETRY',
                                     Value=data['GEOMETRY'])
        ]
        # Add the LOD info
        for i, dist in enumerate(self.lod_distances):
            self.Attributes.append(
                TkSceneNodeAttributeData(Name=f'LODDIST{i + 1}', Value=dist)
            )
        self.Attributes.append(
            TkSceneNodeAttributeData(Name='NUMLODS',
                                     Value=len(self.lod_distances) + 1))

    def check_vert_colours(self):
        for mesh in self.Meshes.values():
            # Also, if an object has vertex colour data, the entire scene needs
            # to know so dummy data can be provided for every other mesh
            if mesh.Colours is not None:
                self.has_vertex_colours = True

    @property
    def was_imported(self) -> bool:
        return self._was_imported

    @was_imported.setter
    def was_imported(self, val: bool):
        self._was_imported = val


class Reference(Object):
    def __init__(self, Name: str, **kwargs):
        # this will need to recieve SCENEGRAPH as an argument to be used.
        # Hopefully this casn be given by blender? Maybe have the user enter it
        # in or select the path from a popup??
        super(Reference, self).__init__(Name, **kwargs)
        self._Type = "REFERENCE"

        self.Scenegraph = kwargs.get("Scenegraph",
                                     "Enter in the path of the SCENE.MBIN you "
                                     "want to reference here.")

    def create_attributes(self, data: dict, ignore_original: bool = False):
        self.Attributes = List(TkSceneNodeAttributeData(Name='SCENEGRAPH',
                                                        Value=self.Scenegraph))
