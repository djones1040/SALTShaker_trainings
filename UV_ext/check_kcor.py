import glob

with open('kcor_uvext.input','r') as f:
    lines_k = f.readlines()
kcor_list = []
for line in lines_k:
    if line.startswith('FILTER:'):
        kcor_list.append(line.split()[1])

files = glob.glob('final_lcs/*')
for fname in files:
    with open(fname,'r') as f:
        lines = f.readlines()
    for line in lines:
        if line.startswith('OBS:'):
            filt = line.split()[2]
            if filt not in kcor_list:
                print(fname,filt)
