from __future__ import annotations

from rich.text import Text
from textual.reactive import reactive
from textual.widgets import Static


class StatusBar(Static):
    """Footer status bar showing model info, tokens, cost, and run status."""

    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 2;
        background: $surface;
        color: $text-muted;
        padding: 0 2;
    }
    """

    model_name: reactive[str] = reactive("")
    turn_info: reactive[str] = reactive("0/0")
    total_tokens: reactive[int] = reactive(0)
    cost: reactive[float] = reactive(0.0)
    status: reactive[str] = reactive("idle")

    def render(self) -> Text:
        line1 = Text()
        if self.model_name:
            line1.append(f" {self.model_name}", style="bold")
            line1.append(" │ ", style="dim")
        line1.append(f"Turn {self.turn_info}")
        line1.append(" │ ", style="dim")
        line1.append(f"Tokens: {self.total_tokens}")

        line2 = Text()
        line2.append(f" Cost: ${self.cost:.4f}")
        line2.append(" │ ", style="dim")

        status_style = {
            "idle": "dim",
            "running": "bold yellow",
            "completed": "bold green",
            "failed": "bold red",
        }.get(self.status, "")
        line2.append(self.status.capitalize(), style=status_style)

        result = Text()
        result.append_text(line1)
        result.append("\n")
        result.append_text(line2)
        return result
