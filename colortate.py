from PySide.QtCore import *
from PySide.QtGui import *

import re
from os import path

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

class ColorRotator(object):
    def __init__(self, stylefiles):
        self.stylefiles = {}
        self.knowncolors = {}

        self.groups = []
        self.group_rotations = []
        self.color_items = {}

        for stylefile in stylefiles:
            self.open_stylefile(stylefile)

        self.adjustment_filename = path.join(path.dirname(sorted(self.stylefiles.keys())[0]), "colortate.dat")

        self.read_adjustment_values()

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

        if path.exists(filename + ".src"):
            with open(filename + ".src", "r") as f:
                text = f.read()
        else:
            with open(filename + ".src", "w") as f:
                f.write(text)

        color_rex.findall(text)
        text = text.replace("%", "%%") # escape format string syntax
        new_text = color_rex.sub(replace_with_placeholder, text)

        self.stylefiles[filename] = new_text

    def read_adjustment_values(self):
        try:
            print "reading adjustment values from %s" % self.adjustment_filename
            with open(self.adjustment_filename, "r") as f:
                pairs = f.readlines()
                unpacked_pairs = [pair.strip().split(":") for pair in pairs]
                group_values = dict(map(lambda (k, v): (k, int(v)), unpacked_pairs))

                for gidx, group in enumerate(self.groups):
                    if group[0].name() in group_values:
                        self.group_rotations[gidx] = group_values[group[0].name()]
        except IOError:
            print "no adjustment file found at %s" % (self.adjustment_filename)

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
            print "writing %s" % filename
            with open(filename, "w") as f:
                f.write(text % transformed_colors)

        print "writing %s" % self.adjustment_filename
        with open(self.adjustment_filename, "w") as f:
            pairs = []
            for index, adjustment in enumerate(self.group_rotations):
                repr_name = self.groups[index][0].name()
                pairs.append("%s: %s\n" % (repr_name, adjustment))
            f.writelines(pairs)

class ColorRotatorWindow(QDialog):
    def __init__(self, stylefiles):
        super(ColorRotatorWindow, self).__init__()

        self.cr = ColorRotator(stylefiles)

        self.sliders = []
        self.setup_ui()
        self.update_color_tree()
        self.setup_sliders()

    def setup_ui(self):
        self.cotree = QTreeWidget()
        self.cotree.setIconSize(QSize(ICON_W, ICON_H))
        self.cotree.setHeaderHidden(True)
        self.cotree.currentItemChanged.connect(self.on_tree_item_changed)

        self.write_button = QPushButton("save")
        self.write_button.clicked.connect(self.cr.write_files)

        self.reset_button = QPushButton("reset all")

        self.slider_box = QHBoxLayout()

        self.vlayout = QVBoxLayout()
        self.vlayout.addWidget(self.reset_button)
        self.vlayout.addLayout(self.slider_box)
        self.vlayout.addWidget(self.write_button)

        self.hlayout = QHBoxLayout()
        self.hlayout.addWidget(self.cotree)
        self.hlayout.addLayout(self.vlayout)

        self.setLayout(self.hlayout)

    def setup_sliders(self):
        for group_number, group in enumerate(self.cr.groups):
            self.make_slider(group_number, group)

    def make_slider(self, group_number, group):
        color = group[0]

        def adjust_color(number):
            self.cr.group_rotations[group_number] = number
            for col in self.cr.groups[group_number]:
                self.color_items[col.name()].setIcon(0, colored_icon(col, self.cr.color_transform(col, group_number)))
                self.cotree.scrollToItem(self.color_items[self.cr.groups[group_number][0].name()])

        hue = self.cr.color_transform(color, group_number).hue()

        layout = QVBoxLayout()

        reset = QPushButton("R")
        reset.setFixedWidth(25)
        layout.addWidget(reset)

        label = QLabel(str(group_number + 1))
        layout.addWidget(label)

        slider = QSlider()
        self.sliders.append(slider)
        slider.setRange(-hue, 360 - hue)
        slider.setValue(0)
        slider.setTracking(True)
        slider.valueChanged.connect(adjust_color)

        def reset_color():
            slider.setSliderPosition(0)
            adjust_color(0)

        reset.clicked.connect(reset_color)
        self.reset_button.clicked.connect(reset_color)

        layout.addWidget(slider)

        self.slider_box.addLayout(layout)

    def on_tree_item_changed(self, current, prev):
        for activate, blob in zip((False, True), (prev, current)):
            if not blob: continue

            if blob.childCount() == 0:
                group = blob.parent()
            else:
                group = blob

            gnum = int(group.text(0)) - 1
            slider = self.sliders[gnum]
            if activate:
                slider.setStyleSheet("background-color: lightblue;")
            else:
                slider.setStyleSheet("")

    def update_color_tree(self):
        self.cotree.clear()
        self.color_items = {}
        for index, g in enumerate(self.cr.groups):
            par_it = QTreeWidgetItem(str(index + 1))
            self.cotree.addTopLevelItem(par_it)
            self.cotree.expandItem(par_it)

            sorted_colors = g[:]
            sorted_colors.sort(key = lambda c: c.value())

            for color in sorted_colors:
                col_it = QTreeWidgetItem([color.name()])
                col_it.setIcon(0, colored_icon(color, self.cr.color_transform(color)))
                self.color_items[color.name()] = col_it

                par_it.addChild(col_it)

if __name__ == "__main__":
    import sys
    import argparse

    ap = argparse.ArgumentParser()

    ap.add_argument("--headless", action="store_true",
            help="read new adjustment values from files and re-write the updated versions")

    ap.add_argument("filenames", nargs="+",
            help="css files to read/write.")

    args = ap.parse_args()

    if args.headless:
        app = QApplication(sys.argv, not args.headless)
        cr = ColorRotator(args.filenames)
        cr.write_files()

    else:
        app = QApplication(sys.argv, not args.headless)
        w = ColorRotatorWindow(args.filenames)
        w.show()
        sys.exit(app.exec_())
