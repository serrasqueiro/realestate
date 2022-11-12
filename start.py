# start.py  (c)2022  Henrique Moreira

""" Start realestate configuration

It creates infrastructure at user home: .realestate.conf
"""

# pylint: disable=missing-function-docstring

import sys
import os
import tempfile
import subprocess

MY_START_DIR = os.path.realpath(os.path.dirname(__file__))
sys.path.append(os.path.join(MY_START_DIR, "sources", "jdb", "src", "packages"))

import jdba
from jdba.jbox import JBox
from jdba.database import Database

PRE_NAME = ".realestate.conf"
GO_LATEST = True
SUBMODULES_UPDATE = False

TEMPL_MAIN = {
    "address": "me1",
    "refs": [
        {
            "Id": 1001,
            "Name": "1A",
        },
    ],
    "perm": [
        {
            "1A": 19.5,
        },
    ],
    "~": None,
}

def main():
    code = do_run(sys.argv[1:])
    if code is None:
        print(f"""Usage:
{__file__} [conf-path] [dir-main-infos]

If conf-path is '@', home directory will be adopted.

dir-main-infos is optional, if specified is the directory basename;
should be an absolute path.

Configuration filename is {PRE_NAME}
""")
    sys.exit(code if code else 0)

def do_run(args):
    param = args if args else ["@"]
    if len(param) > 2:
        print("Only up to two args expected!")
        return None
    first = param[0]
    if first in ("-h", "--help"):
        return None
    del param[0]
    if param:
        dir_main_infos = param[0].replace("\\", "/")
    else:
        dir_main_infos = ""
    opts = {
        "dir-main-infos": dir_main_infos,
        "dir-gd-refs": "",
        "go-latest": GO_LATEST,
        ""
        "~": None,
    }
    conf = first if first != "@" else os.path.join(home_dir(), PRE_NAME)
    code = do_start(conf, opts)
    if code <= -1:
        confbox = JBox("confjson")
        confbox.load(conf)
        opts = confbox.raw()
    elif code:
        return code
    print("==" * 20)
    code = go_ahead(opts)
    return code

def do_start(conf:str, opts) -> int:
    """ Main function. """
    if os.path.isfile(conf):
        print("Configuration exists already:", conf)
        son = JBox(name="config")
        son.load(conf)
        print(son)
        return -1
    print("Creating:", conf)
    fd_handle, tmp_f = tempfile.mkstemp()
    code, msg = config_creator(os.fdopen(fd_handle, "w"), opts)
    if code != 0:
        print(f"Bailing out (code={code}): {msg}")
        return code
    with open(tmp_f, "r") as fdin:
        data = fdin.read()
    with open(conf, "wb") as f_out:
        f_out.write(data.encode("ascii"))
    return 0

def config_creator(out, opts):
    """ Configuration creator. """
    dir_main_infos = opts["dir-main-infos"]
    if not dir_main_infos:
        while True:
            key = input("Enter directory with main infos ... ").strip()
            if os.path.isdir(key):
                break
            print("Please enter a valid dir.")
        dir_main_infos = key.replace("\\", "/")
    if not opts["dir-gd-refs"]:
        gdrefs = get_gd_refs_location().replace("\\", "/")
        opts["dir-gd-refs"] = gdrefs
        print(f"Copying {gdrefs}/*.json into {dir_main_infos}")
        dbin = Database(gdrefs, name="gd-input!", has_schema=False)
        assert dbin.basic_ok(), dbin.name
        for boxname in ("gd_refs",):
            path_in = dbin.path_refs()[boxname]
            path_out = os.path.join(dir_main_infos, f"{boxname}.json")
            jbx = JBox()
            print("Input:", path_in, "; output:", path_out)
            is_ok = jbx.load(path_in)
            if is_ok:
                is_ok = jbx.save(path_out)
                print(f"Copied to: {path_out}, ok? {is_ok}")
    #print("# dir_main_infos:", dir_main_infos)
    opts["dir-main-infos"] = dir_main_infos
    opts["path-main-refs"] = dir_main_infos + "/" + "main_refs.json"
    son = JBox(opts, "config")
    son.save_stream(out)
    return 0, ""

def go_ahead(opts) -> int:
    assert opts
    cmd = 'git submodule foreach --recursive "(git remote -v ; git checkout master)"'
    cmd2 = 'git submodule foreach --recursive git pull'
    w_else = ""
    if SUBMODULES_UPDATE:
        if os.getcwd() != MY_START_DIR:
            print("Please change directory to:", MY_START_DIR)
            return 3
        strs = run_cmd("git submodule update --init --recursive" + w_else)
        dump_joined(strs)
        if opts["go-latest"]:
            dump_joined(run_cmd(cmd))
            print("\nPulling from repos...")
            dump_joined(run_cmd(cmd2))
    code, msg = sampled_database(opts)
    if code:
        print(f"Error reading database, code={code}: {msg}")
    return code

def home_dir() -> str:
    return os.environ["USERPROFILE"] if os.name == "nt" else os.environ["HOME"]

def dump_joined(strs, ender="\n"):
    astr = '\n'.join(strs)
    if not astr:
        return 0
    print(astr, end=ender)
    return len(astr)

def run_cmd(cmd) -> list:
    pcs = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    print("Running:", cmd)
    btup = pcs.communicate()
    outp, a_stderr = btup
    if not outp:
        return []
    strs = outp.decode("ascii").splitlines()
    #print(f"::: stdout: {len(strs)}, stderr: {len(a_stderr) if a_stderr else 0}")
    if a_stderr:
        err_str = f"Something blurry: {[a_stderr]}"
        strs.append(err_str)
    return strs

def sampled_database(opts) -> tuple:
    where = opts["dir-main-infos"]
    dbx = Database(where)
    table_names = sorted(dbx.get_indexes()["tables"])
    print("Tables:", table_names)
    is_ok = dbx.valid_schema()  # this will create dlist indexes!
    if is_ok:
        print(dbx.name, "schema is valid!")
    assert is_ok, dbx.name
    jbx = dbx.table("main_refs")
    keying = sorted(jbx.dlist.index.byname)
    ptrs = jbx.dlist.index.byname["ptr"]
    aptr = sorted(ptrs)
    print(f"Keying: {keying}, byname ptr: {aptr}")
    ref_list = ptrs["Refs"]
    for idx, aref in enumerate(ref_list, 1):
        if "~" in aref:
            del aref["~"]
        an_id = aref["Id"]
        if an_id <= 0:
            break
        print(aref)
    return 0, ""

def get_gd_refs_location():
    jbx = JBox("gdrefs")
    while True:
        path = input("Enter gd_refs.json location ... ").strip()
        if not path:
            continue
        if os.path.isfile(path):
            is_ok = jbx.load(path)
            if is_ok:
                break
    dirname = os.path.realpath(os.path.dirname(path))
    fpath = os.path.join(dirname, "gd_refs.json")
    if os.path.isfile(fpath):
        print("gd_refs.json at:", dirname)
    else:
        print("Bogus gd_refs.json:", path)
    return dirname

# Main script
if __name__ == "__main__":
    main()
