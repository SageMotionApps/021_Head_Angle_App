from .Quaternion import Quaternion, Euler

def is_Vertical(thorax_quat):
    print(
        f"Sensor Orientation Values: {abs(thorax_quat.quat2euler().roll)}, roll value <30 indicates laying flat"
    )
    if abs(thorax_quat.quat2euler().roll) < 30:  # denotes sensor is nearly flat
        return 0
    return 1


# Sensor to segment calibration
def calibrate(current_thorax_quat, current_forehead_quat):

    thorax_Euler = current_thorax_quat.quat2euler()
    forehead_Euler = current_forehead_quat.quat2euler()

    TmpPoseRef = Euler(roll=0, pitch=0, yaw=-(forehead_Euler.yaw - thorax_Euler.yaw))
    forehead_Yawoffset_q = TmpPoseRef.euler2quat()

    # commonYaw is thorax_init_Yaw
    # for thorax IMU calibrate
    # this is our alignment target, we expect rotate IMU to this orientation, both thorax and forehead have the same target.
    GB_Euler0_target = Euler(roll=0, pitch=0, yaw=thorax_Euler.yaw)
    GB_q0_target = GB_Euler0_target.euler2quat()  # target in quaternion format.
    GS_q0 = current_thorax_quat  # current IMU orientation, in global coordinate.
    # conjugate quaternion of forehead sensor to segment quaternion. inv represent for inversion, the same as conjugate.
    BS_q_thorax_inv = Quaternion.quat_multiply(
        Quaternion.quat_conj(GS_q0), GB_q0_target
    )

    # for forehead IMU calibrate
    GB_Euler0_target = Euler(
        roll=0, pitch=0, yaw=forehead_Euler.yaw
    )  # this is our alignment target, we expect rotate IMU to this orientation, both thorax and forehead have the same target.
    GB_q0_target = GB_Euler0_target.euler2quat()  # target in quaternion format.
    GS_q0 = current_forehead_quat  # current IMU orientation, in global coordinate.
    BS_q_forehead_inv = Quaternion.quat_multiply(
        Quaternion.quat_conj(GS_q0), GB_q0_target
    )

    print("Forehead angle Calibrate finished")
    return (forehead_Yawoffset_q, BS_q_thorax_inv, BS_q_forehead_inv)


def calculate_joint_angle(
    current_thorax_quat,
    BS_q_thorax_inv,
    current_forehead_quat,
    BS_q_forehead_inv,
    forehead_Yawoffset_q,
    body_orientation_vertical,
):

    GB_thorax_q = Quaternion.quat_multiply(current_thorax_quat, BS_q_thorax_inv)

    GB_forehead_q = Quaternion.quat_multiply(current_forehead_quat, BS_q_forehead_inv)
    GB_forehead_q = Quaternion.quat_multiply(
        forehead_Yawoffset_q, GB_forehead_q
    )  # Yaw correction

    # calculate three dimensional angles
    B_q_angles = Quaternion.quat_multiply(
        Quaternion.quat_conj(GB_thorax_q), GB_forehead_q
    )

    if body_orientation_vertical == 0:  # lying down calibration
        this_Euler = B_q_angles.quat2euler(orientation="XZY")  # Euler must be XZY order
    else:
        this_Euler = B_q_angles.quat2euler(
            orientation="XYZ"
        )  # Euler must be XYZ order, which is the same as the definition of hip angle.

    head_rotation = this_Euler.roll
    head_obliquity = -this_Euler.pitch
    head_tilt = this_Euler.yaw

    return (head_tilt, head_obliquity, head_rotation)
