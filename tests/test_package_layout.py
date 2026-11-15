"""Guard project-relative resources after moving the backend into a package."""
import importlib
from pathlib import Path
import unittest

class PackageLayoutTests(unittest.TestCase):
    def test_project_paths_still_point_outside_package(self):
        root=Path(__file__).resolve().parents[1]
        for name in ('runtime','copilot','studio','archive','ingest','evidence','knowledge','investigation','research','discovery','observed'):
            self.assertEqual(importlib.import_module('aero_psi.'+name).ROOT,root,name)
        from aero_psi import backend
        self.assertEqual(backend.DEFAULT_CATALOG_PATH,root/'aero_psi_catalog.json')
        self.assertEqual(backend.DEFAULT_DATA_ROOT,root/'DATA')
        self.assertEqual(backend.DEFAULT_FRONTEND_DIR,root/'frontend')

    def test_backend_modules_import_under_package(self):
        root=Path(__file__).resolve().parents[1]
        for path in (root/'aero_psi').glob('*.py'):
            if path.stem not in ('__main__','__init__'):
                module=importlib.import_module('aero_psi.'+path.stem)
                self.assertEqual(Path(module.__file__).resolve(),path)
        self.assertFalse(list(root.glob('aero_psi_*.py')))
