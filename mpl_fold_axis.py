"""Fold axis in matplotlib to make broken axis.

This module provides a function `fold_axis` to fold axis in matplotlib, which is also
called broken axis.

Unlike the example named `Broken axis` in matplotlib gallery
(https://matplotlib.org/stable/gallery/subplots_axes_and_figures/broken_axis.html) and
the `brokenaxes` package(https://github.com/bendichter/brokenaxes), this module use
single axes to realize the broken axis, which is easier to use.


Examples
========
import numpy as np
import matplotlib.pyplot as plt

# What user need to do is only import the `fold_axis` function.
from mpl_fold_axis import fold_axis

# Generate data
np.random.seed(19680801)
x = [-31, -30, -29, -1, 0, 1, 29, 30, 31]
y = np.random.randint(0, 50, 9)
y[4] = 172

# Create the figure and the axis
fig, ax = plt.subplots(figsize=(4.5, 3.0))

# Call `Axes.bar` to plot the data
rects = ax.bar(x, y)
ax.bar_label(rects, fmt="%d", padding=2)

# Fold the lower xaxis
# scale (-28, -2) by factor 0.015
# scale (2, 28) by factor 0.015
fold_axis(ax, [(-28, -2, 0.015), (2, 28, 0.015)], axis="x", which="lower")

# Fold both yaxis (lower and upper)
# scale (55, 145) by factor 0.05
fold_axis(ax, [(55, 145, 0.05)], axis="y", which="both")

# Set the ticks and limits
ax.set_xticks(x)
ax.set_yticks([0, 25, 50, 150, 175])
ax.set_ylim(0, 190)

# Enable the grid
ax.grid(True, ls=":")

# Set the labels and title
ax.set_xlabel("X Label")
ax.set_ylabel("Y Label")
ax.set_title("Broken Axis Example")

# Add some text and annotations
ax.text(-31, 160, "Text won't be folded")
ax.annotate(
    "The annotate function \ncan be used normally.",
    fontsize=9,
    xy=(1.3, 4),
    xytext=(1.2, 165),
    arrowprops=dict(
        facecolor="black", connectionstyle="arc3,rad=-0.1", arrowstyle="-|>"
    ),
)

plt.show()

"""

__all__ = ["fold_axis", "add_fold_line", "create_scale", "scale_axis"]

from typing import Literal, Tuple

from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.transforms import blended_transform_factory
from matplotlib.scale import FuncScale, FuncScaleLog

__version__ = "0.1.0"
__author__ = "Wu Yao <wuyao1997@qq.com>"


def add_fold_line(
    ax: Axes,
    lim: Tuple[float, float],
    axis: Literal["x", "y"] = "x",
    which: Literal["lower", "upper", "both"] = "lower",
    lw: float = 1,
    d: float = 1.0,
    color: str = "k",
    span_color: str = "w",
    size: int = 10,
    **kwargs
) -> Tuple[list[Line2D], list[Rectangle]]:
    """Add fold line at the given limit and use white rectangle to cover the fold area.

    In fact, the fold line is a marker line with marker size and marker style of
    `(1, -d)` and `(-1, d)`.

    Parameters
    ----------
    ax : Axes
        The axes to add the fold line to.
    lim : Tuple[float, float]
        Fold limit.
    axis : Literal["x", "y"], optional
        Add fold line in which axis, by default "x"
    which : Literal["lower", "upper", "both"], optional
        Add fold line in which spines, by default "lower"
    lw : float, optional
        Line width of fold line, by default 1
    d : float, optional
        Slope of fold line, by default 1.0
    color : str, optional
        Color of fold line, by default "k"
    span_color : str, optional
        Color of rectangle which used to cover the fold area, by default "w"
    size : int, optional
        Size of fold line, by default 10

    Returns
    -------
    Tuple[list[Line2D], list[Rectangle]]
        fold lines and rectangles
    """
    line_kwargs = dict(
        marker=[(-1, -d), (1, d)],
        markersize=size,
        mew=lw,
        linestyle="none",
        color=color,
        zorder=2.8,
        clip_on=False,
        **kwargs
    )

    span_kwargs = dict(color=span_color, lw=0, clip_on=False, zorder=2.6)

    low, up = lim
    lines, rectangles = [], []

    def _plot_fold_lines(trans, position_func):
        if which in ("lower", "both"):
            l = ax.plot(*position_func(0), transform=trans, **line_kwargs)
            lines.extend(l)
        if which in ("upper", "both"):
            l = ax.plot(*position_func(1), transform=trans, **line_kwargs)
            lines.extend(l)

    def _plot_axspan(axspan_func):
        if which == "both":
            rect = axspan_func(low, up, -0.01, 1.01, **span_kwargs)
            rectangles.append(rect)
        else:
            _min, _max = (-0.01, 0.01) if (which == "lower") else (0.99, 1.01)
            rect1 = axspan_func(low, up, zorder=2.4, color="w", lw=0)
            rect2 = axspan_func(low, up, _min, _max, **span_kwargs)
            rectangles.extend([rect1, rect2])

    if axis == "x":
        trans = blended_transform_factory(ax.transData, ax.transAxes)
        _plot_fold_lines(trans, lambda pos: ([low, up], [pos, pos]))
        _plot_axspan(ax.axvspan)

    if axis == "y":
        trans = blended_transform_factory(ax.transAxes, ax.transData)
        _plot_fold_lines(trans, lambda pos: ([pos, pos], [low, up]))
        _plot_axspan(ax.axhspan)

    return lines, rectangles


def create_scale(
    interval: list[Tuple[float, float, float]],
    mode: Literal["linear", "log"] = "linear",
) -> FuncScale | FuncScaleLog:
    """Create a ScaleBase object by FuncScale or FuncScaleLog.

    Parameters
    ----------
    interval : list[Tuple[float, float, float]]
        [(a1, b1, f1), (a2, b2, f2), ...], where a1 < b1 < a2 < b2 < ...,
        f1 > 0, f2 > 0, ..., and f1, f2 are the scale factor of [a1, b1] and [a2, b2]...
    mode : Literal["linear", "log"], optional
        Scale mode, by default "linear"

    Returns
    -------
    FuncScale | FuncScaleLog
        ScaleBase object which could be passed to ax.set_xscale() or ax.set_yscale()

    Raises
    ------
    ValueError
        Input interval must be non-overlapping and sorted.
    ValueError
        Input scale factor must be positive.
    """
    x0, factor = [], []
    _prev_b = float("-inf")
    for a, b, f in interval:
        if not ((a < b) and (_prev_b < a)):
            raise ValueError("Input interval must be non-overlapping and sorted.")
        if f <= 0:
            raise ValueError("c must be positive")
        x0.extend([a, b])
        factor.extend([f, 1])

    N = len(x0)

    def _forward(x):
        res = x.copy()

        ymin = x0[0]
        for n in range(N - 1):
            xmin, xmax = x0[n], x0[n + 1]
            cond = (x > xmin) & (x <= xmax)
            res[cond] = (x[cond] - xmin) * factor[n] + ymin
            ymin += (xmax - xmin) * factor[n]

        res[x > xmax] = (x[x > xmax] - xmax) * factor[-1] + ymin

        return res

    def _inverse(y):
        res = y.copy()

        ymin = x0[0]
        for n in range(N - 1):
            xmin, xmax = x0[n], x0[n + 1]
            ymax = ymin + (xmax - xmin) * factor[n]
            cond = (y > ymin) & (y <= ymax)
            res[cond] = (y[cond] - ymin) / factor[n] + xmin

            ymin = ymax

        res[y > ymax] = (y[y > ymax] - ymax) / factor[-1] + xmax

        return res

    if mode == "linear":
        return FuncScale(None, functions=(_forward, _inverse))
    else:
        return FuncScaleLog(None, functions=(_forward, _inverse))


def scale_axis(
    ax: Axes,
    interval: list[Tuple[float, float, float]],
    axis: Literal["x", "y"] = "x",
    mode: Literal["linear", "log"] = "linear",
) -> None:
    """Scale the axis by the given interval and factor.

    Parameters
    ----------
    ax : Axes
        The axes to scale.
    interval : list[Tuple[float, float, float]]
        [(a1, b1, f1), (a2, b2, f2), ...], where a1 < b1 < a2 < b2 < ...,
        f1 > 0, f2 > 0, ..., and f1, f2 are the scale factor of [a1, b1] and [a2, b2]...
    axis : Literal["x", "y"], optional
        The axis to scale, by default "x"
    mode : Literal["linear", "log"], optional
        Scale mode, by default "linear"
    """
    scale = create_scale(interval, mode=mode)
    if axis == "x":
        ax.set_xscale(scale)
    if axis == "y":
        ax.set_yscale(scale)
    return


def fold_axis(
    ax: Axes,
    interval: list[Tuple[float, float, float]],
    axis: Literal["x", "y"] = "x",
    which: Literal["lower", "upper", "both"] = "lower",
    mode: Literal["linear", "log"] = "linear",
    lw: float = 1,
    d: float = 1.0,
    color: str = "k",
    span_color: str = "w",
    size: int = 10,
) -> Tuple[list[list[Line2D]], list[list[Rectangle]]]:
    """Fold the axis of axes by the given interval and factor.

    Parameters
    ----------
    ax : Axes
        The axes to fold.
    interval : list[Tuple[float, float, float]]
         [(a1, b1, f1), (a2, b2, f2), ...], where a1 < b1 < a2 < b2 < ...,
        f1 > 0, f2 > 0, ..., and f1, f2 are the scale factor of [a1, b1] and [a2, b2]...
    axis : Literal["x", "y"], optional
        The axis to scale, by default "x"
    which : Literal["lower", "upper", "both"], optional
        Add fold line in which spines, by default "lower"
    mode : Literal["linear", "log"], optional
        Scale mode, by default "linear"
    lw : float, optional
        Line width of fold line, by default 1
    d : float, optional
        Slope of fold line, by default 1.0
    color : str, optional
        Color of fold line, by default "k"
    span_color : str, optional
        Color of rectangle which used to cover the fold area, by default "w"
    size : int, optional
        Size of fold line, by default 10

    Returns
    -------
    Tuple[list[list[Line2D]], list[list[Rectangle]]]
        list of fold lines and rectangles

    Examples
    --------
    >>> ...
    >>> fold_axis(ax, [(-28, -2, 0.015), (2, 28, 0.015)], axis="x", which="lower")
    >>> fold_axis(ax, [(55, 145, 0.05)], axis="y", which="both")
    >>> ...
    >>> fold_axis(ax, [(600, 4000, 0.1)], mode="log")
    >>> fold_axis(ax, [(600, 4000, 0.1)], axis='y', which='both', mode="log")
    """
    if not interval:
        return

    scale_axis(ax, interval, axis=axis, mode=mode)

    lines, rectangles = [], []
    for a, b, _ in interval:
        l, r = add_fold_line(ax, (a, b), axis=axis, which=which)
        lines.append(l)
        rectangles.append(r)

    return lines, rectangles
