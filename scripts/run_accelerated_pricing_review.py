import argparse
from src.simulation.accelerated_pricing_review import run
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--resume',action='store_true');a=p.parse_args();run(a.resume)
