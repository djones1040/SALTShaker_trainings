import glob
import numpy as np

with open('kcor_uvext.input','r') as f:
    lines_k = f.readlines()
kcor_list = []
n=0
for line in lines_k:
    if line.startswith('FILTER:'):
        kcor_list.append(line.split()[1])
        n+=1
files = glob.glob('final_lcs/*')
kcor_list = np.array(kcor_list)
found = np.zeros(len(kcor_list))
for fname in files:
    with open(fname,'r') as f:
        lines = f.readlines()
    for line in lines:
        if line.startswith('OBS:'):
            filt = line.split()[2]
            if filt not in kcor_list:
                print(fname,filt)
            else:
                found[kcor_list==filt]+=1
print(n)
print(kcor_list[found==0])
