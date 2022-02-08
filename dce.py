"""Dead code elimination pass
bril2json < *.bril | python dce.py | bril2txt
bril2json < *.bril | python dce.py | brili -p # profile dynamic instr count
"""
import json
import sys

from basic_block import form_basic_blocks

# Note: 
# - every instruction is a dict
# - you can delete dict in a list by list.remove(dict)

def local_dce(block):
    # Candidate instr to remove
    # These are instrs that assigns to a variable
    # that are not used yet
    candidates = dict() # varaible -> the last instr 
    for instr in block:
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
            if instr['dest'] in candidates:
                # the var is defined, and now redefining it
                instr_to_rm = candidates[instr['dest']]
                block.remove(instr_to_rm)
            # Update the latest definition
            candidates[instr['dest']] = instr
    # delete all unused instrs
    for k, instr in candidates.items():
        block.remove(instr)  
    return block  

def iterate_to_converge(block):
    iter_num = 0
    while True: 
        old_len = len(block)
        new_block = local_dce(block)
        new_len = len(new_block)
        iter_num += 1
        if old_len == new_len: break
        block = new_block
    return new_block

def main():
    prog = json.load(sys.stdin)
    for func in prog['functions']:
        blocks = form_basic_blocks(func['instrs'])
        for block in blocks:
            new_blocks = iterate_to_converge(block)
        func['instrs'] = new_blocks
    print(json.dumps(prog))

if __name__ == "__main__":
    main()