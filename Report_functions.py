from abc import ABC, abstractmethod
import datetime as dt
import matplotlib.pyplot as plt
from jinja2 import Template  # I use template since there are no inherited templates.
from bs4 import BeautifulSoup as Soup
import sage


class ReportGenerator(ABC):

    def __init__(self, trial_file_name, template_name, info, config, nodes) -> None:
        self.save_folder = sage.experiments_data_dir
        if ".csv" in trial_file_name:
            self.trial_save_name = (
                trial_file_name[: trial_file_name.index("+")]
                + "_report"
                + trial_file_name[
                    trial_file_name.index("+") : trial_file_name.index(".csv")
                ]
                + ".html"
            )
        elif ".xlsx" in trial_file_name:
            self.trial_save_name = (
                trial_file_name[: trial_file_name.index("+")]
                + "_report"
                + trial_file_name[
                    trial_file_name.index("+") : trial_file_name.index(".xlsx")
                ]
                + ".html"
            )
        print(f"trial_file_name = {self.trial_save_name}")

        with open(template_name) as f:
            self.template = Template(f.read())
        self.trial_info = {**info, **config, "nodes": nodes}

    def load_render_dict(self, render_dict):
        self.render_dict = render_dict

    def generate_report(self):
        self.html = self.template.render(self.render_dict)

    def save_report(self):
        with open(self.trial_save_name, "w") as f:
            f.write(self.html)

    @abstractmethod
    def define_report_inputs(data_df):
        """
        This needs to be designed for whatever report parameters
        """
        pass


class Testing_ReportGenerator(ReportGenerator):
    def __init__(self, trial_file_name, template_name, info, config, nodes) -> None:
        super().__init__(trial_file_name, template_name, info, config, nodes)

    def define_report_inputs(self, data_df):
        trial_name = self.trial_info["trial_name"]
        app_description = self.trial_info["app_description"]
        trial_notes = self.trial_info["trial_notes"]
        if min(data_df["body_orientation"]) == 1:
            trial_notes = (
                f"This trial was performed with the user in a vertical position. "
                + trial_notes
            )
        else:
            trial_notes = (
                f"This trial was performed with the user in a horizontal position. "
                + trial_notes
            )

        start_time = self.trial_info["local_time"]
        start_time_formatted = dt.datetime.strptime(start_time, "%Y-%m-%d-%H-%M-%S")

        duration = dt.timedelta(seconds=data_df.tail(1).time.values[0])
        duration_formatted = str(duration)[: str(duration).find(".") + 2]

        end_time = start_time_formatted + duration
        end_time_formatted = str(end_time)[: str(end_time).find(".") + 2]

        basic_info_dict = {
            "trial_name": trial_name,
            "app_description": app_description,
            "start_time": start_time_formatted,
            "end_time": end_time_formatted,
            "trial_elapsed_time": duration_formatted,
            "trial_notes": trial_notes,
            "node_count": len(self.trial_info["nodes"]),
            "chart_type": self.trial_info["chart_type"],
        }

        key_metric_dict = {
            "right_rotation": abs(max(data_df["head_rotation"])),
            "left_rotation": abs(min(data_df["head_rotation"])),
            "upward_head_tilt": abs(max(data_df["head_tilt"])),
            "downward_head_tilt": abs(min(data_df["head_tilt"])),
            "right_obliquity": abs(min(data_df["head_obliquity"])),
            "left_obliquity": abs(max(data_df["head_obliquity"])),
        }

        nodes_all = self.trial_info["nodes"]
        nodes = [node["mac"] for node in nodes_all]

        charts_dict = {
            "Head_Rotation_Chart": self.make_head_angle_plot(
                data_df, ["head_rotation"]
            ),
            "head_tilt_Chart": self.make_head_angle_plot(data_df, ["head_tilt"]),
            "head_obliquity_Chart": self.make_head_angle_plot(
                data_df, ["head_obliquity"]
            ),
            "head_tilt_Bullet_Chart": self.make_head_bullet_plot(
                key_metric_dict["downward_head_tilt"],
                key_metric_dict["upward_head_tilt"],
                labels=["Down", "Up"],
                xlimit=80,
            ),
            "Head_Rotation_Bullet_Chart": self.make_head_bullet_plot(
                key_metric_dict["right_rotation"],
                key_metric_dict["left_rotation"],
                labels=["Left", "Right"],
                xlimit=100,
            ),
            "head_obliquity_Bullet_Chart": self.make_head_bullet_plot(
                key_metric_dict["right_obliquity"],
                key_metric_dict["left_obliquity"],
                labels=["Right", "Left"],
                xlimit=60,
            ),
        }

        render_dict = {
            "nodes_info": nodes_all,
            **basic_info_dict,
            **key_metric_dict,
            **charts_dict,
        }

        self.load_render_dict(render_dict)

    def make_head_angle_plot(self, df, fields_to_plot=["head_rotation"]):
        plt.figure(figsize=(15, 7.5))
        ax = plt.subplot(111)

        for this_field in fields_to_plot:
            ax.plot(df[this_field])
        ax.spines.right.set_visible(False)
        ax.spines.top.set_visible(False)
        ax.yaxis.set_ticks_position("left")
        ax.xaxis.set_ticks_position("bottom")
        ax.set_xlabel("Time (sec)", fontsize=16)
        ax.set_ylabel(f"Angle", fontsize=16)
        ax.legend(fontsize=16)
        path_name = "/tmp/tmp.svg"
        plt.savefig(path_name)
        plt.close()  # release it from memory
        with open(path_name, "r") as f:
            svg_data = f.read()
        svg_parsed = Soup(svg_data, features="xml")
        chart_svg = svg_parsed.find("svg")
        chart_svg.attrs["id"] = "chartSvg"
        del chart_svg["height"]
        del chart_svg["width"]
        return chart_svg

    def make_head_bullet_plot(
        self, left, right, xlabel="Head Rotation", labels=["Left", "Right"], xlimit=100
    ):

        colors = ["#fb7116", "#f6d32b", "#f4fb16", "#b4dd1e", "#19d228"]
        width = [i * (xlimit / 5) for i in range(1, 6)]
        left_start = [0] + width[:-1]
        print(f"width is {width}")
        print(f"left_start is {left_start}")
        fig = plt.figure(figsize=(15, 7.5))
        ax = plt.subplot(111)

        plt.barh(y=[0, 0, 0, 0, 0], width=width, left=left_start, color=colors)
        plt.barh(y=[1, 1, 1, 1, 1], width=width, left=left_start, color=colors)
        plt.barh(y=[0], width=[left], color="black", height=0.4)
        plt.barh(y=[1], width=[right], color="black", height=0.4)

        plt.xticks(
            range(0, 101, 10),
            ["{}°".format(i) for i in range(0, 101, 10)],
            fontsize=22,
            fontweight="bold",
        )

        plt.yticks([0, 1], labels, fontsize=22, fontweight="bold")
        plt.xlim(0, xlimit)

        ax.spines[["bottom", "top", "left", "right"]].set_visible(False)

        plt.xlabel(xlabel, fontsize=22, fontweight="bold")

        path_name = "/tmp/tmp.svg"
        plt.savefig(path_name)
        plt.close()  # release it from memory
        with open(path_name, "r") as f:
            svg_data = f.read()
        svg_parsed = Soup(svg_data, features="xml")
        chart_svg = svg_parsed.find("svg")
        chart_svg.attrs["id"] = "chartSvg"
        del chart_svg["height"]
        del chart_svg["width"]
        return chart_svg
