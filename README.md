# 021_Head_Angle
This app is used to measure the head angles: obliquity, rotation, and tilt. This app is intended to be used as a quick diagnostic tool for tortecolis and generates a report with the max angle achieved for each angle.

### Nodes Required: 2 
- Sensing (2): 
  - forehead (switch pointing superiorly)
  - thorax (switch pointing superiorly)
- Feedback (0)
  
## Algorithm & Calibration
### Algorithm Information
The raw quaternions from the IMU are converted to Euler angles, and the roll angle is extracted using well established mathematical principles. If you'd like to learn more about quaternion to Euler angles calculations, we suggest starting with this Wikipedia page: [Conversion between quaternions and Euler angles](https://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles)

### Calibration Process:
- The participant's torso should be either vertical (standing or sitting with their back next to a wall) or horizontal (laying flat on their back). The app takes the initial position when the app starts as in alignment.

## Description of Data in Downloaded File
### Calculated Fields
- time (sec): time since trial start
- body_orientation: 1 indicates vertical orientation (standing or sitting with their back next to a wall), 0 indicates horizontal orientation (laying flat on their back).
- head_tilt (deg): the angle of the head tilt. Positive values are upward tilt, negative values are downward tilt.
- head_obliquity (deg): the angle of the head obliquity. Positive values are to the left, negative values are to the right.
- head_rotation (deg): the angle of the head rotation. Positive values are to the left, negative values are to the right.
- max_head_rotation (deg): the max angle of head rotation to the left achieved so far. 
- min_head_rotation (deg): the max angle of head rotation to the right achieved so far. 
- max_head_tilt (deg): the max angle of head tilt upward achieved so far. 
- min_head_tilt (deg): the max angle of head tilt downward achieved so far. 
- max_head_obliquity (deg): the max angle of head obliquity to the left achieved so far. 
- min_head_obliquity (deg): the max angle of head obliquity to the right achieved so far. 
- annotations: if any annotations are sent to the dashboard chart, they will also be listed here.
- audio_feedback: if any audio feedback is sent to the dashboard, it will also be listed here.
- user_defined_status: the prompts displayed to the user on the dashboard, will also be listed here.

### Sensor Raw Data Values 
Please Note: Each of the columns listed below will be repeated for each sensor
- SensorIndex: index of raw sensor data
- AccelX/Y/Z (m/s^2): raw acceleration data
- GyroX/Y/Z (deg/s): raw gyroscope data
- MagX/Y/Z (μT): raw magnetometer data
- Quat1/2/3/4: quaternion data (Scaler first order)
- Sampletime: timestamp of the sensor value
- Package: package number of the sensor value
