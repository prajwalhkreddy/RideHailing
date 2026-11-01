import argparse
from src.simulation.multiepisode_pricing import run_fixture,run_final
if __name__=='__main__':
 p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--protocol-fixture',action='store_true');g.add_argument('--launch',action='store_true');p.add_argument('--resume',action='store_true');a=p.parse_args()
 if a.protocol_fixture:
  if a.resume:p.error('Fixture reuses completed artifact automatically.')
  run_fixture()
 else:run_final(a.resume)
