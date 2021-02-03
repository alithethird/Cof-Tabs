from mpu6050 import mpu6050

imu_sensor = mpu6050(0x68)
def gyro():
    global GxCal
    global GyCal
    global GzCal
    gyro_data = imu_sensor.get_gyro_data()
    gyro_x = gyro_data['x']
    gyro_y = gyro_data['y']
    gyro_z = gyro_data['z']

    Gx = gyro_x / 131.0 - GxCal
    Gy = gyro_y / 131.0 - GyCal
    Gz = gyro_z / 131.0 - GzCal
    return Gx, Gy, Gz

def calibrate():
    print("Calibrate....")
    gyro_data = imu_sensor.get_gyro_data()

    global GxCal
    global GyCal
    global GzCal
    x = 0
    y = 0
    z = 0
    for i in range(50):
        x = x + gyro_data['x']
        y = y + gyro_data['y']
        z = z + gyro_data['z']
    x = x / 50
    y = y / 50
    z = z / 50
    GxCal = x / 131.0
    GyCal = y / 131.0
    GzCal = z / 131.0

    print("GxCal")
    print("GyCal")
    print("GzCal")

while(1):

    x, y, z = gyro()
    print("x: " + x + '\n')
    print("y: " + y + '\n')
    print("Z: " + z + '\n')




