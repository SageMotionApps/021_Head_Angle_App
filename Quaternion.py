import numpy as np
import math


class Euler:
    def __init__(self, roll=None, pitch=None, yaw=None, orientation=""):
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw
        self.orientation = orientation

    def euler2quat(self):
        # Input: ZYX Euler Angle (in degrees) [roll, pitch, yaw]
        # Output: Quaternion [qw, qx, qy, qz]

        # ZYX Euler Angle formed by first rotating about the Z axis (yaw), then Y axis (pitch), then X axis (roll)
        # en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles#Euler_Angles_to_Quaternion_Conversion
        # computergraphics.stackexchange.com/questions/8195/how-to-convert-euler-angles-to-quaternions-and-get-the-same-euler-angles-back-fr

        roll = self.roll * np.pi / 180  # X axis rotation, convert to radians
        pitch = self.pitch * np.pi / 180  # Y axis rotation, convert to radians
        yaw = self.yaw * np.pi / 180  # Z axis rotation, convert to radians

        qw = np.cos(roll / 2) * np.cos(pitch / 2) * np.cos(yaw / 2) + np.sin(
            roll / 2
        ) * np.sin(pitch / 2) * np.sin(yaw / 2)
        qx = np.sin(roll / 2) * np.cos(pitch / 2) * np.cos(yaw / 2) - np.cos(
            roll / 2
        ) * np.sin(pitch / 2) * np.sin(yaw / 2)
        qy = np.cos(roll / 2) * np.sin(pitch / 2) * np.cos(yaw / 2) + np.sin(
            roll / 2
        ) * np.cos(pitch / 2) * np.sin(yaw / 2)
        qz = np.cos(roll / 2) * np.cos(pitch / 2) * np.sin(yaw / 2) - np.sin(
            roll / 2
        ) * np.sin(pitch / 2) * np.cos(yaw / 2)

        return Quaternion(w=qw, x=qx, y=qy, z=qz)

    def __str__(self):
        return f"Angle [Roll={np.around(self.roll,3)}, Pitch={np.around(self.pitch,3)}, Yaw={np.around(self.yaw,3)}]"


class Quaternion:

    @classmethod
    def quat_conj(cls, data=None):
        return Quaternion(w=data.w, x=data.x * -1, y=data.y * -1, z=data.z * -1)

    @classmethod
    def quat_multiply(cls, quat1, other_Quat):
        product = Quaternion()
        product.w = (
            quat1.w * other_Quat.w
            - quat1.x * other_Quat.x
            - quat1.y * other_Quat.y
            - quat1.z * other_Quat.z
        )
        product.x = (
            quat1.w * other_Quat.x
            + quat1.x * other_Quat.w
            + quat1.y * other_Quat.z
            - quat1.z * other_Quat.y
        )
        product.y = (
            quat1.w * other_Quat.y
            + quat1.y * other_Quat.w
            + quat1.z * other_Quat.x
            - quat1.x * other_Quat.z
        )
        product.z = (
            quat1.w * other_Quat.z
            + quat1.z * other_Quat.w
            + quat1.x * other_Quat.y
            - quat1.y * other_Quat.x
        )
        return product

    def __init__(self, w=None, x=None, y=None, z=None):
        self.w = w
        self.x = x
        self.y = y
        self.z = z

    def updateFromRawData(self, data=None):
        self.w = data["Quat1"]
        self.x = data["Quat2"]
        self.y = data["Quat3"]
        self.z = data["Quat4"]

    def __str__(self):
        return f"Quaternion({self.w}, {self.x}, {self.y}, {self.z})"

    def calculateVerticalSwayAngle(self):
        """
        This will calculate the Rotation Z->Y->Z for a node that that is switch pointing up.
        Note: This is about the z-axis (axis out of IMU board)
        """
        # case zyz, Rotation sequence: Z->Y->Z
        t0 = 2 * (self.y * self.z + self.w * self.x)
        t1 = -2 * (self.x * self.z - self.w * self.y)

        sway = np.arctan2(t0, t1)  # in radians
        # in deg and adjusted for keeping the sensor vertical
        verticalsway = sway * 180 / 3.14159 + 90

        # this_angle is corresponding to the sway angle when the sensor is kept vertical with switch pointing up
        return verticalsway

    def calculateFrontalSwayAngle(self):
        """
        This will calculate the Rotation Z->Y->X for a node that that is switch pointing up.
        Note: This is about the x-axis (axis along short edge of IMU board)
        """

        # case zyx, Rotation sequence: Z->Y->X, res0 about x-axis
        r31 = 2 * (self.y * self.z + self.w * self.x)
        r32 = self.w * self.w - self.x * self.x - self.y * self.y + self.z * self.z
        res0 = np.arctan2(r31, r32)  # in radians
        res0 = (
            res0 * 180 / 3.14159 + 90
        )  # in deg and adjusted for alignment on the back
        frontalsway = -res0  # adjust for sign convention

        # this_angle is corresponding to the sway angle when the sensor is kept vertical with switch pointing up
        return frontalsway

    def quat2euler(self, orientation="ZYX"):
        # Input: Quaternion [qw, qx, qy, qz]
        # Output: Euler Angle (in degress)

        returnEuler = Euler()

        if orientation == "ZYX":
            # Output: ZYX Euler Angle (in degrees) [roll, pitch, yaw]
            # ZYX Euler Angle formed by first rotating about the Z axis (yaw), then Y axis (pitch), then X axis (roll)
            # en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles#Euler_Angles_to_Quaternion_Conversion
            # computergraphics.stackexchange.com/questions/8195/how-to-convert-euler-angles-to-quaternions-and-get-the-same-euler-angles-back-fr

            # qw = q[0]
            # qx = q[1]
            # qy = q[2]
            # qz = q[3]

            t0 = 2 * (self.y * self.z + self.w * self.x)
            t1 = 1.0 - 2.0 * (self.x * self.x + self.y * self.y)
            roll = math.atan2(t0, t1)

            t2 = 2.0 * (self.w * self.y - self.z * self.x)
            t2 = 1.0 if t2 > 1.0 else t2  # correct if it is out of range
            t2 = -1.0 if t2 < -1.0 else t2  # correct if it is out of range
            pitch = math.asin(t2)

            t3 = 2.0 * (self.w * self.z + self.x * self.y)
            t4 = 1.0 - 2.0 * (self.y * self.y + self.z * self.z)
            yaw = math.atan2(t3, t4)

            # Convert to degrees
            returnEuler.roll = roll * 180 / np.pi
            returnEuler.pitch = pitch * 180 / np.pi
            returnEuler.yaw = yaw * 180 / np.pi
            returnEuler.orientation = orientation

            # return [roll, pitch, yaw]
        elif orientation == "XYZ":
            # Input: Quaternion [qw, qx, qy, qz]
            # Output: XYZ Euler Angle (in degrees) [roll, pitch, yaw]
            # modified from quat2euler

            t0 = 2.0 * (-self.x * self.y + self.w * self.z)
            t1 = 1.0 - 2.0 * (self.y * self.y + self.z * self.z)
            roll = math.atan2(t0, t1)

            t2 = 2.0 * (self.x * self.z + self.w * self.y)
            t2 = 1.0 if t2 > 1.0 else t2  # correct if it is out of range
            t2 = -1.0 if t2 < -1.0 else t2  # correct if it is out of range
            pitch = math.asin(t2)

            t3 = 2.0 * (-self.y * self.z + self.w * self.x)
            t4 = 1.0 - 2.0 * (self.x * self.x + self.y * self.y)
            yaw = math.atan2(t3, t4)

            # Convert to degrees
            returnEuler.roll = roll * 180 / np.pi
            returnEuler.pitch = pitch * 180 / np.pi
            returnEuler.yaw = yaw * 180 / np.pi
            returnEuler.orientation = orientation

            # return [roll, pitch, yaw]
        elif orientation == "XZY":
            # Input: Quaternion [qw, qx, qy, qz]
            # Output: XZY Euler Angle (in degrees) [roll, pitch, yaw]
            # modified from quat2euler

            t0 = 2.0 * (self.x * self.z + self.w * self.y)
            t1 = 1.0 - 2.0 * (self.z * self.z + self.y * self.y)
            roll = math.atan2(t0, t1)

            t2 = 2.0 * (self.x * self.y - self.w * self.z)
            t2 = 1.0 if t2 > 1.0 else t2  # correct if it is out of range
            t2 = -1.0 if t2 < -1.0 else t2  # correct if it is out of range
            pitch = -math.asin(t2)

            t3 = 2.0 * (self.y * self.z + self.w * self.x)
            t4 = 1.0 - 2.0 * (self.x * self.x + self.z * self.z)
            yaw = math.atan2(t3, t4)

            # Convert to degrees
            returnEuler.roll = roll * 180 / np.pi
            returnEuler.pitch = pitch * 180 / np.pi
            returnEuler.yaw = yaw * 180 / np.pi
            returnEuler.orientation = orientation
            # return [roll, pitch, yaw]

        return returnEuler

    def test_print_sensor_quaternions(self, data):
        # Test print
        this_Euler = self.quat2euler()
        print(f"Quaternion({self.w}, {self.x}, {self.y}, {self.z})")
        print(f"Roll: {this_Euler[0]}, Pitch: {this_Euler[1]}, Yaw: {this_Euler[2]}")
        print("")
        print(np.around(this_Euler, decimals=3))
        print("")
