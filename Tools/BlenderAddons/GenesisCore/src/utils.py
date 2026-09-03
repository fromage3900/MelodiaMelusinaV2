import bpy
import logging


class BTextWriter:
    _text_name = "GenesisCore.log.py"
    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls()
        try:
            cls._instance.ensure_text()
        except AttributeError:
            pass
        return cls._instance

    def __init__(self):
        self.text: bpy.types.Text = None
        self.should_flush = False
        self.prev_role = "user"
        self.prev_index = 0
        self.messages = []

    def ensure_text(self):
        if self._text_name not in bpy.data.texts:
            self.text = bpy.data.texts.new(self._text_name)
        self.text = bpy.data.texts[self._text_name]

    def push(self, message):
        self.should_flush = True
        self.messages.append(message)

    def flush1(self):
        if self.prev_index == len(self.messages):
            return
        # 先将光标移到末尾
        self.text.cursor_set(len(self.text.lines), character=len(self.text.lines[-1].body) * 2)
        for message in self.messages[self.prev_index :]:
            role = message.get("role", "user")
            content = message.get("content", "")
            line = ""
            # 收到streaming
            if role == "streaming":
                line = "" if self.prev_role == "streaming" else "\n"  # streaming开始时换行
                line += content
            elif role != "streaming":
                line = "" if self.prev_role != "streaming" else "\n"  # streaming结束时换行
                line += f"{role}:\n{content}\n"
            self.prev_role = role
            if not content:
                continue
            self.text.write(line)
        self.prev_index = len(self.messages)

    def flush(self):
        if self.prev_index == len(self.messages):
            return
        # 先将光标移到末尾
        lines = []
        for message in self.messages[self.prev_index :]:
            role = message.get("role", "user")
            content = message.get("content", "")
            line = ""
            # 收到streaming
            if role == "streaming":
                line = "" if self.prev_role == "streaming" else "\n"  # streaming开始时换行
                line += content
            elif role != "streaming":
                line = "" if self.prev_role != "streaming" else "\n"  # streaming结束时换行
                line += f"{role}:\n{content}\n"
            self.prev_role = role
            if not content:
                continue
            lines.append(line)
        self.text.from_string("".join(lines))
        self.prev_index = len(self.messages)

    def refresh(self):
        # 重新加载文本数据
        self.text.clear()
        self.prev_role = "user"
        self.prev_index = 0
        self.flush()

    def clear(self):
        self.text.clear()
        self.messages.clear()
        self.prev_role = "user"
        self.prev_index = 0


class BTextHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = BTextWriter.get()
            stream.push({"role": logging.getLevelName(record.levelno), "content": msg})
        except RecursionError:
            raise
        except Exception:
            self.handleError(record)


def update_screen():
    try:
        for area in bpy.context.screen.areas:
            if area not in {"VIEW_3D", "TEXT_EDITOR"}:
                continue
            area.tag_redraw()
    except Exception:
        ...


def update_text():
    try:
        text_writer = BTextWriter.get()
        if not text_writer.should_flush:
            return
        text_writer.refresh()
        text_writer.should_flush = False
    except Exception:
        ...


def update_timer():
    update_screen()
    update_text()
    return 1 / 30


def register():
    bpy.app.timers.register(update_timer, persistent=True)


def unregister():
    bpy.app.timers.unregister(update_timer)
