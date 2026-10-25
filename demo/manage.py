#!/usr/bin/env python
import os
import sys
from pathlib import Path

if __name__ == '__main__':
    # Make the repository importable, for both sorl and demo
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'demo.settings.pil')
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
