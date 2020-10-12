import hou
import ptvsd
#import debugpy

print (str(hou))

try:
    ptvsd.enable_attach(None, address = ('127.0.0.1', 5678))
    print("Not attached already, enabling attach in ptvsd ... " + str(ptvsd))
except ptvsd.AttachAlreadyEnabledError:
    print("Attach is enabled, Client is_attached()="+str(ptvsd.is_attached())+", continuing...")


def test():
    ptvsd.settrace
    # pause the program until a remote debugger is attached
    ptvsd.wait_for_attach()

    # break at this line
    ptvsd.break_into_debugger()
    
    before = "before"
    after = "after"

    print(before)
    print(after)
