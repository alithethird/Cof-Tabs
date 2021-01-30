import time
import signal


def catcher(signum, _):
    print("yeah")


signal.signal(signal.SIGALRM, catcher)
signal.setitimer(signal.ITIMER_REAL, 3, 0)

while True:
    print("hell")
    time.sleep(1)
