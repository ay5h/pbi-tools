import os
from git import Repo
import zipfile as zf

def handle_request(r, allowed_codes=None):
    if not allowed_codes:
        allowed_codes = []  # Default to empty list

    if not r.ok:
        message = f'{r.status_code}: {r.text if r.text else "Unknown error"} when running {r.request.method} {r.url}'

        if r.status_code in allowed_codes:
            print(f"WARNING: {message}")
        else:
            raise SystemExit(f"ERROR {message}")

    return r.json() if r.content else None


def rebind_report(filepath, connection_string):
    """Repoint a PBIX file to use another model. Only works if the original file was pointed at a remote model when it was last saved (i.e. does not have an embedded model).

    **Warning**: This modifies the PBIX file by copying some content from another file. This is not supported by Microsoft and future updates to Power BI may cause this function to corrupt the file. **Never** use on a file which is not backed up.

    :param filepath: path to the PBIX file to modify
    :param connection_string: the connection string, extracted from another PBIX file
    """

    root, filename = os.path.split(filepath)
    base, ext = os.path.splitext(filename)
    temp_filepath = os.path.join(root, f"{base} Temp{ext}")

    with zf.ZipFile(filepath, "r") as original_zip:
        with zf.ZipFile(temp_filepath, "w", compression=zf.ZIP_DEFLATED) as new_zip:
            for f in original_zip.namelist():
                if f == "Connections":
                    new_zip.writestr(f, connection_string)
                elif f != "SecurityBindings":
                    new_zip.writestr(f, original_zip.read(f))

    os.remove(filepath)
    os.rename(temp_filepath, filepath)


def get_connection_string(filepath):
    """Returns the connection string component from a PBIX file. Only works if the original file was pointed at a remote model when it was last saved (i.e. does not have an embedded model).

    :param filepath: path to the PBIX file to read from
    """

    with zf.ZipFile(filepath, "r") as zip_file:
        for f in zip_file.namelist():
            if f == "Connections":
                return zip_file.read(f)


def check_file_modified(filepath):
    """Checks whether the given file was modified in the most recent commit. Only works if the file is within a git repo.

    :param filepath: path to the file being examined
    :return: a boolean indicating whether the file was modified in the most recent commit
    """

    repo = Repo(filepath, search_parent_directories=True)
    diff = repo.head.commit.diff("HEAD~1")
    filepath_end = filepath.replace("\\", "/").split("pbi/")[-1]

    return any(
        f.b_path.split("pbi/")[-1] == filepath_end and f.change_type in ["A", "M", "R"]
        for f in diff
    )


def open_branches():
    """Returns a list of open git branches. Only works if the current working directory is within a git repo.

    :return: an array of branch names
    """

    return [
        b.remote_head
        for b in Repo(
            os.path.abspath(__file__), search_parent_directories=True
        ).remotes.origin.refs
    ]
