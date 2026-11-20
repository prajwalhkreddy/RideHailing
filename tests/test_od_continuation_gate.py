import contextlib,io,unittest
from scripts.continue_multi_episode_od import arguments
class ContinuationGateTests(unittest.TestCase):
 def test_explicit_authorization_required(self):
  with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):arguments(['--checkpoint','x','--output','y','--models','z'])
 def test_separate_output_arguments_required(self):
  with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):arguments(['--authorize-remaining-33'])
if __name__=='__main__':unittest.main()
