from ..utils.utils import scene_to_dict  # noqa pylint: disable=relative-beyond-top-level


def compare_exmls(path1, path2):

    # Take all the attribute data and throw it into two lists.
    data1 = scene_to_dict(path1)
    data2 = scene_to_dict(path2)
    # For now we'll do a lazy 1-1 comparison
    diff_data = list()
    for i in range(max(len(data1), len(data2))):
        if data1[i] != data2[i]:
            diff_data.append((i, data1[i], data2[i]))
    return diff_data
