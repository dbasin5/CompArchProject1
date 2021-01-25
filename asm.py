# Author: David Basin
# Purpose of the program is to convert a set of instructions to machine code

import argparse

# The print_machine_code function takes machine code and it's address and puts it into
# a readable format (in the format: ram[addr] = 16'b machine code;)
def print_machine_code(address, instruction):
    final_instruct = "ram[" + str(address) + "] = 16'b" + instruction + ";"
    print(final_instruct)

# The threereg function takes in an instr. line that has three registers and translates it into machine code
def threereg(line):
    # In order to always include leading 3 zeroes in the machine code for the 3-register instructions,
    # we set machine_code to equal 0b100..0 (16 zeroes); we'll take the 1 out later
    machine_code = 0b10000000000000000
    offset = 0
    # If the instruction is jr, the dest register and second source register are both set to zero
    if (line[0:2] == "jr"):
        regDst = 0
        # This while loop is used to find the $, adding to offset if it hits spaces. That way, when
        # we assign a value to regSrcA, it will surely be the number of a source.
        while line[3+offset] == " ": offset += 1
        regSrcA = int(line[4+offset])
        regSrcB = 0
    else:
        # If the instruction isn't jr, we read for all three register values
        # Again, while loops are used here to navigate through the spaces in the line
        offset = 0
        if line[0:2] != "or": offset += 1
        while line[3+offset] == " ": offset += 1
        regDst = int(line[4+offset])
        while line[6+offset] == " ": offset += 1
        regSrcA = int(line[7+offset])
        while line[9+offset] == " ": offset += 1
        regSrcB = int(line[10+offset])
    # The machine code is set as a combination of the sources regs and dest reg. Then, the last four binary digits,
    # which are dependent on what the opcode is, are added on
    machine_code = machine_code | (regSrcA << 10) | (regSrcB << 7) | (regDst << 4)
    if (line[0:3] == "sub"): machine_code = machine_code | 0b1
    if (line[0:3] == "and"): machine_code = machine_code | 0b10
    if (line[0:2] == "or"): machine_code = machine_code | 0b11
    if (line[0:3] == "slt"): machine_code = machine_code | 0b100
    if (line[0:2] == "jr"): machine_code = machine_code | 0b1000
    # The binary representation of the final number is then cut down to exclude the "0b" and the leading 1
    return bin(machine_code)[3:]

# The tworegImm function takes in an instr. line that has two registers and an immediate value at the end of the
# instructions (i.e. addi, slti, and movi) and translates it into machine code. It also takes in the labels dict
def tworegImm(line, labels):
    offset = 0
    machine_code = 0b10000000000000
    # If the opcode is movi, the regSrc is zero, while the regDst is found in the line
    if line[0:4] == "movi":
        regSrc = 0
        while line[5+offset] == " ": offset += 1
        regDst = int(line[6+offset])
        while line[8+offset] == " ": offset += 1
        start = 8+offset
    # Otherwise, I find both the dest and src register numbers
    else:
        offset = 0
        while line[4+offset] == " ": offset += 1
        regDst = int(line[6])
        while line[8+offset] == " ": offset += 1
        regSrc = int(line[9+offset])
        while line[11+offset] == " ": offset += 1
        start = 11+offset
    # The variable start is found to be the first index of an immediate value. If that index is a number or a
    # negative symbol, then we know we're being given a numberical value and take it in as the immediate.
    if line[start] in "-0123456789":
        imm = int(line[start:])
    # Otherwise, we know that it's a label and we find it in the dictionary of labels
    else:
        imm = labels[line[start:]]
    # If the immediate value is negative, we turn it into a 7-bit 2's complement
    if imm < 0: imm = imm % (1<<7)
    machine_code = machine_code | (regSrc << 10) | (regDst << 7) | imm
    # The first three bits at the beginning vary depending on if we are doing slti or addi
    if (line[0:4] == "slti"): return "001" + bin(machine_code)[3:]
    if (line[0:4] in {"addi", "movi"}): return "111" + bin(machine_code)[3:]

# The memImm function takes in an instruction with sw or lw, which contains two registers and an imm.,
# where the immediate is added to a register's value to find where to look in the memory.
# Like before, while loops are used to skip over reading spaces, and the immediate value is either assigned
# to be the number listed (if a numerical value is given) or the number associated with the label listed,
# in which case we look back at the labels dictionary, which the function also takes in
def memImm(line,labels):
    offset = 0
    machine_code = 0b10000000000000
    while line[3+offset] == " ": offset += 1
    regDst = int(line[4+offset])
    # The negative offset is created to check for spaces inside the parentheses, since I find the regAddr
    # from the back rather than the front
    negoffset = 0
    while line[-2-negoffset] == " ": negoffset += 1
    regAddr = int(line[-2-negoffset])
    while line[6+offset] == " ": offset += 1
    while line[-4-negoffset] == " ": negoffset += 1
    if line[6+offset] in "-0123456789":
        imm = int(line[6+offset:-4-negoffset])
    else:
        imm = labels[line[6+offset:-4-negoffset]]
    if imm < 0: imm = imm % (1<<7)
    machine_code = machine_code | (regAddr << 10) | (regDst << 7) | imm
    # The first two bits of the machine code depend on if we have opcode sw or lw
    if (line[0:2] == "lw"): return "100" + bin(machine_code)[3:]
    if (line[0:2] == "sw"): return "101" + bin(machine_code)[3:]

# The jeq function takes in an instruction with jeq, a 2-register instruction, and turns it into machine code.
# Again, while loops are used to skip over reading spaces in the line, and the immediate is either a number or
# a label, found in the labels dictionary. We also take in the program counter in order to find the rel_imm.
def jeq(line,labels,count):
    offset = 0
    machine_code = 0b10000000000000
    regA = int(line[5])
    while line[7+offset] == " ": offset += 1
    regB = int(line[8+offset])
    while line[10+offset] == " ": offset += 1
    if line[10+offset] in "-0123456789":
        imm = int(line[10+offset:])
    else:
        imm = labels[line[10+offset:]]
    # The relative immediate (+1) is how many instructions we move up by. It's assigned accordingly here
    rel_imm = (imm - count - 1)
    if rel_imm < 0: rel_imm = rel_imm % (1<<7)
    machine_code = machine_code | (regA << 10) | (regB << 7) | rel_imm
    return "110" + bin(machine_code)[3:]

# The fill function takes in an instruction with .fill, and returns a 16-bit binary evaluation of the immediate
# value given in the line, whether it be by numerical value or by label, found from the labels dict it takes in
def fill(line,labels):
    offset = 0
    machine_code = 0b10000000000000000
    while line[6+offset] == " ": offset += 1
    if line[6+offset] in "-0123456789":
        imm = int(line[6+offset:])
    else:
        imm = labels[line[6+offset:]]
    if imm < 0: imm = imm % (1<<16)
    return bin(machine_code | imm)[3:]

# The j_or_jal function takes in an instruction that jumps, jumps and links, or jumps to itself (halts).
# It uses while loops to negate the space characters to find the immediate value to which it jumps to
# (except for in the case of halt, where it jumps to itself, using the program counter that the function
# takes in). That immediate value is either a number or a label who's value is found in the labels dict
def j_or_jal(line,labels,count):
    # The "start" index is found depending on which opcode we're given and the spaces between opcode & imm
    if line[0:2] == "j ":
        offset = 0
        while line[2+offset] == " ": offset += 1
        start = 2+offset
        opcode = 0b10
    elif line[0:3] == "jal":
        offset = 0
        while line[4+offset] == " ": offset += 1
        start = 4+offset
        opcode = 0b11
    # If it isn't j or jal, it is halt - it jumps to itself
    else: return "010" + bin((0b10000000000000) | count)[3:]
    if line[start] in "-0123456789":
        imm = int(line[start:])
    else:
        imm = labels[line[start:]]
    if imm < 0: imm = imm % (1<<13)
    return "0" + bin((opcode << 13) | imm)[2:]    
    
def main():
    # The main features some elements given by Professor Epstein in his starter code
    parser = argparse.ArgumentParser(description='Assemble E20 files into machine code')
    parser.add_argument('filename', help='The file containing assembly language, typically with .s suffix')
    cmdline = parser.parse_args()

    # we store a dict mapping labels to their values here
    labels = {}

    # our final output is a list of ints values representing
    # machine code instructions
    instructions=[]

    # store the lines relevant to our program (i.e. no blank lines)
    lines = []
    
    # iterate through the line in the file, construct a list
    # of numeric values representing machine code
    with open(cmdline.filename) as f:
        for line in f:
            line = line.split("#",1)[0].strip()    # remove comments
            if len(line) > 0:
                lines.append(line.lower()) # lower case version of the line
    instructionCounter = 0
    # Here I iterate through the lines and find our labels. If the label is on its own line, the
    # program counter for that line will be added to the value for the label key in the labels dict
    # Otherwise, whatever is in front of the colon is denoted the label
    for line in lines:
        if ":" in line:
            if line[-1] == ":":
                labels[line[0:-1]] = instructionCounter
            else:
                elemcounter = 0
                while (line[elemcounter] != ":"): elemcounter += 1
                labels[line[0:elemcounter]] = instructionCounter
                instructionCounter += 1
        # If a colon isn't found, then there's no label and add one to the program count
        else: instructionCounter += 1
    instructionCounter = 0
    # This is where the instructions turn into machine code
    for line in lines:
        # If there's a colon in the line and it's not in the last index, then we update our line
        # to be only what's behind that colon + whitespace
        addInstruction = True
        if ":" in line:
            if line[-1] != ":": 
                elemcounter = 0
                while (line[elemcounter] != ":"): elemcounter += 1
                while (line[elemcounter+1] == " "): elemcounter += 1
                line = line[elemcounter+1:]
            else: addInstruction = False
        # The following if statements will go to the relevant function above the main depending on
        # what the opcode is, and then will add the resulting machine code to the list of instructions
        if ((line[0:4] in {"sub ", "add ", "and ", "slt "}) or (line[0:2] in {"jr","or"})):
            instructions.append(threereg(line))
        elif (line[0:4] in {"slti", "addi", "movi"}):
            instructions.append(tworegImm(line,labels))
        elif (line[0:2] in {"sw", "lw"}):
            instructions.append(memImm(line,labels))
        elif (line[0:3] == "jeq"):
            instructions.append(jeq(line,labels,instructionCounter))
        elif ((line[0:2] == "j ") or (line[0:3] == "jal") or (line[0:4] == "halt")):
            instructions.append(j_or_jal(line,labels,instructionCounter))
        elif (line[0:5] == ".fill"):
            instructions.append(fill(line,labels))
        #There's no function for nop because it's machine code is just sixteen zeroes
        elif (line[0:3] == "nop"):
            instructions.append("0"*16)
        if (addInstruction): instructionCounter += 1
        
    # print out each instruction in the required format
    for address, instruction in enumerate(instructions):
        print_machine_code(address, instruction) 


if __name__ == "__main__":
    main()
