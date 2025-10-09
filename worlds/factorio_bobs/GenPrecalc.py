import sys
from pathlib import Path

if __name__ == '__main__' and (__package__ is None or __package__ == ''):
    file = Path(__file__).resolve()
    parent, top = file.parent, file.parents[2]

    sys.path.append(str(top))
    try:
        sys.path.remove(str(parent))
    except ValueError: # Already removed
        pass

    import worlds.factorio_bobs
    __package__ = 'worlds.factorio_bobs'

import json

from .InternalItem import all_ingredients

def main():
    output = {}
    for name, item in all_ingredients.items():
        raw, best, tech, cat = item.eval()
        output[name] = {"raw_ingredients": {item.name: cost for item, cost in raw.items()},
                        "best_recipe": best.name if best else None,
                        "technologies": [technology.name for technology in tech],
                        "category": list(cat)}
    json.dump(output, open("data/precalc.json", "w"), indent=4, sort_keys=True)


if __name__ == '__main__':
    main()
