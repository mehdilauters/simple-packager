#!/usr/bin/env python
import errno
import subprocess
import sys
import argparse
import tempfile
import os
import shutil
import tarfile
import json
import glob

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--package", help="package description")
    parser.add_argument("-c", "--create", help=" name of package: create package description")
    parser.add_argument("-o", "--output", help=" output folder")
    parser.add_argument("-i", "--install", action="store_true", help=" install")
    parser.add_argument("-r", "--requirements", action="store_true", help="install dependencies")
    
    return parser.parse_args()

class Package:
  def __init__(self, desc = None):
    self.desc = {
      'control': {
        'Package':'',
        'Source':'',
        'Version':None,
        'Architecture':'',
        'Maintainer':'',
        'Depends': [],
        'Section':'',
        'Description':'',
        'postinst':None,
        'postrm':None,
        },
      'data' : []
      }
    if desc is not None:
      self.desc = desc
  
  def get_dependencies(self):
    return self.desc['control']['Depends']
  
  def install(self,_src, _target):
    self.desc['data'].append({
        'src':_src, 
       'target':_target
       })
  
  def create(self, _name):
    with open('%s.json'%_name, 'w') as f:
      self.desc['control']['Package'] = _name
      json.dump(self.desc, f)
  
  def load(self, _name):
    json_data=open(_name).read()
    self.desc = json.loads(json_data)
  
  def mkdir_p(self, path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
  
  def make_tarfile(self, output_filename, source_dir):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))
  
  def check_version(self):
    if self.desc['control']['Version'] is None:
      out = subprocess.check_output(["git", "describe", "--always"])
      version = out.strip()
      if not '.' in version:
        version = '0.0.0-%s'%version
      self.desc['control']['Version'] = version
  
  def build(self,_output):
    self.check_version()
    basetmp = tempfile.mkdtemp()
    tmp = os.path.join(basetmp, self.desc['control']['Package'])
    os.mkdir(tmp)
    
    
    ctrl_path = os.path.join(tmp,'DEBIAN')
    data_path = tmp
    
    os.mkdir(ctrl_path)
    if not os.path.isdir(data_path):
      os.mkdir(data_path)
    
    with open(os.path.join(ctrl_path, 'control'), 'w') as f:
      for k,v in self.desc['control'].iteritems():
        if k != 'postinst' and k != 'postrm' and k != 'Depends':
          f.write('%s: %s\n'%(k,v))
      f.write('Depends: %s\n\n'%', '.join(self.desc['control']['Depends']))
    
    if self.desc['control']['postinst'] is not None:
      postinst = os.path.join(ctrl_path, 'postinst')
      shutil.copyfile(self.desc['control']['postinst'], postinst)
      os.system('chmod 755 %s'%postinst)
    
    for target in self.desc['data']:
        
      target_dir = data_path + os.path.normpath(target['target'])
      if not os.path.isdir(target['src']):
        self.mkdir_p(target_dir)
      else:
        if target.has_key('rename'):
          target_dir = os.path.join(target_dir, target['rename'])
        
      out = None
      if os.path.isdir(target['src']):
        out = target_dir
        shutil.copytree(target['src'], out)
      else:
        for src in glob.glob(target['src']):
          target_file = os.path.join(target_dir,src)
          if target.has_key('rename'):
            target_file = os.path.join(target_dir,target['rename'])
          out = target_file
          shutil.copyfile(src, target_file)
      
      
      if target.has_key('rights'):
        os.system('fakeroot chmod -R %s %s'%(target['rights'], out))
      if target.has_key('owner'):
        os.system('fakeroot chown -R %s %s'%(target['owner'], out))
    
    os.system('fakeroot dpkg-deb -b %s >/dev/null'%tmp)
    out = os.path.join(basetmp, self.desc['control']['Package']+'.deb')
    fname = '%s-%s-%s.deb'%(self.desc['control']['Package'], self.desc['control']['Version'], self.desc['control']['Architecture'])
    shutil.move(out, fname)
    path = os.path.join(_output,fname)
    shutil.move(fname, path)
    return path
    

if __name__ == '__main__':
  args = parse_args()
  
  if args.output is None:
    args.output = './'
  
  if args.create is not None:
    p = Package()
    p.create(args.create)
    sys.exit(0)
    
  
  if args.package is not None:
    p = Package()
    p.load(args.package)
    
    if args.requirements:
      deps = p.get_dependencies()
      d = ' '.join(deps)
      os.system('sudo apt install %s'%d)
      sys.exit(0)
    
    
    
    path = p.build(args.output)
    print "%s generated"%path
    if args.install:
      print 'installing..'
      os.system('sudo dpkg -i %s'%path)
    sys.exit(0)