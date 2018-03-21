#!/usr/bin/env python3
import argparse
from collections import Counter
import sys

def HEADER(text): return '\033[95m' + text + '\033[0m' 
def OKBLUE(text): return '\033[94m' + text + '\033[0m' 
def OKGREEN(text): return '\033[92m' + text + '\033[0m' 
def WARNING(text): return '\033[93m' + text + '\033[0m' 
def FAIL(text): return '\033[91m' + text + '\033[0m' 
def BOLD(text): return '\033[1m' + text + '\033[0m' 
def UNDERLINE(text): return '\033[4m' + text + '\033[0m' 

# For parsing
# ...Greenspun's Tenth Rule, or something like that...
currOpStr = ''

# Really, these are (always?) tied together, but we'll keep them separate for now
# We'll use them like stacks that we push the currently-parsed Op onto
surfaces = []
ops = []
recordType = '' # enum surface, op

# could do this with sets.Set, but eh
allOps = ['conv', 'sdp', 'pdp', 'cdp', 'rubik', 'bdma']

class Surface:
    def __init__(self, surfaceType):
        self.surfaceType = surfaceType

class Op:
    def __init__(self, opType):
        self.opType = opType

# initialize opcounters
# TODO remove this (deprecated... or will be)
ctr = Counter()
bdma_ctr = conv_ctr = pdp_ctr = cdp_ctr = rubik_ctr = sdp_ctr = 0


parser = argparse.ArgumentParser(description='Preprocess a screen log from an NVDLA run.')
parser.add_argument('filepath', type=str, nargs=None,
                    help='the input file to be processed')
#parser.add_argument('-s', '--strip', action='store_true', help='whether/not to strip blank lines')
args = parser.parse_args()


if __name__ == '__main__':
    lines = None
    with open(args.filepath, 'r') as f:
        lines = f.readlines()
    lines = [l for l in lines if l != '\n']
    print("%d lines parsed." % len(lines))

    # capture the ./nvdla_runtime command as the first line
    '''
    start_idx = 0
    for i, l in enumerate(lines):
        if './nvdla_runtime' in l:
            start_idx = i
            break
    '''
    # TODO assumes ./nvdla_runtime command spans 2 lines
    start_idx = lines.index('creating new runtime context...\n') - 2

    end_idx = lines.index('Test pass\n')
    lines = lines[start_idx:end_idx+1]

    for i, l in enumerate(lines):
        # TODO actually use regex
        if 'NVDLA FW ROI' in l:
            if '_surface_desc' in l:
                opStrBegin = l.index('_') + 1
                currOpStr = l[opStrBegin:opStrBegin+l[opStrBegin:].index('_')]
                #print(currOpStr)
                surfaces.append(Surface(currOpStr))
                recordType = 'surface'

            if '_op_desc' in l:
                opStrBegin = l.index('_') + 1
                currOpStr = l[opStrBegin:opStrBegin+l[opStrBegin:].index('_')]
                #print(currOpStr)
                ops.append(Op(currOpStr))
                recordType = 'op'

        if 'src_data' in l:
            srcSizeStr = lines[i+6].split()[-1]
            #print(srcSizeStr)
            surfaces[-1].srcDataSize = int(srcSizeStr)

        if 'weight_data' in l:
            weightSizeStr = lines[i+6].split()[-1]
            #print(srcSizeStr)
            surfaces[-1].weightDataSize = int(weightSizeStr)

        if 'dst_data' in l:
            dstSizeStr = lines[i+6].split()[-1]
            surfaces[-1].dstDataSize = int(dstSizeStr)



        # These just print out the lines
        '''
        if 'HWLs done' in l:
            sys.stdout.write(OKGREEN(l))
        elif '-1' in l:
            sys.stdout.write(OKBLUE(l))
        elif 'NVDLA FW ROI' in l and '_desc' in l:
            sys.stdout.write(FAIL(l))
            if 'bdma' in l:
                ctr['bdma'] += 1
            elif 'conv' in l:
                ctr['conv'] += 1
            elif 'pdp' in l:
                ctr['pdp'] += 1
            elif 'cdp' in l:
                ctr['cdp'] += 1
            elif 'rubik' in l:
                ctr['rubik'] += 1
            else:
                ctr['sdp'] += 1
        else:
            sys.stdout.write(l) # already includes newlines
        '''

for item in ctr:
    print('op %s performed %dX' %(item, ctr[item]/2))

for s in surfaces:
    surfStr = s.surfaceType + ' ' + str(s.srcDataSize)
    print(surfStr)

totalSrcData = sum(map(lambda s: s.srcDataSize if s.surfaceType == 'conv' else 0, surfaces))
totalWeightData = sum(map(lambda s: s.weightDataSize if s.surfaceType == 'conv' else 0, surfaces))
print("Total Source Data: " + str(totalSrcData))
print("Total Weight Data: " + str(totalWeightData))


print('-'*40)

for opType in allOps:
    totalSrcData = sum(map(lambda s: s.srcDataSize if s.surfaceType == opType else 0, surfaces))
    print(OKGREEN(opType + ' src data: ' + str(totalSrcData)))
    if opType == 'conv':
        totalWeightData = sum(map(lambda s: s.weightDataSize if s.surfaceType == 'conv' else 0, surfaces))
        print(OKBLUE(opType + ' weight data: ' + str(totalWeightData)))

for opType in allOps:
    totalDstData = sum(map(lambda s: s.dstDataSize if s.surfaceType == opType else 0, surfaces))
    print(FAIL(opType + ' dst data: ' + str(totalDstData)))
