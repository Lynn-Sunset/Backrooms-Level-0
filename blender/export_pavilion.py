"""Build the detailed timber-and-stone pavilion.

Run: blender --background --factory-startup --python blender/export_pavilion.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pavilion_asset import build_pavilion

if __name__ == '__main__':
    build_pavilion()
