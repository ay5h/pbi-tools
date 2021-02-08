import os
import zipfile as zf
from git import Repo

def handle_request(r, stop=True):
    if not r.ok:
        message = f'ERROR {r.status_code}: {r.text if r.text else "Unknown error"} when running {r.request.method} {r.url}'
        
        if stop: raise SystemExit(message)
        else: print(message)

    return r.json() if r.content else None

def rebind_report(filepath, connection_string):
    root, filename = os.path.split(filepath)
    base, ext = os.path.splitext(filename)
    temp_filepath = os.path.join(root, f'{base} Temp{ext}')

    with zf.ZipFile(filepath, 'r') as original_zip:
        with zf.ZipFile(temp_filepath, 'w', compression=zf.ZIP_DEFLATED) as new_zip:
            for f in original_zip.namelist():
                if f == 'Connections':
                    new_zip.writestr(f, connection_string)
                elif f != 'SecurityBindings':
                    new_zip.writestr(f, original_zip.read(f))
    
    os.remove(filepath)
    os.rename(temp_filepath, filepath)

def get_connection_string(filepath):
    with zf.ZipFile(filepath, 'r') as zip_file:
        for f in zip_file.namelist():
            if f == 'Connections':
                return zip_file.read(f)

def check_file_modified(filepath):
    repo = Repo(filepath, search_parent_directories=True)
    diff = repo.head.commit.diff('HEAD~1')
    filepath_end = filepath.replace('\\', '/').split('pbi/')[-1]
    
    return any(f.b_path.split('pbi/')[-1] == filepath_end and f.change_type in ['A', 'M', 'R'] for f in diff)

def open_branches():
    return [b.remote_head for b in Repo(os.path.abspath(__file__), search_parent_directories=True).remotes.origin.refs]