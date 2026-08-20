import time



#select output text
def chooseRandomText(lines):

    current_time = int(time.time())
    index = current_time % len(lines)
    return lines[index]
