import unittest,ast,tempfile,fcntl
from pathlib import Path
class ResumeTests(unittest.TestCase):
 def test_schedule_resumes_and_stops_25(self):
  tree=ast.parse(Path(__file__).with_name('resume_harness.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='schedule');ns={"CHECKPOINTS":(1,5,10,15,20,25),"traceback":__import__("traceback")};exec(compile(ast.Module(body=[fn],type_ignores=[]),'schedule','exec'),ns)
  episodes=[];checkpoints=[];evaluations=[];states=[]
  ns['schedule'](episodes.append,checkpoints.append,evaluations.append,lambda *x:states.append(x),start_episode=2)
  self.assertEqual(episodes,list(range(2,26)));self.assertEqual(checkpoints,[5,10,15,20,25]);self.assertEqual(evaluations,checkpoints);self.assertEqual(states[-1],('COMPLETED',25,None))
 def test_lock_excludes_second_writer(self):
  with tempfile.TemporaryDirectory() as d:
   with open(Path(d)/'lock','a+') as a,open(Path(d)/'lock','a+') as b:
    fcntl.flock(a,fcntl.LOCK_EX|fcntl.LOCK_NB)
    with self.assertRaises(BlockingIOError):fcntl.flock(b,fcntl.LOCK_EX|fcntl.LOCK_NB)
if __name__=='__main__':unittest.main()
