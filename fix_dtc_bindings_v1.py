#!/usr/bin/env python3
from pathlib import Path
import difflib
import shutil
import sys
ROOT=Path('/root/kernel-source')
TARGET=ROOT/'work/kernel-4.9.205/android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15/scripts/Makefile.lib'
BACKUP=TARGET.with_name(TARGET.name+'.pre-fix-dtc-bindings-v1')
needle=' \t\t -I$(objtree)/include/\t\t\t\t\t \\\n'
insert='\n\t\t -I$(srctree)/include\t\t\t\t\t\t \\\n'
text=TARGET.read_text()
if '-I$(srctree)/include' in text or text.count(needle)!=1:
 print('ERROR: exact patch precondition failed',file=sys.stderr);sys.exit(1)
shutil.copy2(TARGET,BACKUP)
updated=text.replace(needle,needle+insert,1)
TARGET.write_text(updated)
if updated.count('-I$(srctree)/include')!=1:
 print('ERROR: validation failed',file=sys.stderr);shutil.copy2(BACKUP,TARGET);sys.exit(1)
print('BACKUP:',BACKUP);print(''.join(difflib.unified_diff(text.splitlines(True),updated.splitlines(True),fromfile=str(TARGET),tofile=str(TARGET))))
