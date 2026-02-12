# String structure for compatibility with exporting directly to mbins

from struct import pack

null = chr(0)


class String():
    def __init__(self, string, length, endpadding=b'', fmt=None):
        self.size = length
        self.string = string
        self.endpadding = endpadding
        self.fmt = fmt

    def __str__(self):
        if self.fmt:
            return self.fmt.format(self.string)
        else:
            return str(self.string)

    def __len__(self):
        return self.size

    def __bytes__(self):
        if self.endpadding == b'':
            return pack('{}s'.format(self.size), self.string.encode('utf-8'))
        else:
            # assume it will be <string> b'' <endpadding> (up to size)
            s = pack('{}s'.format(len(self.string) + 1),
                     self.string.encode('utf-8'))
            pad_amount = self.size - len(self.string) - 1
            s.extend(pad_amount*self.endpadding)
            return s

    def serialize(self, output, list_worker, move_end=False,
                  return_data=False):
        # if this procedure is being called to retrive a serialized version of
        # the data, simply return it
        if return_data:
            return self.string.ljust(self.size, null)
        else:
            # otherwise, proceed with the usual routine
            list_worker['curr'] += self.size
            if move_end:
                list_worker['end'] += self.size
            output.write(self.string.ljust(self.size, null))
