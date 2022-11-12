# start.py  (c)2022  Henrique Moreira

""" Start realestate configuration

It creates infrastructure at user home: .realestate.conf
"""

# pylint: disable=missing-function-docstring

import sys
import os
import tempfile

MY_START_DIR = os.path.realpath(os.path.dirname(__file__))
sys.path.append(os.path.join(MY_START_DIR, "sources", "jdb", "src", "packages"))

import jdba
from jdba.jbox import JBox

PRE_NAME = ".realestate.conf"

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
        dir_main_infos = param[0]
    else:
        dir_main_infos = ""
    opts = {
        "dir-main-infos": dir_main_infos,
        "~": None,
    }
    conf = first if first != "@" else os.path.join(home_dir(), PRE_NAME)
    return do_start(conf, opts)

def do_start(conf:str, opts) -> int:
    """ Main function. """
    if os.path.isfile(conf):
        print("Configuration exists already:", conf)
        son = JBox(name="config")
        son.load(conf)
        print(son)
        return 0
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
            key = input("Enter directory with main infos ... ")
            if os.path.isdir(key):
                break
            print("Please enter a valid dir.")
        dir_main_infos = key
    #print("# dir_main_infos:", dir_main_infos)
    opts["dir-main-infos"] = dir_main_infos
    opts["path-main-refs"] = dir_main_infos + "/" + "main_refs.json"
    son = JBox(opts, "config")
    son.save_stream(out)
    return 0, ""

def home_dir() -> str:
    return os.environ["USERPROFILE"] if os.name == "nt" else os.environ["HOME"]

# Main script
if __name__ == "__main__":
    main()
