"""Launch with python -m aero_psi serve (or index)."""
from .runtime import use_project_environment

use_project_environment()

from .backend import main

main()
