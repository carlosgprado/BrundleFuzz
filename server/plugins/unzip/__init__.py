#
# Unzip / Zip plugin.
#
# Use this if the file format consumed by your application is
# zipped (for example, DOCX or alike)
#
# NOTE: There is a reason why these formats are zipped.
# Usually they contain a whole directory structure. This plugin will
# extract the contents of a single file within it.
#
# At the very least two functions must be defined:
#
# - pre(buf)
#   Takes the raw file input and prepares it to be consumed by Cthulhu.
#
# - post(buf)
#   Takes the mutated data and prepares it to be written back to file
#

import StringIO
import zipfile
import random
from collections import namedtuple


def pre(raw_data):
    """
    This plugin extracts the contents of a random file
    within the original Zip file
    :param raw_data: file contents
    :return: Extracted data (str) and named tuple
    """

    # A file-like object is needed by ZipFile
    file_like_object = StringIO.StringIO(raw_data)
    zin = zipfile.ZipFile(file_like_object, mode = 'r')
    selected_filename = get_random_filename(zin.filelist)

    # I will need this later to restore the file
    DataToPost = namedtuple('DataToPost', 'zin extracted_file_name')
    data_to_post = DataToPost(zin = zin, extracted_file_name = selected_filename)
    data = zin.read(selected_filename)

    return data, data_to_post


def post(mutated_data, data_to_post):
    """
    This is rather tricky since it is not possible to
    delete or update a file within a Zip file in Python
    It is necessary to create a new ZipFile object
    Thanks StackOverflow ;)
    :param mutated_data: data mutated by Cthulhu
    :return: Zipped modified data (str)
    """
    zin = data_to_post.zin
    extracted_file_name = data_to_post.extracted_file_name
    
    file_like_object = StringIO.StringIO()

    zout = zipfile.ZipFile(file_like_object, mode = 'w')
    for item in zin.infolist():
        # Copy everything verbatim, except the mutated item
        if item.filename != extracted_file_name:
            zout.writestr(item, zin.read(item.filename))

    # Add the mutated item
    zout.writestr(extracted_file_name, mutated_data)

    # Cleanup
    zin.close()
    zout.close()

    return file_like_object.getvalue()


def get_random_filename(file_list):
    """
    Gets a random filename from inside the ZipFile object,
    with the selected file extension
    :return: arbitrary filename of selected type (extension)
    """
    file_extension = '.xml'
    filename_list = [x.filename for x in file_list if x.filename.endswith(file_extension)]
    rand_idx = random.randint(0, len(filename_list) - 1)

    return filename_list[rand_idx]
