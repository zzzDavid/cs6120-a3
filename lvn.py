"""Local Variable Numbering Pass
bril2json < *.bril | python lvn.py | bril2txt
bril2json < *.bril | python lvn.py | brili -p # profile dynamic instr count
"""
import sys
import json
from copy import copy
from basic_block import form_basic_blocks

class unique(object):
    num = 0
    def __init__(self):
        pass
    @classmethod
    def increase(cls):
        cls.num += 1
    @classmethod
    def get(cls):
        return cls.num

def is_overwritten(dest, instrs):
    for instr in instrs:
        if 'dest' not in instr: continue
        if instr['dest'] == dest:
            return True
    return False

def lvn(block, debug=False):
    new_block = list()

    # env: symbol name -> local value number
    env = dict() # str -> int
    # local value numbering table
    table = dict() # int -> {'value_tuple': tuple, 'cname': str}
    # list of value tuples for book-keeping
    tuples = list()

    for idx, instr in enumerate(block):
        old_name = None
        # skip the labels
        if 'op' not in instr: continue
        # Build value tuple
        if 'args' in instr:
            arg_nums = [env[arg_name] for arg_name in instr['args']]
            arg_nums.sort()
            value_tuple = (instr['op'], *arg_nums)
        else: # const instr
            value_tuple = (instr['op'], instr['value'])

        # re-generate the instr's argument
        if 'args' in instr:
            arg_numbers = [env[arg_name] for arg_name in instr['args']]
            instr['args'] = [table[number]['cname'] for number in arg_numbers]

        if value_tuple in tuples:
            # if the value is in the table (computed)
            # then we use the value
            num = tuples.index(value_tuple)
            opcode = table[num]['value_tuple'][0]
            if opcode == "const":
                # do const folding
                pass
            else:
                # replace the value with an id of the cached operator
                canonical_name = table[num]['cname']
                instr['op'] = 'id'
                instr['args'] = [canonical_name]
        elif instr['op'] == "id": # copying from a value
            id_operand_num = value_tuple[1] # copying from which value
            opcode = table[id_operand_num]['value_tuple'][0] # is it a const?
            if opcode == 'const': # const propagation
                instr['op'] = 'const'
                instr['value'] = table[num]['value_tuple'][1]
        else:
            # add an entry to the table
            tuples.append(value_tuple)
            num = len(tuples) - 1
            if 'dest' in instr:
                cname = instr['dest']
                # overwritten case
                """e.g.
                x = a + b
                # use x for some time
                x = c + d
                y = a + b # lvn will try to replace this with y = x, which is wrong
                The reason is that x as "canonical value" corresponds to both a+b and c+d
                value tuples. 
                """
                if idx + 1 < len(block) \
                    and is_overwritten(instr['dest'], block[idx+1:]):
                    cname = "lvn." + str(unique.get())
                    unique.increase()
                    # rename the destination
                    old_name = instr['dest']
                    instr['dest'] = cname
                
                # update the table
                table[num] = {'value_tuple': value_tuple, 'cname': cname}
        # update the env
        if 'dest' in instr:
            # if instr['op'] == 'id': # if the instr is an id
                # find the number of its id operand
                #num = tuples.index(value_tuple)
            if old_name is not None:
                env[old_name] = num
            else:
                env[instr['dest']] = num


        new_block.append(instr)
    return new_block

def main():
    prog = json.load(sys.stdin)
    for func in prog['functions']:
        new_blocks = list()
        for block in form_basic_blocks(func['instrs']):
            new_blocks.extend(lvn(block))
        func['instr'] = new_blocks
    print(json.dumps(prog))

if __name__ == "__main__":
    main()