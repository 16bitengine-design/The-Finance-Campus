"""Illustrative Manim scene for a hypothetical compound-growth example.

Render from the repository root:
    manim -qh assets/manim/compound_growth_demo.py CompoundGrowthDemo

The assumed 5% rate is a teaching input, not a forecast or promised return.
"""
from decimal import Decimal

from manim import (
    DOWN,
    LEFT,
    UP,
    Axes,
    Create,
    DecimalNumber,
    FadeIn,
    Scene,
    Text,
    VGroup,
)


class CompoundGrowthDemo(Scene):
    def construct(self) -> None:
        principal = Decimal("1000")
        annual_rate = Decimal("0.05")
        years = 10
        values = [
            float(principal * (Decimal("1") + annual_rate) ** year)
            for year in range(years + 1)
        ]

        title = Text("How compound growth works", color="#FFFFFF", font_size=42)
        subtitle = Text(
            "Hypothetical example • $1,000 at 5% annually",
            color="#FFFFFF",
            font_size=24,
        )
        header = VGroup(title, subtitle).arrange(direction=DOWN, buff=0.18)
        header.to_edge(UP)
        self.play(FadeIn(header))

        axes = Axes(
            x_range=[0, years, 2],
            y_range=[0, 1800, 300],
            x_length=10,
            y_length=5,
            axis_config={"color": "#FFFFFF", "include_numbers": True},
            tips=False,
        ).shift(DOWN * 0.55)
        x_label = Text("Years", font_size=24).next_to(axes, DOWN)
        y_label = Text("Value ($)", font_size=24).rotate(1.5708).next_to(axes, LEFT)
        self.play(Create(axes), FadeIn(x_label), FadeIn(y_label))

        curve = axes.plot(
            lambda t: 1000 * (1.05**t),
            x_range=[0, years],
            color="#168C43",
            use_smoothing=True,
        )
        self.play(Create(curve), run_time=4)

        final_value = DecimalNumber(
            values[-1],
            num_decimal_places=2,
            group_with_commas=True,
            color="#F5B817",
            font_size=40,
        )
        final_value.next_to(axes, UP, buff=0.22)
        label = Text("After 10 years:", font_size=26, color="#FFFFFF")
        label.next_to(final_value, DOWN, buff=0.12)
        self.play(FadeIn(label), FadeIn(final_value))
        self.wait(1.5)
