import sys
from pathlib import Path

package_root = Path(__file__).parent.parent.resolve().as_posix()
sys.path.append(package_root)  # Allows importing modules from 'src/' as 'src.<module_name>...'.
