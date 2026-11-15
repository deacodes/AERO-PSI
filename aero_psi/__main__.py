"""Launch with python -m aero_psi serve (or index)."""
from .runtime import use_project_environment

use_project_environment()

from .runtime_data import initialize
initialize()

from .backend import main

main()
