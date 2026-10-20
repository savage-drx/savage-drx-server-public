"""Pinned offline reproducible public-Game build; never install or deploy."""
import argparse,hashlib,json,os,shutil,subprocess,tarfile,tempfile
from pathlib import Path
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--source-archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 extension=Path(__file__).resolve().parent;manifest=json.loads((extension/'manifest.json').read_text())
 assert set(os.listdir('/sys/class/net'))=={'lo'},'Build must be run with networking disabled'
 assert sha(a.source_archive)==manifest['sourceArchiveSHA256'],'Wrong source archive'
 assert sha(extension/'public-core.patch')==manifest['patchSHA256'],'Patch changed'
 a.output.mkdir(parents=True,exist_ok=True);assert not list(a.output.iterdir()),'Use an empty output directory'
 report=dict(passed=False,installed=False,deployed=False)
 try:
  with tempfile.TemporaryDirectory(prefix='drx-public-notice-') as folder:
   source=Path(folder)/'source';source.mkdir();build=Path(folder)/'build'
   with tarfile.open(str(a.source_archive)) as archive:
    for member in archive.getmembers():
     assert not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
     assert member.isfile() or member.isdir()
    archive.extractall(str(source))
   env=dict(os.environ,SOURCE_DATE_EPOCH='1788723004')
   def run(label,args):
    with (a.output/(label+'.log')).open('wb') as log:subprocess.run(args,cwd=source,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=900)
   def configure(label):run(label,['cmake','-S',str(source),'-B',str(build),'-DBUILD_CLIENT=OFF','-DCMAKE_BUILD_TYPE=Release','-DDEPLOY=OFF'])
   configure('parent-configure');run('parent-build',['cmake','--build',str(build),'--target','game_dedicated','-j2'])
   game=build/'libs/libgame_dedicated.so';assert sha(game)==manifest['parentGameSHA256'],'Baseline not reproduced'
   shutil.copy2(game,a.output/'parent-game64.so')
   run('patch-check',['patch','--dry-run','--batch','-p1','-i',str(extension/'public-core.patch')])
   run('patch',['patch','--batch','--forward','-p1','-i',str(extension/'public-core.patch')])
   for rel,h in manifest['normalizedSourceSHA256'].items():
    assert hashlib.sha256((source/rel).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==h,rel
   run('tests',['python3',str(extension/'test.py'),'--source',str(source),'--output',str(a.output/'tests')])
   configure('candidate-configure');run('candidate-build',['cmake','--build',str(build),'--target','game_dedicated','-j2'])
   assert sha(game)==manifest['gameSHA256'],'Candidate hash mismatch'
   shutil.copy2(game,a.output/'game64.so');report.update(passed=True,parentByteIdentical=True,gameSHA256=sha(game))
 except Exception as error:
  import traceback
  report.update(error=repr(error),traceback=traceback.format_exc())
 (a.output/'BUILD-RESULT.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
 raise SystemExit(0 if report['passed'] else 1)
if __name__=='__main__':main()
