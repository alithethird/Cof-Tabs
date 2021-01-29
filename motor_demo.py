import time
import signal


def catcher(signum, _):
    print("yeah")


signal.signal(signal.SIGALRM, catcher)
signal.setitimer(signal.ITIMER_REAL, 0.01, 3)

while True:
    time.sleep(5)
