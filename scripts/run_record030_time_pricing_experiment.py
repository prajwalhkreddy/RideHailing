"""Opt-in Option A comparison; no Record-029 sensitivity data are loaded."""
from pathlib import Path
import sys,json,time
from dataclasses import asdict
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.simulation.production import ProductionExperiment
from src.pricing.time_policy import TimePricingPolicy

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/analysis/2026-10-13_record030_time_pricing_experiment'

class ObservedExperiment(ProductionExperiment):
    def _build_report(self, timestamp, routing_source, requests, evaluations, result, before_weights, after_weights):
        report=super()._build_report(timestamp,routing_source,requests,evaluations,result,before_weights,after_weights)
        self.offered_fare_sum=sum(a.offered_fare for a in result.pricing_dispatch.request_audit)
        return report

def aggregate(frame, name, seed, part):
    n=int(frame.generated.sum());accepted=int(frame.accepted.sum());served=int(frame.served.sum())
    assert n==accepted+int(frame.rejected.sum())
    assert accepted==served+int(frame.accepted_unserved.sum())
    return dict(experiment=name,seed=seed,daypart=part,requested_trips=n,accepted_trips=accepted,rejected_trips=int(frame.rejected.sum()),accepted_unserved=int(frame.accepted_unserved.sum()),assigned_trips=served,completed_trips=None,acceptance_rate=accepted/n if n else None,completion_rate=None,assignment_rate=served/n if n else None,mean_offered_fare=float(frame.offered_fare_sum.sum())/n if n else None,total_revenue=float(frame.raw_served_revenue.sum()),driver_earnings=None,average_passenger_wait=None)

def main():
    config=json.loads((ROOT/'config/record030_time_pricing_experiment.json').read_text())
    overall=[];parts=[]
    for policy in config['policies']:
        name=policy['name'];start=time.perf_counter()
        model=ObservedExperiment(ROOT,seed=config['seed'],time_pricing_policy=TimePricingPolicy.from_config({k:v for k,v in policy.items() if k!='name'}))
        reports=[]
        for i in range(config['slots']):
            row=asdict(model.run_slot());row["offered_fare_sum"]=model.offered_fare_sum;reports.append(row)
            print(name,i+1,'slots',round(time.perf_counter()-start,1),'seconds',flush=True)
        f=pd.DataFrame(reports);hours=pd.to_datetime(f.timestamp).dt.hour
        overall.append(aggregate(f,name,config['seed'],'ALL'))
        for part,mask in [('DAYTIME',hours.between(8,19)),('OTHER',~hours.between(8,19))]:parts.append(aggregate(f[mask],name,config['seed'],part))
        for row in overall+parts:
            base=next(r for r in overall+parts if r['experiment']=='control' and r['daypart']==row['daypart'])
            for metric in ['accepted_trips','assigned_trips','mean_offered_fare','total_revenue']:
                row[metric+'_change']=row[metric]-base[metric]
                row[metric+'_change_pct']=100*(row[metric]-base[metric])/base[metric] if base[metric] else None
        pd.DataFrame(overall).to_csv(OUT/'pricing_experiment_summary.csv',index=False)
        pd.DataFrame(parts).to_csv(OUT/'pricing_experiment_daypart_summary.csv',index=False)
if __name__=='__main__':main()
