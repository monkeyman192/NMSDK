# String structure for compatibility with exporting directly to mbins

null = chr(0)

class String():
    def __init__(self, string, length):
        self.size = length
        self.string = string
        
    def __str__(self):
        return self.string

    def __len__(self):
        return self.size

    def serialise(self, output, list_worker, move_end = False, return_data = False):
        # if this procedure is being called to retrive a serialised version of the data, simply return it
        if return_data:
            return self.string.ljust(self.size, null)
        else:
            # otherwise, proceed with the usual routine
            list_worker['curr'] += self.size
            if move_end:
                list_worker['end'] += self.size
            print(len(self.string.ljust(self.size, null)))
            output.write(self.string.ljust(self.size, null))
