from collections import defaultdict
from rich.syntax import Syntax
from textwrap import indent
from rich.markdown import Markdown
from textual.app import App, ComposeResult
from textual.containers import Content, Container, Horizontal
from textual.widgets import Button, Static, Input

EXTENSION_MAP = {
    "py": "# skipcq",
    "js": "// skipcq",
    "ts": "// skipcq",
    "java": "// skipcq",
    "scala": "// skipcq",
    "cs": "// skipcq",
    "go": "// skipcq",
    "php": "// skipcq",
}


class Auditor(Static):
    """A Textual app to triage Audit issues."""

    skipcq_map = defaultdict(lambda: defaultdict(dict))
    current_file_pos = None

    db = (
        ("/Users/sauravsrijan/work/hackathon/app.py", 8, 8, "This is a random message"),
        ("/Users/sauravsrijan/work/hackathon/app.py", 19, 19, "This is another random message"),
        ("/Users/sauravsrijan/work/hackathon/app.py", 26, 27, "This is yet another random message"),
        ("/Users/sauravsrijan/work/hackathon/app.py", 33, 33, "oh come on!"),
    )

    iter_db = iter(db)

    def render_markdown(self, filepath, startline, endline):
        """Read a file, and render the markdown."""
        with open(filepath) as fp:
            lines = fp.readlines()
        start_index = startline - 3 - 1 # 0-index!
        if start_index < 0:
            start_index = 0

        end_index = endline + 3 - 1  # 0-index!

        while True:
            try:
                lines[end_index]
                break
            except:
                end_index -= 1

        _lines = lines[start_index: end_index+1]

        start_offset = startline - start_index
        end_offset = endline - end_index

        code_lines = indent(''.join(_lines), '    ')

        output = f"""
File: **{filepath}**

---

{code_lines}
    """

        return output

    def compose(self) -> ComposeResult:
        """Creatre child widgets for the Audit App."""
        yield Content(Static(id="results"), id="results-container")
        yield Input(placeholder="Add optional skipcq message.")
        yield Container(
            Horizontal(
                Button("Looks legit!", id="valid", variant="success"),
                Button("Non-issue", id="invalid", variant="error"),
                Button("I am done!", id="fin", variant="success"),
                classes="buttons",
            ),
            id="buttons-container"
        )
        # yield Button("Looks legit!", id="valid", variant="success")
        # yield Button("Non-issue", id="invalid", variant="error")
        # yield Button("I am done!", id="fin", variant="success")

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        file, line, col, _desc = next(self.iter_db)
        message = self.render_markdown(file, line, col)
        self.current_file_pos = (file, line)
        self.query_one("#results", Static).update(Markdown(message))

    @staticmethod
    def get_comment_prefix(filepath):
        """Get the prefix for comment."""
        extension = filepath.split('.')[-1]
        return EXTENSION_MAP.get(extension, "// skipcq")

    def do_suppress(self):
        """Add skipcqs in the files."""
        for filepath, data in self.skipcq_map.items():
            prefix = self.get_comment_prefix(filepath)
            suffix = "\n"
            with open(filepath) as fp:
                lines = fp.readlines()
            for lno, msg in sorted(data.items(), reverse=True):
                # get the index of line number
                line_index = lno - 1
                # get indentation for line:
                prefix_spaces = ''
                for c in lines[line_index]:
                    if c in ("\t", " "):
                        prefix_spaces += c
                    else:
                        break
                # insert position of skipcq is 1 line above.
                skipcq_index = line_index - 1
                if msg:
                    msg = prefix + ": " + msg
                else:
                    msg = prefix
                skip_msg = prefix_spaces + msg + suffix

                lines.insert(skipcq_index, skip_msg)

            with open(filepath, "w") as fp:
                fp.writelines(lines)


    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        button_id = event.button.id

        if button_id == "fin":
            self.do_suppress()
            exit()

        if button_id == "invalid":
            skipcq_msg = self.query_one(Input).value
            if not skipcq_msg:
                skipcq_msg = ''
            file, line = self.current_file_pos
            self.skipcq_map[file][line] = skipcq_msg

        try:
            file, line, col, _desc = next(self.iter_db)
            message = self.render_markdown(file, line, col)
            self.current_file_pos = (file, line)
            self.query_one("#results", Static).update(Markdown(message))
        except StopIteration:
            self.query_one("#results", Static).update("Audit Complete!")



class AuditorApp(App):
    """A Textual app to triage Audit issues."""

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]
    CSS_PATH = "audit_me.css"

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Auditor()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        # self.dark = not self.dark
        yield Button(self.query_one(Input).value)

if __name__ == "__main__":
    app = AuditorApp()
    app.run()
