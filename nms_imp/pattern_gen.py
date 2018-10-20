# generator to yield the iterable passed to it in a patterned way


def patterned(lst, **kwargs):
    # this will return the values in the list in a patterned order
    # the generator will yield the pattern name, and the entry in the list
    patterns = dict()
    indexes = set()
    mapping = dict()
    for key in kwargs:
        patterns[key] = kwargs[key]
        for index in kwargs[key]:
            mapping[index] = key
        indexes.update(set(kwargs[key]))
    max_index = max(indexes)
    missing = set(range(max_index+1)) - indexes

    i = 0       # current index in list
    k = 0       # current sub-index
    while i < len(lst):
        try:
            yield mapping[k], lst[i]
        except:
            pass
        i += 1
        if k < max_index:
            k += 1
        else:
            k = 0
        

if __name__ == "__main__":
    for i, j in patterned([1,2,3,4,5,6,7,8,9,10,11,12], ptrn1=[0, 2, 4], ptrn2=[1]):
        print(i,j)
