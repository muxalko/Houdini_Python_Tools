from collections import Counter
import os
import shutil
from pathlib import Path

# INIT VARIABLES
project_path = 'C:/Projects/MegaProject'
assets_path = 'C:/Assets/temp'

# counters
counter = Counter()

# TODO: proper logging
# log_file = Path(assets_path).joinpath(temp_folder).joinpath("FileOrganiizer.log")
# timestamp = time.strftime('%d.%m_%H:%M')

project_folder_structure = {
    "textures": {"folder": "tex", "filter": {".png", ".jpg"}},
    "materials": {"folder": "mat", "filter": {".mat"}},
    "models": {"folder": "models", "filter": {".obj", ".mtl", ".fbx"}},
    "scripts": {"folder": "scripts", "filter": {".c", ".py", ".txt"}},
}

project_assets_category = {
    "trees": {"tree", "oak", "pine", "log", "bark"},
    "rocks": {"rock", "cliff", "stone"},
    "vegetation": {"grass", "bush", "leave", "strand"},
    "vfx": {"fx", "effect", "particle", "explosion"},
}


# FUNCTIONS
def print_iter(object):
    # create an iterator object from that iterable
    iter_obj = object  #
    # infinite loop
    while True:
        try:
            # get the next item
            element = next(iter_obj)
            # do something with element

            if element.is_dir():
                print (element)
                files = [_path.suffix for _path in Path(element).glob('**/*') if _path.is_file() and _path.suffix]
                # print (files)
                data = Counter(files)
                print(data)

        except StopIteration:
            # if StopIteration is raised, break from loop
            break


def count_iter(object):
    # create an iterator object from that iterable
    iter_obj = object  #
    # infinite loop
    while True:
        try:
            # get the next item
            element = next(iter_obj)
            # do something with element

            if element.is_dir():
                print (element)
                categories = [_path for _path in Path(element).glob('**/*') if _path.is_file() and _path]
                for _asset in categories:
                    for category, values in project_assets_category.items():

                        for _value in values:
                            if _asset.match("*" + _value + "*"):
                                counter.update([_value])
                                print(str(_asset) + " --- Matched category: " + category + ", value: " + _value)

        except StopIteration:
            # if StopIteration is raised, break from loop
            break


def sort_iter(_object):
    print ("#################### START SORTING #########################")
    print ("Existing categories counter: " + str(counter))
    # create an iterator object from that iterable
    iter_obj = _object  #
    # infinite loop
    while True:
        try:
            # get the next item
            element = next(iter_obj)
            # do something with element

            if element.is_dir():
                # print (element)
                files = [_path for _path in Path(element).glob('**/*') if _path.is_file() and _path.suffix]
                # print (files)
                for _file in files:
                    # print ("FILE PROCESS - " + str(_file))
                    category_matched = ''
                    folder_matched = ''
                    filter_matched = ''
                    ext_matched = ''
                    for _key, _value in project_folder_structure.items():
                        for _filter in _value['filter']:
                            if _file.match("*" + _filter):
                                print("!!! Matched file - " + str(_file))
                                # print ("key: " + _key + ", value: " + str(_value))
                                print(" - filter: " + _filter)
                                for _category, _filters in project_assets_category.items():
                                    for _match in _filters:
                                        if _file.match("*" + _match + "*"):
                                            print(" - Matched category: " + _category + ", filters " + str(_filters))
                                            folder_matched = _value['folder']
                                            category_matched = _category
                                            filter_matched = _match;
                                            ext_matched = _filter
                                        # else:
                                        # print (" --- ERROR: Category Not Found! -  Category " + _category + ", filters " + str(_match))
                    if folder_matched and category_matched:
                        # Build custom path based on category
                        dst_path = Path(project_path) / folder_matched / category_matched / filter_matched
                        src_path = _file

                        # create missing folders
                        if not dst_path.is_dir():
                            try:
                                dst_path.mkdir(parents=True)
                            except OSError:
                                print ("Creation of the directory %s failed" % dst_path)
                            else:
                                print ("Successfully created the directory %s " % dst_path)

                        # create file name
                        # TODO 1: Find solution for multiple matches, when for example two or more filters match (ex. tree and rock in rocktree.fbx)
                        # TODO 2: Find solution for matching material map types: diffuse, normal,height etc...
                        # TODO 3: Find solution for matching separate items: for example when textures must match the model asset.
                        # TODO 4: Find a way to make file asset unique id, so there will be no duplicates when rerunning the script and still copies in the src folder

                        dst_path = Path(dst_path / filter_matched).with_name(
                            filter_matched + "_" + str(format(counter[filter_matched], '03d'))) \
                            .with_suffix(ext_matched)

                        # Move a file from the directory d1 to d2
                        print("DEBUG src(" + str(src_path) + "), dst(" + str(dst_path) + ")")
                        # os.rename(str(src_path), str(dst_path))
                        shutil.move(str(src_path), str(dst_path))
                        # src_path.rename(dst_path)

                        counter.update([filter_matched])

                        print ("FILE PROCESSED: " + str(
                            _file) + "\n + category_matched=" + category_matched + ",folder_matched=" + folder_matched)
                    else:
                        print ("FILE NOT PROCESSED: " + str(
                            _file) + "\n - category_matched=" + category_matched + ",folder_matched=" + folder_matched)
        except StopIteration:
            # if StopIteration is raised, break from loop
            break

    print ("#################### END SORTING #########################")


# PRINT EVERYTHING
print ("############ VARIABLES #############")
# detect the current working directory and print it
print ("The current working directory is %s" % Path.cwd())
print("=======================================")
print ("Our project_folder_structure:")
for key, value in project_folder_structure.items():
    print(key + " - " + str(value))
print("=======================================")

print ("Our project_assets_filters:")
for key, value in project_assets_category.items():
    print(key + " - " + str(value))
print("=======================================")

print ("Project Path Folder: %s" % project_path)
if any(Path(project_path).iterdir()):
    print(" counting the existing project items")
    print_iter(iter(Path(project_path).iterdir()))
    count_iter(iter(Path(project_path).iterdir()))
print (" ")

print ("############ PROJECT FOLDERS #############")
for item in project_folder_structure.itervalues():
    path = Path(project_path) / item['folder']
    if not path.is_dir():
        try:
            path.mkdir(parents=False)
        except OSError:
            print ("Creation of the directory %s failed" % path)
        else:
            print ("Successfully created the directory %s " % path)
    else:
        print (item['folder'] + " exists")

print ("############ ASSETS #############")
print ("Assets Path Folder: %s" % assets_path)
if any(Path(assets_path).iterdir()):
    print(" listing the existing assets items count by type:")
    print_iter(iter(Path(assets_path).iterdir()))
    sort_iter(iter(Path(assets_path).iterdir()))

print ("############ FINAL STATS #############")
print_iter(iter(Path(project_path).iterdir()))
print("=======================================")