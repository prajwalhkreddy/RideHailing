"""Resume deterministic real March 1–15 collection; no model training."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.simulation.routing_experience_generation import generate
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stop-after-slot',type=int,default=720)
    args=parser.parse_args()
    generate(ROOT,stop_after_slot=args.stop_after_slot)
