import os
import json

def find_bundled_data():
    candidates=[]
    base_dirs=[os.getcwd(), os.path.dirname(__file__), os.path.dirname(os.path.abspath(__file__)), ".", "./ZSSKAPP"]
    try:
        from kivy.utils import platform
        if platform=='android':
            from android.storage import app_storage_path
            base_dirs.append(app_storage_path())
            base_dirs.append("/data/data/org.zssk.zsskzmeny/files/app")
    except: pass
    for bd in base_dirs:
        for name in ["data.json", "bbbbbb.json", "zssk_data.json", "bundle_data.json"]:
            p=os.path.join(bd, name)
            if os.path.exists(p) and os.path.isfile(p):
                candidates.append(p)
    seen=set(); uniq=[]
    for c in candidates:
        if c not in seen:
            seen.add(c); uniq.append(c)
    return uniq

def load_bundled_json_file(path):
    try:
        with open(path,'r',encoding='utf-8') as f:
            data=json.load(f)
        if isinstance(data,list):
            return {"shifts_data": data, "turnus": None, "source": path}
        elif isinstance(data,dict):
            shifts=data.get('shifts_data') or data.get('shifts') or data.get('data') or []
            turnus=data.get('turnus_data') or data.get('turnus') or data.get('turnus_profiles') or None
            if isinstance(turnus, dict) and 'profiles' in turnus:
                turnus_obj=turnus
            elif isinstance(turnus, list):
                turnus_obj={"active":"Import","profiles":{"Import":turnus}}
            else:
                turnus_obj=None
            return {"shifts_data": shifts, "turnus": turnus_obj, "employee": data.get('employee_info'), "source": path}
    except Exception as e:
        print(f"Chyba načítania bundled {path}: {e}")
    return None

def safe_read_any_path(path_or_uri):
    if not path_or_uri: raise Exception("Prázdna cesta")
    if str(path_or_uri).startswith("content://"):
        try:
            from jnius import autoclass
            PythonActivity=autoclass('org.kivy.android.PythonActivity')
            activity=PythonActivity.mActivity
            Uri=autoclass('android.net.Uri')
            uri=Uri.parse(path_or_uri)
            cr=activity.getContentResolver()
            istream=cr.openInputStream(uri)
            BufferedReader=autoclass('java.io.BufferedReader')
            InputStreamReader=autoclass('java.io.InputStreamReader')
            reader=BufferedReader(InputStreamReader(istream))
            sb=[]
            while True:
                line=reader.readLine()
                if line is None: break
                sb.append(str(line))
            reader.close()
            return "\n".join(sb)
        except Exception as e:
            raise Exception(f"Chyba čítania content:// URI: {e}")
    if os.path.isdir(path_or_uri):
        raise IsADirectoryError(f"Vybral si priečinok, nie súbor: {path_or_uri}")
    with open(path_or_uri,'r',encoding='utf-8') as f:
        return f.read()
