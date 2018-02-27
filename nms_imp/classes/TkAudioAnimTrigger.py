# TkAudioAnimTrigger struct

from .Struct import Struct

STRUCTNAME = 'TkAudioAnimTrigger'

class TkAudioAnimTrigger(Struct):
    def __init__(self, **kwargs):
        super(TkAudioAnimTrigger, self).__init__()

        """ Contents of the struct """
        self.data['Sound'] = kwargs.get('Sound', '')
        self.data['Anim'] = kwargs.get('Anim', '')
        self.data['FrameStart'] = kwargs.get('FrameStart', 0)
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
