from sage.base_app import BaseApp
import numpy as np
from sage.tools.common.api_tools import get_system_status
import os
import pandas as pd
import time
import pathlib


from sage.base_app import BaseApp

if __name__ == "__main__":
    import App_functions
    from Report_functions import Testing_ReportGenerator
    from Quaternion import Quaternion, Euler
else:
    from . import App_functions
    from .Report_functions import Testing_ReportGenerator
    from .Quaternion import Quaternion, Euler


class Core(BaseApp):
    ###########################################################
    # INITIALIZE APP
    ###########################################################
    def __init__(self, my_sage):
        BaseApp.__init__(self, my_sage, __file__)
        self.DATARATE = self.info["datarate"]

        self.NodeNum_forehead = self.info["sensors"].index("forehead")
        self.current_forehead_quat = Quaternion()
        self.NodeNum_thorax = self.info["sensors"].index("thorax")
        self.current_thorax_quat = Quaternion()

        self.operation_list = [
            "Turn Your Head To the Left",
            "Turn Your Head To the RIGHT",
            "Tilt Your Head Down",
            "Tilt Your Head Up",
            "Make your Left Ear touch your Left Shoulder",
            "Make your Right Ear touch your Right Shoulder",
        ]
        self.operation_time = self.config["operation_time"]  # seconds
        self.operation_index = 0

        self.iteration = 0
        self.audio_prompts_enable = self.config["audio_prompts_enable"]
        self.sound = ""
        self.user_defined_status = ""

        self.forehead_Yawoffset_q = [1, 0, 0, 0]
        self.body_orientation_vertical = 0  # default 0: calibrate by standing posture, 1: calibrate by flat lying posture

        # sensor to segment alignment quaternion, inv denotes conjugate.
        self.BS_q_thorax_inv = [1, 0, 0, 0]
        self.BS_q_forehead_inv = [1, 0, 0, 0]

        self.max_rotatation = 0
        self.min_rotatation = 0
        self.max_head_tilt = 0
        self.min_head_tilt = 0
        self.max_head_obliquity = 0
        self.min_head_obliquity = 0

        self.start_time = None
        self.end_time = None

    #############################################################
    # UPON STARTING THE APP
    # If you have anything that needs to happen before the app starts
    # collecting data, you can uncomment the following lines
    # and add the code in there. This function will be called before the
    # run_in_loop() function below.
    #############################################################
    # def on_start_event(self, start_time):
    #     print("In On Start Event: {start_time}")

    ###########################################################
    # RUN APP IN LOOP
    ###########################################################
    def run_in_loop(self):
        data = self.my_sage.get_next_data()

        # Get Quaternion Data
        self.current_forehead_quat.updateFromRawData(data[self.NodeNum_forehead])
        self.current_thorax_quat.updateFromRawData(data[self.NodeNum_thorax])

        # Calibrate to find BS_q, sensor to body segment alignment quaternions on 1st iteration
        if self.iteration == 0:
            # Find GS_q_init
            self.GS_thorax_q_init = self.current_thorax_quat
            self.GS_forehead_q_init = self.current_forehead_quat

            # Determine Body Orientation and honor manual override via UI.
            if self.config["body_position"] == "Auto Detect":
                self.body_orientation_vertical = App_functions.is_Vertical(
                    self.current_thorax_quat
                )
            elif self.config["body_position"] == "Horizontal":
                self.body_orientation_vertical = 0
            elif self.config["body_position"] == "Vertical":
                self.body_orientation_vertical = 1

            (
                self.forehead_Yawoffset_q,
                self.BS_q_thorax_inv,
                self.BS_q_forehead_inv,
            ) = App_functions.calibrate(
                self.current_thorax_quat, self.current_forehead_quat
            )
            self.start_time = time.time()
            self.iteration_times = [
                self.operation_time * 100 * i for i in range(len(self.operation_list))
            ]
            print(f"iteration times are: {self.iteration_times}")
            self.operation_index = 0
        else:
            self.end_time = time.time()

        # Calculate head angle
        (head_tilt, head_obliquity, head_rotation) = (
            App_functions.calculate_joint_angle(
                self.current_thorax_quat,
                self.BS_q_thorax_inv,
                self.current_forehead_quat,
                self.BS_q_forehead_inv,
                self.forehead_Yawoffset_q,
                self.body_orientation_vertical,
            )
        )

        # Test print
        if self.iteration % 100 == 0:
            print(
                f"Angle [Roll/HeadRotation={np.around(head_rotation,3)}, Pitch/Obliquity={np.around(head_obliquity,3)}, Yaw/HeadTilt={np.around(head_tilt,3)}]"
            )

        # Update the min,max Values Attained so far.
        self.max_rotatation = max(self.max_rotatation, head_rotation)
        self.min_rotatation = min(self.min_rotatation, head_rotation)
        self.max_head_tilt = max(self.max_head_tilt, head_tilt)
        self.min_head_tilt = min(self.min_head_tilt, head_tilt)
        self.max_head_obliquity = max(self.max_head_obliquity, head_obliquity)
        self.min_head_obliquity = min(self.min_head_obliquity, head_obliquity)

        # This section will determine the prompt that is displayed to the user.
        self.operation_index, step = divmod(self.iteration, self.operation_time * 100)
        self.user_defined_status = self.operation_list[self.operation_index]
        if self.audio_prompts_enable:
            self.sound = self.user_defined_status if step != 0 else ""
        else:
            self.sound = ""

        annotations = ""
        # If you wanted to provide custom annotations on the plot, you can uncomment and update the following code:
        # annotation_string = f"Rotation [{abs(self.min_rotatation):.3f}, {self.max_rotatation:.3f}]"
        # annotations = {"x": '.1', "y": '.9', "xref": 'paper', "yref": 'paper', "text": annotation_string}

        time_now = self.iteration / self.DATARATE  # time in seconds

        my_data = {
            "time": [time_now],
            "head_tilt": [head_tilt],
            "body_orientation": [self.body_orientation_vertical],
            "head_obliquity": [head_obliquity],
            "head_rotation": [head_rotation],
            "max_head_rotation": [self.max_rotatation],
            "min_head_rotation": [self.min_rotatation],
            "max_head_tilt": [self.max_head_tilt],
            "min_head_tilt": [self.min_head_tilt],
            "max_head_obliquity": [self.max_head_obliquity],
            "min_head_obliquity": [self.min_head_obliquity],
            "user_defined_status": [self.user_defined_status],
            "annotations": [annotations],
            "audio_feedback": [self.sound],
        }

        self.my_sage.save_data(data, my_data)
        self.my_sage.send_stream_data(data, my_data)

        self.iteration += 1

        return self.iteration <= max(self.iteration_times)

    def on_stop_event(self, stop_time):
        self.end_time = time.time()
        run_time = self.end_time - self.start_time
        print(f"Testing Ran for: {run_time} seconds / {run_time/60:.2f} minutes")
        post_process_start = time.time()
        self.nodes = get_system_status(self.my_sage.my_system_state)["sage_status"][
            "nodes"
        ]
        print(f"reports: {self.config['save_report']}")
        if self.config["save_report"]:
            time.sleep(
                2
            )  # Everything happens so fast that it is hard to know if it worked or not
            self.logger.info("Running Report Calcuations")
            trial_file_name, trial_data_dict, trial_info_dict = self.get_trial_data(
                include_raw=True
            )
            data_df = pd.DataFrame.from_dict(trial_data_dict)
            self.logger.info("Generating the report")
            ReportGenerator = Testing_ReportGenerator(
                trial_file_name,
                os.path.dirname(__file__) + "/report_template.html",
                self.info,
                self.config,
                self.nodes,
            )
            ReportGenerator.define_report_inputs(data_df)
            ReportGenerator.generate_report()
            self.logger.info("Saving the report")
            ReportGenerator.save_report()

        post_process_end = time.time()
        time_taken = post_process_end - post_process_start
        final_message = f"""<p> Run Time: {run_time:.2f} seconds / {run_time/60:.2f} minutes </p>
                            <p> Post Processing Time: {time_taken:.2f} seconds / {time_taken/60:.2f} minutes</p>"""

        # Append the report information if a report was asked to be created.
        if self.config["save_report"]:
            final_message += f"""<p>Report saved. You can find it <a id='hostLink' href='#'>here</a> or in the data management tab</p>
                                        <script> document.getElementById('hostLink').href = 'http://' + window.location.host + '/files/data/{pathlib.Path(ReportGenerator.trial_save_name).name}';</script>"""

        self.logger.info(final_message)
