#
# Example plugin.
# You can use this as a template.
#
# At the very least two functions must be defined:
#
# - pre(buf)
#   Takes the raw file input and prepares it to be consumed by Cthulhu.
#
# - post(buf)
#   Takes the mutated data and prepares it to be written back to file
#


def pre(raw_data):
    """
    This example plugin does not really process the data.
    It just prints some debug message
    :param raw_data: file contents
    :return: unmodified data
    """
    print '> Preprocessing input...'

    return raw_data, ()


def post(mutated_data, data_to_post = None):
    """
    This example plugin does not really process the data.
    It just prints some debug message
    :param mutated_data: data mutated by Cthulhu
    :return: unmodified data
    """
    print '< Postprocessing input...'

    return mutated_data

