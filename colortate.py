from PySide.QtCore import *
from PySide.QtGui import *

import re

color_rex = re.compile("(?P<color>#[0-9a-fA-F]{3}|#[0-9a-fA-F]{6})")

class ColorRotatorWindow(QDialog):
    def __init__(self):
        super(ColorRotatorWindow, self).__init__()

        self.stylefiles = []
        self.knowncolors = {}

        self.setup_ui()

    def setup_ui(self):
        self.colist = QListWidget()
        self.cowheel = QWidget()
        self.rotate_slider = QSlider()

        self.vlayout = QVBoxLayout()
        self.vlayout.addWidget(self.cowheel)
        self.vlayout.addWidget(self.rotate_slider)

        self.hlayout = QHBoxLayout()
        self.hlayout.addWidgets(self.colist)
        self.hlayout.addLayout(self.vlayout)

    def open_stylefile(self, filename):
        def replace_with_placeholder(match):
            match = [key for key, value in self.knowncolors.iter_items() if value == match.group("color")]
            if match:
                return "%(" + match[0] + ")s"
            else:
                matchkey = "color_%d" % (len(self.knowncolors))
                self.knowncolors[matchkey] = match.group("color")
                return "%(" + matchkey + ")s"

        with open(filename, "r") as f:
            text = f.read()

        colors_from_text = color_rex.findall(text)

        print colors_from_text

        new_text = color_rex.replace(replace_with_placeholder)

        print new_text
