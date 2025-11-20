"""Live ASCII visualization for simulated BCI attention, meditation, and DEFCON levels.

This example script continuously prints simulated values alongside an ASCII bar graph
rendered with ``ascii_graph.Pyasciigraph``. Replace the randomly generated values with
real measurements to visualize live inputs.
"""
from __future__ import annotations

import os
import random
import time
from typing import Tuple

from ascii_graph import Pyasciigraph


def _generate_sample() -> Tuple[int, int, int]:
    """Return a tuple of attention, meditation, and DEFCON values."""

    attention = random.randint(40, 90)
    meditation = random.randint(30, 80)
    defcon = random.randint(1, 5)
    return attention, meditation, defcon


def _render_graph(graph: Pyasciigraph, attention: int, meditation: int, defcon: int) -> None:
    """Render the latest values using ``Pyasciigraph``."""

    data = [
        ("Attention", attention),
        ("Meditation", meditation),
        ("DEFCON Level", defcon * 20),  # scale for better visibility
    ]

    for line in graph.graph("", data):
        print(line)


def run_visualization(refresh_interval: float = 1.0) -> None:
    """Continuously update the terminal with simulated metrics and a bar chart."""

    graph = Pyasciigraph()
    print("\ud83d\udcc8 Live BCI / DEFCON visualization started (Ctrl+C to stop)\n")

    while True:
        attention, meditation, defcon = _generate_sample()

        os.system("clear")

        print(f"Time: {time.strftime('%H:%M:%S')}")
        print(f"Attention: {attention} | Meditation: {meditation} | DEFCON: {defcon}\n")

        _render_graph(graph, attention, meditation, defcon)

        time.sleep(refresh_interval)


if __name__ == "__main__":
    try:
        run_visualization()
    except KeyboardInterrupt:
        print("\nVisualization stopped.")
