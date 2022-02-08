"""Local Variable Numbering Pass
bril2json < *.bril | python lvn.py | bril2txt
bril2json < *.bril | python lvn.py | brili -p # profile dynamic instr count
"""
import sys
import json
from copy import copy
from basic_block import form_basic_blocks

def lvn(block):
    new_block = copy(block)

    # env: symbol name -> local value number
    env = dict() # str -> int
    # local value numbering table
    table = dict() # int -> {'value_tuple': tuple, 'cname': str}
    # list of value tuples for book-keeping
    tuples = list()

    for instr in block:
        # skip the labels
        if 'op' not in instr: continue
        # Build value tuple
        arg_nums = [env[arg_name] for arg_name in instr['args']]
        arg_nums.sort()
        value_tuple = (instr['op'], *arg_nums)
        if value_tuple in tuples:
            # if the value is in the table (computed)
            # then we use the value
            num = tuples.index(value_tuple)
            opcode = table[num]['value_tuple'][0]
            if opcode == "const":
                # do constant propagation
                pass
            else:
                # replace the value with an id of the cached operator
                canonical_name = table[num]['cname']
                instr['op'] = 'id'
                instr['args'] = [canonical_name]
        else:
            # add an entry to the table
            tuples.append(value_tuple)
            num = len(tuples)
            cname = instr['dest']
            # overwritten case

            table[num] = {'value_tuple': value_tuple, 'cname': cname}
        # update the env
        env[instr['op']] = num

    return new_block

def main():
    prog = json.load(sys.stdin)
    for func in prog['functions']:
        new_blocks = list()
        for block in form_basic_blocks(func['instr']):
            new_blocks.append(lvn(block))
        func['instr'] = new_blocks
    print(json.dumps(prog))

if __name__ == "__main__":
    main()