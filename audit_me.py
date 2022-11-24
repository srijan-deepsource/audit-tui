from collections import defaultdict
import sys
import json
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

json_path = sys.argv[1]

def prepare_db():
    with open(json_path) as fp:
        data = json.load(fp)
    db = []
    for issue in data:
        shortcode = issue["issue"]["code"]
        title = issue["issue"]["title"]
        if not title.split(":")[0].lower().startswith("audit"):
            continue
        filepath = issue["path"]
        start_line = issue["beginLine"]
        end_line = issue["endLine"]

        db.append((filepath, start_line, end_line, shortcode, title))

    return tuple(db)

class Auditor(Static):
    """A Textual app to triage Audit issues."""

    skipcq_map = defaultdict(lambda: defaultdict(dict))
    skipcq_data = None

    db = prepare_db()

    iter_db = iter(db)

    def render_markdown(self, filepath, startline, endline, shortcode, title):
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
File: **{filepath}**\n
Issue Code: **{shortcode}**\n
Issue: **{title}**\n

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

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        try:
            file, start_line, end_line, shortcode, title = next(self.iter_db)
            message = self.render_markdown(file, start_line, end_line, shortcode, title)
            self.skipcq_data = (file, start_line, shortcode)
            self.query_one("#results", Static).update(Markdown(message))
        except StopIteration:
            self.query_one("#results", Static).update("Nothing to Audit!")

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
            for lno, (shortcode, msg) in sorted(data.items(), reverse=True):
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
                    msg = prefix + f": {shortcode} ({msg})"
                else:
                    msg = prefix + f": {shortcode}"
                skip_msg = prefix_spaces + msg + suffix

                lines.insert(skipcq_index, skip_msg)

            with open(filepath, "w") as fp:
                fp.writelines(lines)


    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        button_id = event.button.id

        if button_id == "fin":
            self.do_suppress()
            sys.exit(0)

        if button_id == "invalid":
            skipcq_msg = self.query_one(Input).value
            if not skipcq_msg:
                skipcq_msg = ''
            file, line, shortcode = self.skipcq_data
            self.skipcq_map[file][line] = (shortcode, skipcq_msg)

        try:
            file, start_line, end_line, shortcode, title = next(self.iter_db)
            message = self.render_markdown(file, start_line, end_line, shortcode, title)
            self.skipcq_data = (file, start_line, shortcode)
            self.query_one("#results", Static).update(Markdown(message))
        except StopIteration:
            self.query_one("#results", Static).update("Audit Complete!")



class AuditorApp(App):
    """A Textual app to triage Audit issues."""

    CSS_PATH = "audit_me.css"

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Auditor()

if __name__ == "__main__":
    app = AuditorApp()
    app.run()
