import pytest

pytest.importorskip("textual")

from textual.app import App, ComposeResult

from coagent.tui import StatusBar


class StatusBarTestApp(App):
    def compose(self) -> ComposeResult:
        yield StatusBar()


async def test_status_bar_default_render():
    async with StatusBarTestApp().run_test() as pilot:
        bar = pilot.app.query_one(StatusBar)
        rendered = bar.render()
        # rendered is a Rich Text object — check it has some content
        assert rendered is not None


async def test_status_bar_updates():
    async with StatusBarTestApp().run_test() as pilot:
        bar = pilot.app.query_one(StatusBar)
        bar.model_name = "ollama/llama3"
        bar.turn_info = "2/20"
        bar.total_tokens = 1234
        bar.cost = 0.0012
        bar.status = "running"
        rendered = bar.render()
        rendered_str = rendered.plain if hasattr(rendered, "plain") else str(rendered)
        assert "ollama/llama3" in rendered_str
        assert "2/20" in rendered_str
        assert "1234" in rendered_str
