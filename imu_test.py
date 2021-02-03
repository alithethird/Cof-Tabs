from mpu6050 import mpu6050

imu_sensor = mpu6050(0x68)


    while(1):
        gyro_data = imu_sensor.get_gyro_data()  # sensörden gyro_data okundu
        gyro_x = gyro_data['x']
        gyro_y = gyro_data['y']
        gyro_z = gyro_data['z']

        print("x: " + gyro_x + '\n')
        print("y: " + gyro_y + '\n')
        print("Z: " + gyro_z + '\n')