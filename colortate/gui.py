from PySide.QtCore import *
from PySide.QtGui import *

from rotator import ColorRotator

ICON_W, ICON_H = 40, 20

def colored_icon(color_a, color_b):
    icon = QPixmap(ICON_W, ICON_H)
    icon.fill(color_a)
    qp = QPainter(icon)
    qp.fillRect(QRect(ICON_W/2, 0, ICON_W/2, ICON_H), color_b)
    qp.end()
    return icon

class ColorPicker(QLabel):
    acceptColor = Signal(QColor)
    hoverNewColor = Signal(QColor)

    def __init__(self):
        super(ColorPicker, self).__init__()

        self.dragging = False
        self.accepted = QColor("white")
        self.color = QColor("black")

        self.setPixmap(colored_icon(self.accepted, self.color))

    def mousePressEvent(self, event):
        self.dragging = True

    def mouseMoveEvent(self, event):
        globalpos = self.mapToGlobal(event.pos())
        pixels = QPixmap.grabWindow(QApplication.desktop().winId(), globalpos.x(), globalpos.y(), 1, 1)
        prevcolor = self.color
        self.color = QColor(pixels.toImage().pixel(0, 0))

        if self.color != prevcolor:
            self.setPixmap(colored_icon(self.accepted, self.color))

            self.hoverNewColor.emit(self.color)

    def mouseReleaseEvent(self, event):
        self.dragging = False
        self.accepted = self.color
        self.setPixmap(colored_icon(self.accepted, self.color))
        self.acceptColor.emit(self.accepted)

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

        self.colorpickers = QHBoxLayout()
        self.colorpicker = ColorPicker()
        self.colorpicker.hoverNewColor.connect(self.find_color)
        self.transformedpicker = ColorPicker()
        self.transformedpicker.hoverNewColor.connect(self.find_transformed_color)

        self.colorpickers.addWidget(QLabel("pick original:"))
        self.colorpickers.addWidget(self.colorpicker)
        self.colorpickers.addWidget(QLabel("pick transformed:"))
        self.colorpickers.addWidget(self.transformedpicker)

        self.slider_box = QHBoxLayout()

        self.vlayout = QVBoxLayout()
        self.vlayout.addWidget(self.reset_button)
        self.vlayout.addLayout(self.slider_box)
        self.vlayout.addLayout(self.colorpickers)
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

            gnum = int(group.text(0).split(" ")[0]) - 1
            slider = self.sliders[gnum]
            if activate:
                slider.setStyleSheet("background-color: lightblue;")
            else:
                slider.setStyleSheet("")

    def update_color_tree(self):
        self.cotree.clear()
        self.color_items = {}
        for index, g in enumerate(self.cr.groups):
            par_it = QTreeWidgetItem(("%d - %s" % (index + 1, g[0].name()), ))
            self.cotree.addTopLevelItem(par_it)
            self.cotree.expandItem(par_it)

            sorted_colors = g[:]
            sorted_colors.sort(key = lambda c: c.value())

            for color in sorted_colors:
                col_it = QTreeWidgetItem([color.name()])
                col_it.setIcon(0, colored_icon(color, self.cr.color_transform(color)))
                self.color_items[color.name()] = col_it

                par_it.addChild(col_it)

    def find_color(self, color, transformed=False):
        match = self.cr.match_color_to_group(color, transformed)
        if match is not None:
            self.cotree.setCurrentItem(self.cotree.topLevelItem(match))

    def find_transformed_color(self, color):
        self.find_color(color, transformed=True)

