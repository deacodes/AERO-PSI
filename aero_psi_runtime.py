"""Local runtime selection and capability checks; never installs packages at request time."""
from pathlib import Path
import importlib.util
import os
import sys

ROOT = Path(__file__).resolve().parent


class RuntimeDependencyError(RuntimeError):
    pass


def use_project_environment():
    """CLI launches use the configured project environment when one exists."""
    environment = ROOT / '.venv'
    executable = environment / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if executable.is_file() and Path(sys.prefix).resolve() != environment.resolve():
        os.execv(str(executable), [str(executable), str(ROOT/'aero_psi_backend.py'), *sys.argv[1:]])


def capabilities():
    def installed(module):
        try: return importlib.util.find_spec(module) is not None
        except (ImportError, ValueError): return False
    return {'project_environment':Path(sys.prefix).resolve()==(ROOT/'.venv').resolve(),
            'scattering':{'mie':installed('miepython') and installed('numpy'),'rayleigh':True},
            'vertex_sdk':installed('google.genai')}
