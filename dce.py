"""Dead code elimination pass
bril2json < *.bril | python dce.py | bril2txt
bril2json < *.bril | python dce.py | brili -p # profile dynamic instr count
"""
import json
import sys
import argparse
from copy import copy
from basic_block import form_basic_blocks

# Note: 
# - every instruction is a dict
# - you can delete dict in a list by list.remove(dict)

def dce(block, global_dce=False):
    # Candidate instr to remove
    # These are instrs that assigns to a variable
    # that are not used yet
    candidates = dict() # varaible -> the last instr 
    for instr in copy(block):
        # skip the labels
        if 'op' not in instr: continue
        # Check for usage
        if 'args' in instr: # if instr has args
            for arg in instr['args']: 
                if arg in candidates:
                    # var 'arg' is consumed
                    # so we remove it from candidates
                    candidates.pop(arg)
        # Check for def (assign)
        if 'dest' in instr: # if instr has destination
            if instr['dest'] in candidates and not global_dce:
                # the var is defined, and now redefining it
                instr_to_rm = candidates[instr['dest']]
                block.remove(instr_to_rm)
            # Update the latest definition
            candidates[instr['dest']] = instr
    # delete all unused instrs
    for _, instr in candidates.items():
        block.remove(instr)  
    return block  

def iterate_to_converge(block, global_dce):
    iter_num = 0
    while True: 
        old_len = len(block)
        new_block = dce(block, global_dce)
        new_len = len(new_block)
        iter_num += 1
        if old_len == new_len: break
        block = new_block
    return new_block

def main(global_dce=False):
    prog = json.load(sys.stdin)
    if global_dce:
        for func in prog['functions']:
            func['instrs'] = iterate_to_converge(func['instrs'], global_dce)
    else:
        for func in prog['functions']:
            blocks = form_basic_blocks(func['instrs'])
            new_blocks = list()
            for block in blocks:
                new_blocks.extend(iterate_to_converge(block, global_dce))
            func['instrs'] = new_blocks
    print(json.dumps(prog))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', dest='global_dce',
                        default=False, action='store_true',
                        help='global dce')

    args = parser.parse_args()
    global_dce = args.global_dce
    main(global_dce)