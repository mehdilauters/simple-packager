#!/usr/bin/env python
import sys
import argparse
import tempfile
import os
import shutil
import tarfile
import json

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--package", help="package description")
    parser.add_argument("-c", "--create", help=" name of package: create package description")
    parser.add_argument("-output", "--output", help=" output name")
    
    return parser.parse_args()

class Package:
  def __init__(self, desc = None):
    self.desc = {
      'control': {
        'Package':'',
        'Source':'',
        'Version':'',
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
  
  def build(self,_out):
    basetmp = tempfile.mkdtemp()
    print basetmp
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
    
    for target in self.desc['data']:
        
      target_dir = data_path + os.path.normpath(target['target'])
      if not os.path.isdir(target['src']):
        self.mkdir_p(target_dir)
      else:
        if target.has_key('rename'):
          target_dir = os.path.join(target_dir, target['rename'])
        
      print '=>', target_dir
      out = None
      if os.path.isdir(target['src']):
        out = target_dir
        shutil.copytree(target['src'], out)
      else:
        target_file = os.path.join(target_dir,target['src'])
        if target.has_key('rename'):
          target_file = os.path.join(target_dir,target['rename'])
        out = target_file
        shutil.copyfile(target['src'], target_file)
      
      
      if target.has_key('rights'):
        os.system('chmod -R %s %s'%(target['rights'], out))
      if target.has_key('owner'):
        os.system('chown -R %s %s'%(target['owner'], out))
    
    os.system('dpkg-deb -b %s'%tmp)
    out = os.path.join(basetmp, self.desc['control']['Package']+'.deb')
    print out
    os.rename(out, _out)
    

if __name__ == '__main__':
  args = parse_args()
  
  if args.output is None:
    args.output = '/tmp/test.deb'
  
  if args.create is not None:
    p = Package()
    p.create(args.create)
    sys.exit(0)
  
  if args.package is not None:
    p = Package()
    p.load(args.package)
    p.build(args.output)
    sys.exit(0)