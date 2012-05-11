import colorsys

def hex_to_ints(val):
    if len(val) == 3:
        val = val[0] * 2 + val[1] * 2 + val[2] * 2

    val = val.lower()

    parts = []
    for upper, lower in zip(val[:-1:2], val[1::2]):
        parts.append(int(upper, 16) * 16 + int(lower, 16))

    return parts

class QColor(object):
    def __init__(self, *args):
        if isinstance(args[0], str):
            if args[0].startswith("#"):
                self.setRgb(*hex_to_ints(args[0][1:]))
        elif len(args[0]) == 3:
            self.setRgb(*args[0])

    @classmethod
    def fromRgb(cls, r, g, b):
        return cls((r, g, b))

    @classmethod
    def fromHsv(cls, h, s, v):
        col = cls("#000")
        col.setHsv(h, s, v)
        return col

    def setRgb(self, r, g, b):
        self.r = r / 255.
        self.g = g / 255.
        self.b = b / 255.
        self.update_hsv()

    def setHsv(self, h, s, v):
        self.h = h / 360.
        self.s = s / 255.
        self.v = v / 255.
        self.update_rgb()

    def update_hsv(self):
        self.h, self.s, self.v = colorsys.rgb_to_hsv(self.r, self.g, self.b)

    def update_rgb(self):
        self.r, self.g, self.b = colorsys.hsv_to_rgb(self.h, self.s, self.v)

    hue = lambda self: self.h * 360
    hsvSaturation = lambda self: self.s * 255
    value = lambda self: self.v * 255

    def name(self):
        return "#%02x%02x%02x" % (self.r * 255, self.g * 255, self.b * 255)
