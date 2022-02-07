"""
bril2json < *.bril | python basic_block.py
"""

import json
import sys

TERMINATORS = ['jmp', 'ret', 'br']

def form_basic_blocks(instrs):
    """
    A generator that generates basic blocks from an input function region.
    """
    curr_block = []
    for instr in instrs:
        if 'op' in instr: # instr is a an actual instruction
            curr_block.append(instr)
            if instr['op'] in TERMINATORS:
                yield curr_block
                curr_block = []
        else: # instr is a label, label is the entry of basic block
            # the current basic block ends naturally 
            yield curr_block
            # We also want to include the label on the top of next block
            curr_block = [instr]
    # implicit return: no ret at the end of function
    yield curr_block
    

def main():
    prog = json.load(sys.stdin)
    for func in prog['functions']:
        blocks = form_basic_blocks(func['instrs'])
        for block in blocks:
            print(block)


if __name__ == "__main__":
    main()