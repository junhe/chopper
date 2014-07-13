import subprocess
import pprint
import re



def dmesg_lines():
    cmd = ['dmesg']
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    lines = []
    for line in proc.stdout:
        if ('ino' in line and 'logical' in line and 'len' in line) or \
                'mabllocOrderEnd' in line:
            lines.append(line)
    proc.wait()

    return lines

def remove_old_inplace(lines):
    latestend = 0 # if no end mark, keep all (not deleting anything)
    for i,line in reversed(list(enumerate(lines))):
        if 'mabllocOrderEnd' in line:
            latestend = i
            break
    if latestend != 0:
        del lines[0:latestend+1]
            

def prettify_one_line(line):
    line = re.sub(r'\[.*\]', '', line)
    line = line.strip()
    return line

def mark_end():
    f = open('/dev/kmsg', 'w')
    f.write('mabllocOrderEnd\n')
    f.flush()
    f.close()

def collect_order():
    lines = dmesg_lines()
    lines = [ prettify_one_line(line) for line in lines]
    #mark_end()
    remove_old_inplace(lines)

    retstr = ';'.join(lines)
    return retstr

if __name__ == '__main__':
    print collect_order()


