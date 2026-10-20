"""Run the actual adapter and original client's CVar responder without networking."""
import argparse,json,re,subprocess
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 root=Path(__file__).resolve().parent;out=a.output;out.mkdir(parents=True,exist_ok=False)
 old=(a.source/'Game/cl_main.cpp').read_text();start=old.index('void\tCL_CvarAnswer(char *cvar)');end=old.index('\nint CheckMinimapPanel(',start)
 constant=re.search(r'^#define\s+CLIENT_CVARANSWER\s+"[^"]+"',(a.source/'Game/game.h').read_text(),re.M).group(0)
 (out/'old_client_answer.cpp').write_text(constant+'\n'+old[start:end])
 report=dict(passed=False,http='mocked libcurl',cases=[])
 try:
  for label,flags in [('normal',[]),('asan',['-fsanitize=address','-fno-omit-frame-pointer']),('ubsan',['-fsanitize=undefined','-fno-sanitize-recover=all'])]:
   exe=out/label
   with (out/(label+'-build.log')).open('wb') as log:
    subprocess.run(['g++','-std=c++11','-O1','-g','-pthread','-DDEDICATED_SERVER','-I'+str(a.source/'Game'),'-I'+str(out),*flags,str(root/'adapter_test.cpp'),'-o',str(exe)],stdout=log,stderr=subprocess.STDOUT,check=True)
   run=subprocess.run([str(exe)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=30)
   (out/(label+'.log')).write_text(run.stdout);assert not run.returncode,run.stdout
   report['cases'].append(dict(mode=label,checks=int(re.search(r'PASS (\d+)',run.stdout)[1])))
  subprocess.run(['g++','-std=c++11','-Wall','-Wextra','-Werror','-pedantic','-I'+str(a.source/'Game'),str(root/'policy_test.cpp'),'-o',str(out/'policy')],check=True)
  subprocess.run([str(out/'policy')],check=True)
  report.update(passed=True,portablePolicy=True)
 except Exception as error:report['error']=repr(error)
 (out/'RESULT.json').write_text(json.dumps(report,indent=2));assert report['passed'],report
if __name__=='__main__':main()
