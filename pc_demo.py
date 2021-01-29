from motor_driver_pc import motor_driver_pc
import time
md = motor_driver_pc()

ttime, ticks, direction = md.calculate_ticks()

md.motor_run(ttime, ticks, direction)

while True:
    time.sleep(5)