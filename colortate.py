from PySide.QtCore import *
from PySide.QtGui import *

import re

color_rex = re.compile("(?P<color>#[0-9a-fA-F]{3}|#[0-9a-fA-F]{6})")

HUE_THRESH = 20

class ColorRotatorWindow(QDialog):
    def __init__(self):
        super(ColorRotatorWindow, self).__init__()

        self.stylefiles = {}
        self.knowncolors = {}

        self.groups = []
        self.group_rotations = []

        self.setup_ui()

    def setup_ui(self):
        self.colist = QListWidget()
        self.cowheel = QWidget()
        self.rotate_slider = QSlider()

        self.vlayout = QVBoxLayout()
        self.vlayout.addWidget(self.cowheel)
        self.vlayout.addWidget(self.rotate_slider)

        self.hlayout = QHBoxLayout()
        self.hlayout.addWidget(self.colist)
        self.hlayout.addLayout(self.vlayout)

        self.setLayout(self.hlayout)

    def new_color(self, color):
        for group in self.groups:
            # XXX this may lead to imprecise stuff
            # or dependance on order of colors in the file.
            representant = group[0]
            if abs(representant.hslHue() - color.hslHue()) < HUE_THRESH:
                group.append(color)
                return

        # no group was found, create a new one.
        self.groups.append([color])
        self.group_rotations.append([0])

    def open_stylefile(self, filename):
        print "reading stylefile", filename
        def replace_with_placeholder(match):
            color_obj = QColor(match.group("color"))

            match = [key for key, value in self.knowncolors.iter_items() if value == color_obj]
            if match:
                return "%(" + match[0] + ")s"
            else:
                matchkey = "color_%d" % (len(self.knowncolors))
                self.knowncolors[matchkey] = color_obj
                self.new_color(color_obj)
                return "%(" + matchkey + ")s"

        with open(filename, "r") as f:
            text = f.read()

        colors_from_text = color_rex.findall(text)

        print colors_from_text

        new_text = color_rex.sub(replace_with_placeholder)

        print new_text

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    w = ColorRotatorWindow()
    w.show()

    w.open_stylefile("style.css")

    sys.exit(app.exec_())
