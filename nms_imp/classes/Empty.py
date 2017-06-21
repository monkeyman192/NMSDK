# Empty structure for compatibility with exporting directly to mbins

null = chr(0)

class Empty():
    def __init__(self, length):
        self.size = length

    def serialise(self, output, list_worker, move_end = False, return_data = False):
        output.write(null*self.size)
        list_worker['curr'] += self.size
        if move_end:
            list_worker['end'] += self.size

    def __str__(self):
        return '{0:#x} Padding'.format(self.size)
