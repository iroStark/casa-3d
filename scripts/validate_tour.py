"""Valida o percurso: blender -b blender/casa.blend -P scripts/validate_tour.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import casa.tour as tour
probs = tour.validate()
print("PROBLEMAS", len(probs))
last = None
for p in probs:
    key = (p[1], p[2])
    if key != last:
        print("  ", p)
    last = key
