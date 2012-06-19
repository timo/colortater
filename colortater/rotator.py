try:
    from PySide.QtGui import QColor
except ImportError:
    from compat import QColor

import re
from os import path

color_rex = re.compile(
      """(?P<hexcolor>#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3})|(?P<rgbfunc>rgb[(](?P<r>[0-9]+), (?P<g>[0-9]+), (?P<b>[0-9]+)[)])""")

HUE_THRESH = 20

def parse_color(match):
    if match.group("hexcolor"):
        return QColor(match.group("hexcolor"))
    elif match.group("rgbfunc"):
        return QColor.fromRgb(int(match.group("r")), int(match.group("g")), int(match.group("b")))

class ColorRotator(object):
    def __init__(self, stylefiles):
        self.stylefiles = {}
        self.knowncolors = {}

        self.groups = []
        self.group_rotations = []
        self.color_items = {}

        for stylefile in stylefiles:
            self.open_stylefile(stylefile)

        self.adjustment_filename = path.join(path.dirname(sorted(self.stylefiles.keys())[0]), "colortater.dat")

        self.read_adjustment_values()

    def match_color_to_group(self, color, transformed = False):
        for gid, group in enumerate(self.groups):
            representant = group[0]
            if transformed:
                representant = self.color_transform(representant, gid)
            h1 = representant.hue()
            h2 = color.hue()
            if min(abs(h1 - h2), abs(360 + h1 - h2)) < HUE_THRESH:
                return gid

        return None

    def new_color(self, color):
        match = self.match_color_to_group(color)
        if match is not None:
            self.groups[match].append(color)
            return

        # no group was found, create a new one.
        self.groups.append([color])
        self.group_rotations.append(0)

    def rotate_group(self, representant, value, absolute = False):
        for gidx, group in enumerate(self.groups):
            if group[0].name().replace("#","") == representant.replace("#",""):
                if absolute:
                    new_value = value % 360
                else:
                    new_value = (self.group_rotations[gidx] + value) % 360
                self.group_rotations[gidx] = new_value
                print "adjusting %d" % gidx
                return True
        return False

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
            text = f.read().decode("utf8")

        if path.exists(filename + ".src"):
            with open(filename + ".src", "r") as f:
                text = f.read().decode("utf8")
        else:
            with open(filename + ".src", "w") as f:
                f.write(text.encode("utf8"))

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
                f.write((text % transformed_colors).encode("utf8"))

        print "writing %s" % self.adjustment_filename
        with open(self.adjustment_filename, "w") as f:
            pairs = []
            for index, adjustment in enumerate(self.group_rotations):
                repr_name = self.groups[index][0].name()
                pairs.append("%s: %s\n" % (repr_name, adjustment))
            f.writelines(pairs)

