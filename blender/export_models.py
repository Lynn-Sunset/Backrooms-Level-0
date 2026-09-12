"""Build the five interior assets using the shared PBR modeling pipeline.

Run: blender --background --factory-startup --python blender/export_models.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_assets import (build_pillar, build_light_panel, build_exit_door,
                          build_industrial_door, build_almond_water)

if __name__ == '__main__':
    for build in (build_pillar, build_light_panel, build_exit_door,
                  build_industrial_door, build_almond_water):
        build()
