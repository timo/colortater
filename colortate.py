from PySide.QtCore import *
from PySide.QtGui import *

import re
import shutil

color_rex = re.compile(
      """(?P<hexcolor>#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3})|(?P<rgbfunc>rgb[(](?P<r>[0-9]+), (?P<g>[0-9]+), (?P<b>[0-9]+)[)])""")

HUE_THRESH = 20

ICON_W, ICON_H = 40, 20

def parse_color(match):
    if match.group("hexcolor"):
        return QColor(match.group("hexcolor"))
    elif match.group("rgbfunc"):
        return QColor.fromRgb(int(match.group("r")), int(match.group("g")), int(match.group("b")))

def colored_icon(color_a, color_b):
    icon = QPixmap(ICON_W, ICON_H)
    icon.fill(color_a)
    qp = QPainter(icon)
    qp.fillRect(QRect(ICON_W/2, 0, ICON_W/2, ICON_H), color_b)
    qp.end()
    return icon

class ColorRotatorWindow(QDialog):
    def __init__(self):
        super(ColorRotatorWindow, self).__init__()

        self.stylefiles = {}
        self.knowncolors = {}

        self.groups = []
        self.group_rotations = []
        self.color_items = {}

        self.setup_ui()

    def setup_ui(self):
        self.cotree = QTreeWidget()
        self.cotree.setIconSize(QSize(ICON_W, ICON_H))

        self.write_button = QPushButton("save")
        self.write_button.clicked.connect(self.write_files)

        self.slider_box = QHBoxLayout()

        self.vlayout = QVBoxLayout()
        self.vlayout.addLayout(self.slider_box)
        self.vlayout.addWidget(self.write_button)

        self.hlayout = QHBoxLayout()
        self.hlayout.addWidget(self.cotree)
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
        self.group_rotations.append(0)

        group_number = len(self.groups) - 1
        def adjust_color(number):
            self.group_rotations[group_number] = number
            for col in self.groups[group_number]:
                self.color_items[col.name()].setIcon(0, colored_icon(col, self.color_transform(col, group_number)))

        hue = color.hue()

        slider = QSlider()
        slider.setRange(-hue, 360 - hue)
        slider.setValue(0)
        slider.setTracking(True)
        self.slider_box.addWidget(slider)
        slider.valueChanged.connect(adjust_color)

    def open_stylefile(self, filename):
        print "reading stylefile", filename
        def replace_with_placeholder(match):
            color_obj = parse_color(match)

            match = [key for key, value in self.knowncolors.iteritems() if value == color_obj]
            if match:
                return "%(" + match[0] + ")s"
            else:
                matchkey = "color_%d" % (len(self.knowncolors))
                self.knowncolors[matchkey] = color_obj
                self.new_color(color_obj)
                return "%(" + matchkey + ")s"

        with open(filename, "r") as f:
            text = f.read()

        shutil.copy(filename, filename + ".bak")

        color_rex.findall(text)
        text = text.replace("%", "%%") # escape format string syntax
        new_text = color_rex.sub(replace_with_placeholder, text)

        self.stylefiles[filename] = new_text

        self.update_color_tree()

    def update_color_tree(self):
        self.cotree.clear()
        self.color_items = {}
        for index, g in enumerate(self.groups):
            par_it = QTreeWidgetItem(str(index))
            self.cotree.addTopLevelItem(par_it)
            self.cotree.expandItem(par_it)

            sorted_colors = g[:]
            sorted_colors.sort(key = lambda c: c.value())

            for color in sorted_colors:
                col_it = QTreeWidgetItem([color.name()])
                col_it.setIcon(0, colored_icon(color, self.color_transform(color)))
                self.color_items[color.name()] = col_it

                par_it.addChild(col_it)

    def color_transform(self, color, groupnum=None):
        if not groupnum:
            groupmatches = [idx for idx, g in enumerate(self.groups) if color in g]
            assert len(groupmatches) == 1
            groupnum = groupmatches[0]
        hue_transform = self.group_rotations[groupnum]

        old_hsv = color.hue(), color.hsvSaturation(), color.value()
        new_hsv = (old_hsv[0] + hue_transform)%360, old_hsv[1], old_hsv[2]
        if old_hsv[0] == -1:
            return color


        newc = QColor.fromHsv(*new_hsv)
        return newc

    def write_files(self):
        transformed_colors = dict((name, self.color_transform(color).name()) for name, color in self.knowncolors.iteritems())
        for filename, text in self.stylefiles.iteritems():
            with open(filename, "w") as f:
                f.write(text % transformed_colors)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    w = ColorRotatorWindow()
    w.show()

    if len(sys.argv) > 1:
        for v in sys.argv[1:]:
            w.open_stylefile(v)

    sys.exit(app.exec_())
