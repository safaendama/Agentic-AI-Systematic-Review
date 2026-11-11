
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


class PRISMAVisualizationAgent:
    def __init__(self, output_dir="data/outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, prisma_data, filename="prisma_flow.png"):
        if not isinstance(prisma_data, dict):
            raise ValueError("PRISMA data must be a dictionary.")

        def value(key):
            result = prisma_data.get(key)
            return str(result) if result is not None else "Not available"

        # Historical reconstructed counts should not
        # be presented as independently verified.
        duplicates_verified = prisma_data.get(
            "duplicates_count_verified", False
        )

        duplicate_label = value("duplicates_removed")
        if not duplicates_verified:
            duplicate_label += "\n(Unverified)"

        fig, ax = plt.subplots(figsize=(14, 12))

        ax.set_xlim(0, 14)
        ax.set_ylim(0, 13)
        ax.axis("off")

        def draw_box(
            x, y, width, height, text,
            color="#EAF2F8", fontsize=10
        ):
            patch = FancyBboxPatch(
                (x, y),
                width,
                height,
                boxstyle="round,pad=0.08",
                linewidth=1.4,
                edgecolor="#34495E",
                facecolor=color
            )
            ax.add_patch(patch)

            ax.text(
                x + width / 2,
                y + height / 2,
                text,
                ha="center",
                va="center",
                fontsize=fontsize,
                linespacing=1.5
            )

        def arrow(x1, y1, x2, y2):
            ax.annotate(
                "",
                xy=(x2, y2),
                xytext=(x1, y1),
                arrowprops={
                    "arrowstyle": "->",
                    "lw": 1.5,
                    "color": "#34495E"
                }
            )

        ax.text(
            7, 12.45,
            "Preliminary PRISMA-Style Flow Diagram",
            ha="center",
            fontsize=17,
            fontweight="bold"
        )

        # IDENTIFICATION
        draw_box(
            4.5, 10.8, 5, 0.9,
            "Records identified\n"
            f"n = {value('records_identified')}"
        )

        arrow(7, 10.8, 7, 10.25)

        draw_box(
            4.5, 9.3, 5, 0.9,
            "Records after deduplication\n"
            f"n = {value('records_after_deduplication')}"
        )

        draw_box(
            10.2, 9.3, 3.2, 0.9,
            "Duplicates removed\n"
            f"n = {duplicate_label}",
            "#FDEDEC",
            fontsize=9
        )

        arrow(9.5, 9.75, 10.2, 9.75)

        # SCREENING
        arrow(7, 9.3, 7, 8.7)

        draw_box(
            4.5, 7.8, 5, 0.9,
            "Records screened by title/abstract\n"
            f"n = {value('records_screened_title_abstract')}"
        )

        # Branch into three separate screening outcomes.
        ax.plot(
            [2.5, 11.5], [7.15, 7.15],
            color="#34495E", linewidth=1.4
        )

        arrow(7, 7.8, 7, 7.15)

        arrow(2.5, 7.15, 2.5, 6.6)
        arrow(7, 7.15, 7, 6.6)
        arrow(11.5, 7.15, 11.5, 6.6)

        draw_box(
            0.5, 5.6, 4, 1,
            "Provisionally included\n"
            f"n = {value('records_provisionally_included')}",
            "#E8F6F3"
        )

        draw_box(
            5, 5.6, 4, 1,
            "Excluded at screening\n"
            f"n = {value('records_excluded_title_abstract')}",
            "#FDEDEC"
        )

        draw_box(
            9.5, 5.6, 4, 1,
            "Uncertain / verification needed\n"
            f"n = {value('records_uncertain')}",
            "#FCF3CF"
        )

        # FULL-TEXT ASSESSMENT
        # No arrows from provisional outcomes: the
        # full-text stage has not been established.
        draw_box(
            4.5, 3.5, 5, 1,
            "Full-text eligibility assessment\n"
            f"n = {value('reports_assessed_for_full_text_eligibility')}",
            "#F2F3F4"
        )

        ax.text(
            7, 4.85,
            "Full-text assessment not yet established",
            ha="center",
            fontsize=9,
            style="italic",
            color="#666666"
        )

        arrow(7, 3.5, 7, 2.85)

        draw_box(
            4.5, 1.85, 5, 1,
            "Studies finally included\n"
            f"n = {value('studies_finally_included')}",
            "#F2F3F4"
        )

        ax.text(
            7, 0.9,
            "Preliminary title/abstract screening only. "
            "Final eligibility requires full-text review.",
            ha="center",
            fontsize=10,
            style="italic"
        )

        output_path = self.output_dir / filename

        fig.savefig(
            output_path,
            dpi=200,
            bbox_inches="tight",
            facecolor="white"
        )

        plt.close(fig)

        return str(output_path)


if __name__ == "__main__":
    input_path = Path(
        "data/outputs/reporting_test/prisma_preliminary.json"
    )

    if not input_path.exists():
        raise FileNotFoundError(
            f"Missing PRISMA report: {input_path}"
        )

    with input_path.open("r", encoding="utf-8") as file:
        prisma = json.load(file)

    agent = PRISMAVisualizationAgent(
        output_dir="data/outputs/reporting_test"
    )

    path = agent.generate(prisma)

    print("\nPRISMA diagram generated successfully!")
    print("Saved to:", path)
