"""Local Variable Numbering Pass
bril2json < *.bril | python lvn.py | bril2txt
bril2json < *.bril | python lvn.py | brili -p # profile dynamic instr count
"""
import sys
import json
from basic_block import form_basic_blocks

def str2bool(boolean):
    if boolean:
        return 'true'
    else:
        return 'false'

def compute(instr, env, tuples, table):
    """Try to compute the instruction,
    If computable, return a constant instr,
    else return the original instr. 
    """
    # skip instr without dest
    # nothing to compute for them
    if 'dest' not in instr or 'op' not in instr:
        return instr

    # Build value tuple
    all_const_operands = False
    any_const_operands = False
    args_identical = False
    if 'args' in instr:
        if all(item in env for item in instr['args']):
            if instr['op'] == 'id':
                # let const propagation handle id
                # we skip them here
                return instr
            arg_nums = [env[arg_name] for arg_name in instr['args']]
            arg_nums.sort()
            # Are all operands constant?
            const_operands = [tuples[num][0] == 'const' for num in arg_nums]
            all_const_operands = all(const_operands)
            any_const_operands = any(const_operands)
        else: # func args
            arg_nums = instr['args']
            # Are operands identical?
            args_identical = len(set(arg_nums)) == 1
            # Any operands constant?
            local_args = [env[arg_name] for arg_name in instr['args'] if arg_name in env]
            any_const_operands = any([tuples[num][0] == 'const' for num in local_args])

    else: # const instr
        return instr
    # print(instr)
    # print(const_operands)
    # print(any_const_operands)
    # print("\n")
    op = instr['op']
    const_instr = {'op':'const', 'dest':instr['dest']}
    if all_const_operands: # let's do computation!
        # first, get those const args
        args = [tuples[num][1] for num in arg_nums]
        if op == 'ne':
            value = str2bool(args[0] != args[1])
            const_instr['value'] = value
            const_instr['type'] = 'bool'
            return const_instr
        elif op == 'eq':
            value = str2bool(args[0] == args[1])
            const_instr['value'] = value
            const_instr['type'] = 'bool'
            return const_instr
        elif op == 'le':
            value = str2bool(args[0] <= args[1])
            const_instr['value'] = value
            const_instr['type'] = 'bool'
            return const_instr
        elif op == 'lt':
            value = str2bool(args[0] < args[1])
            const_instr['value'] = value
            const_instr['type'] = 'bool'
            return const_instr
        elif op == 'gt':
            value = str2bool(args[0] > args[1])
            const_instr['value'] = value
            const_instr['type'] = 'bool'
            return const_instr
        elif op == 'ge':
            value = str2bool(args[0] >= args[1])
            const_instr['value'] = value
            const_instr['type'] = 'bool'
            return const_instr
        elif op == 'not':
            value = str2bool(not args[0])
            const_instr['value'] = value
            const_instr['type'] = 'bool'
            return const_instr
        elif op == 'and':
            value = str2bool(args[0] and args[1])
            const_instr['value'] = value
            const_instr['type'] = 'bool'
            return const_instr
        elif op == 'or':
            value = str2bool(args[0] or args[1])
            const_instr['value'] = value
            const_instr['type'] = 'bool'
            return const_instr
        elif op == 'add':
            value = args[0] + args[1]
            const_instr['value'] = value
            const_instr['type'] = 'int'
            return const_instr
        elif op == 'mul':
            value = args[0] * args[1]
            const_instr['value'] = value
            const_instr['type'] = 'int'
            return const_instr
        elif op == 'sub':
            value = args[0] - args[1]
            const_instr['value'] = value
            const_instr['type'] = 'int'
            return const_instr
        elif op == 'div':
            value = args[0] / args[1]
            const_instr['value'] = value
            const_instr['type'] = 'int'
            return const_instr
    elif any_const_operands:
        if op == 'and': # and false any = true
            for arg_name in instr['args']:
                if arg_name not in env: continue
                value = tuples[env[arg_name]][1]
                if value == False:
                    value = str2bool(False)
                    const_instr['value'] = value
                    const_instr['type'] = 'bool'
                    return const_instr
        elif op == 'or': # or true any = false
            for arg_name in instr['args']:
                if arg_name not in env: continue
                value = tuples[env[arg_name]][1]
                if value == True:
                    value = str2bool(True)
                    const_instr['value'] = value
                    const_instr['type'] = 'bool'
                    return const_instr
    elif args_identical:
        if op == 'ne':
            value = str2bool(False)
            const_instr['value'] = value
            const_instr['type'] = 'bool'
            return const_instr
        elif op == 'eq':
            value = str2bool(True)
            const_instr['value'] = value
            const_instr['type'] = 'bool'
            return const_instr
        elif op == 'le':
            value = str2bool(True)
            const_instr['value'] = value
            const_instr['type'] = 'bool'
            return const_instr
        elif op == 'lt':
            value = str2bool(False)
            const_instr['value'] = value
            const_instr['type'] = 'bool'
            return const_instr
        elif op == 'gt':
            value = str2bool(False)
            const_instr['value'] = value
            const_instr['type'] = 'bool'
            return const_instr
        elif op == 'ge':
            value = str2bool(True)
            const_instr['value'] = value
            const_instr['type'] = 'bool'
            return const_instr

    return instr

class unique(object):
    """Provides unique value id
    """
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

        # try compute the instr for constant folding
        instr = compute(instr, env, tuples, table)

        # skip the labels
        if 'op' not in instr: continue
        # Build value tuple
        if 'args' in instr:
            if all(item in env for item in instr['args']):
                arg_nums = [env[arg_name] for arg_name in instr['args']]
                arg_nums.sort()
                value_tuple = (instr['op'], *arg_nums)
            else: # func args
                value_tuple = (instr['op'], *instr['args'])
        else: # const instr
            value_tuple = (instr['op'], instr['value'])

        # re-generate the instr's argument
        if 'args' in instr and all(item in env for item in instr['args']):
            arg_numbers = [env[arg_name] for arg_name in instr['args']]
            instr['args'] = [table[number]['cname'] for number in arg_numbers]

        if value_tuple in tuples:
            # if the value is in the table (computed)
            # then we use the value
            num = tuples.index(value_tuple)
            opcode = table[num]['value_tuple'][0]
            if opcode != 'const':
                canonical_name = table[num]['cname']
                instr['op'] = 'id'
                instr['args'] = [canonical_name]
            else: 
                instr['op'] = 'const'
                instr['value'] = table[num]['value_tuple'][1]
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
            new_blocks += lvn(block)
        func['instrs'] = new_blocks
    print(json.dumps(prog))

if __name__ == "__main__":
    main()