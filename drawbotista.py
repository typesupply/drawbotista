import math
import warnings
import ui
from objc_util import ObjCClass, ObjCInstance

def ObjCConstant(name):
    import ctypes
    from objc_util import c
    return ObjCInstance(ctypes.c_void_p.in_dll(c, name))


NSAttributedString = ObjCClass("NSAttributedString")
NSFont = ObjCClass("NSFont")
NSColor = ObjCClass("NSColor")
NSFontAttributeName = ObjCConstant("NSFontAttributeName")
NSForegroundColorAttributeName = ObjCConstant("NSForegroundColorAttributeName")


class DrawBotDrawingTool(object):

    def __init__(self):
        self._width = 500
        self._height = 500
        self._ctx = PythonistaViewContext()

    # ------
    # Canvas
    # ------

    def size(self, width, height=None):
        # XXX support strings
        if height is None:
            height = width
        self._width = width
        self._height = height

    def newDrawing(self):
        pass

    def endDrawing(self):
        self._ctx.setSize(self._width, self._height)
        self._ctx.present("sheet")

    # ------
    # Colors
    # ------

    def fill(self, r, g=None, b=None, alpha=1):
        self._ctx.addInstruction("fill", r, g, b, alpha)

    def stroke(self, r, g=None, b=None, alpha=1):
        self._ctx.addInstruction("stroke", r, g, b, alpha)

    # ------
    # Shapes
    # ------

    def rect(self, x, y, w, h):
        path = BezierPath()
        path.rect(x, y, w, h)
        self._ctx.addInstruction("drawPath", path)

    def oval(self, x, y, w, h):
        path = BezierPath()
        path.oval(x, y, w, h)
        self._ctx.addInstruction("drawPath", path)

    def polygon(self, *points, **kwargs):
        path = BezierPath()
        path.polygon(*points, **kwargs)
        self._ctx.addInstruction("drawPath", path)

    def line(self, point1, point2):
        path = BezierPath()
        path.line(point1, point2)
        self._ctx.addInstruction("drawPath", path)

    # Path Properties

    def strokeWidth(self, value):
        self._ctx.addInstruction("strokeWidth", value)

    def miterLimit(self, value):
        self._ctx.addInstruction("miterLimit", value)

    def lineJoin(self, value):
        self._ctx.addInstruction("lineJoin", value)

    def lineCap(self, value):
        self._ctx.addInstruction("lineCap", value)

    def lineDash(self, *value):
        if not value:
            raise DrawBotError("lineDash must be a list of dashes or None")
        if isinstance(value[0], (list, tuple)):
            value = value[0]
        self._ctx.addInstruction("lineDash", value)

    # ----
    # Text
    # ----

    """
    hyphenation(value)
    lineHeight(value)
    tracking(value)
    baselineShift(value)
    openTypeFeatures(frac=True, case=True, ...)
    language(language)
    """

    def font(self, fontName, fontSize=None):
        self._ctx.addInstruction("font", fontName, fontSize)

    def fontSize(self, fontSize):
        self._ctx.addInstruction("fontSize", fontSize)

    def textBox(self, txt, box, align=None):
        if not isinstance(txt, str):
            raise TypeError("expected 'str', got '%s'" % type(txt).__name__)
        assert align is None
        self._ctx.addInstruction("textBox", txt, box)

    # ------
    # States
    # ------

    def save(self):
        self._ctx.addInstruction("save")

    def restore(self):
        self._ctx.addInstruction("restore")

    def savedState(self):
        return SavedStateContextManager(self)

    # ---------------
    # Transformations
    # ---------------

    def transform(self, matrix, center=(0, 0)):
        if center != (0, 0):
            warnings.warn("center is not implemented.")
        self._ctx.addInstruction("transform", matrix)

    def translate(self, x=0, y=0):
        self._ctx.addInstruction("translate", x=x, y=y)

    def scale(self, x=1, y=None, center=(0, 0)):
        if center != (0, 0):
            warnings.warn("center is not implemented.")
        if y is None:
            y = x
        self._ctx.addInstruction("scale", x=x, y=y)

    def rotate(self, angle, center=(0, 0)):
        if center != (0, 0):
            warnings.warn("center is not implemented.")
        angle = math.radians(angle)
        self._ctx.addInstruction("rotate", angle)

    def skew(self, angle1, angle2=0, center=(0, 0)):
        angle1 = math.radians(angle1)
        angle2 = math.radians(angle2)
        self.transform((1, math.tan(angle2), math.tan(angle1), 1, 0, 0))


# ----
# View
# ----

class PythonistaViewContext(ui.View):

    def __init__(self):
        self.background_color = (1, 1, 1, 1)
        self._db_instructionStack = []
        self._db_stateStack = []
        self._db_state = GraphicsState()

    def setSize(self, width, height):
        self.frame = (0, 0, width, height)
        transform1 = ui.Transform.translation(0, -height)
        transform2 = ui.Transform.scale(1.0, -1.0)
        self.transform = transform1.concat(transform2)

    def draw(self):
        for instructionSet in self._db_instructionStack:
            instructionSet = list(instructionSet)
            self._executeInstructions(instructionSet)

    def _executeInstructions(self, instructions):
        while instructions:
            callback, args, kwargs = instructions.pop(0)
            if callback == "restore":
                self._db_restore()
                return
            elif callback == "save":
                self._db_save()
                with ui.GState():
                    self._executeInstructions(instructions)
            else:
                callback = "_db_" + callback
                method = getattr(self, callback)
                method(*args, **kwargs)

    # ------------
    # Instructions
    # ------------

    def addInstruction(self, callback, *args, **kwargs):
        if not self._db_instructionStack:
            self._db_instructionStack.append([])
        self._db_instructionStack[-1].append((callback, args, kwargs))

    # Colors

    def _db_fill(self, r, g=None, b=None, a=1):
        if r is None:
            self._db_state.fillColor = None
            return
        self._db_state.fillColor = (r, g, b, a)

    def _db_stroke(self, r, g=None, b=None, a=1):
        if r is None:
            self._db_state.strokeColor = None
            return
        self._db_state.strokeColor = (r, g, b, a)

    # Paths

    def _db_drawPath(self, path):
        state = self._db_state
        if path is not None:
            state.path = path
        if state.path:
            path = state.path._path
            path.objc_instance.setMiterLimit_(state.miterLimit)
            path.line_join_style = lineJoinStyles[state.lineJoin]
            path.line_cap_style = lineCapStyles[state.lineCap]
            if state.lineDash is not None:
                path.set_line_dash(state.lineDash)
            if state.fillColor is not None:
                ui.set_color(state.fillColor)
                path.fill()
            if state.strokeColor is not None:
                ui.set_color(state.strokeColor)
                if state.strokeWidth is not None:
                    path.line_width = state.strokeWidth
                path.stroke()

    # Path Properties

    def _db_strokeWidth(self, value):
        self._db_state.strokeWidth = value

    def _db_miterLimit(self, value):
        self._db_state.miterLimit = value

    def _db_lineJoin(self, value):
        self._db_state.lineJoin = value

    def _db_lineCap(self, value):
        self._db_state.lineCap = value

    def _db_lineDash(self, value):
        if value[0] is None:
            value = None
        self._db_state.lineDash = value

    # Text

    def _db_font(self, fontName, fontSize):
        self._db_state.text_fontName = fontName
        if fontSize is not None:
            self._db_state.text_fontSize = fontSize

    def _db_fontSize(self, fontSize):
        self._db_state.text.text_fontSize = fontSize

    def _db_textBox(self, txt, box):
        with ui.GState():
            x, y, w, h = box
            self._db_translate(x, y + h)
            self._db_scale(1, -1)
            font = None
            if self._db_state.text_fontName is not None:
                font = NSFont.fontWithName_size_(
                    self._db_state.text_fontName,
                    self._db_state.text_fontSize
                )
            if font is None:
                font = NSFont.systemFontOfSize_(self._db_state.text_fontSize)
            r, g, b, a = self._db_state.fillColor
            fillColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, a)
            attrs = {
                NSFontAttributeName : font,
                NSForegroundColorAttributeName : fillColor
            }
            string = NSAttributedString.alloc().initWithString_attributes_(txt, attrs)
            string.drawInRect_(((0, 0), (w, h)))

    # States

    def _db_save(self):
        self._db_stateStack.append(self._db_state.copy())

    def _db_restore(self):
        if not self._db_stateStack:
            raise DrawBotError("can't restore graphics state: no matching save()'")
        self._db_state = self._db_stateStack.pop()

    # Transformations

    def _db_transform(self, matrix):
        warnings.warn("transform is not implemented.")

    def _db_translate(self, x=0, y=0):
        transform = ui.Transform.translation(x, y)
        ui.concat_ctm(transform)

    def _db_scale(self, x, y):
        transform = ui.Transform.scale(x, y)
        ui.concat_ctm(transform)

    def _db_rotate(self, angle):
        transform = ui.Transform.rotation(angle)
        ui.concat_ctm(transform)


lineJoinStyles = dict(
    miter=ui.LINE_JOIN_MITER,
    round=ui.LINE_JOIN_ROUND,
    bevel=ui.LINE_JOIN_BEVEL
)
lineCapStyles = dict(
    butt=ui.LINE_CAP_BUTT,
    round=ui.LINE_CAP_ROUND,
    square=ui.LINE_CAP_SQUARE
)

# --------------
# Graphics State
# --------------

class SavedStateContextManager(object):

    def __init__(self, drawingTools):
        self._drawingTools = drawingTools

    def __enter__(self):
        self._drawingTools.save()
        return self

    def __exit__(self, type, value, traceback):
        self._drawingTools.restore()


class GraphicsState(object):

    def __init__(self):
        self._loadAttributes(None)

    def _loadAttributes(self, other=None):
        attributesAndFallbacks = dict(
            fillColor=(0, 0, 0, 1),
            strokeColor=None,
            strokeWidth=1,
            miterLimit=10,
            lineJoin="miter",
            lineCap="butt",
            lineDash=None,
            path=None,
            text_fontName=None,
            text_fontSize=10
        )
        for attr, fallback in attributesAndFallbacks.items():
            value = fallback
            if other is not None and hasattr(other, attr):
                value = getattr(other, attr)
            setattr(self, attr, value)

    def copy(self):
        new = self.__class__()
        new._loadAttributes(self)
        return new


# -----------
# Bezier Path
# -----------

class BezierPath(object):

    def __init__(self, path=None, glyphSet=None):
        assert glyphSet is None
        if path is None:
            path = ui.Path()
        self._path = path

    # Pen

    def moveTo(self, point):
        self._path.move_to(*point)

    def lineTo(self, point):
        self._path.line_to(*point)

    def curveTo(self, *points):
        self._path.curve_to(*points)

    def qCurveTo(self, *points):
        warnings.warn("BezierPath.qCurveTo is not implemented.")

    def closePath(self):
        self._path.close()

    def endPath(self):
        pass

    # Point Pen

    def beginPath(self, *args, **kwargs):
        warnings.warn("BezierPath.beginPath is not implemented.")

    def addPoint(self, *args, **kwargs):
        warnings.warn("BezierPath.addPoint is not implemented.")

    def addComponent(self, *args, **kwargs):
        warnings.warn("BezierPath.addComponent is not implemented.")

    # Drawing

    def drawToPen(self, *args, **kwargs):
        warnings.warn("BezierPath.drawToPen is not implemented.")

    def drawToPointPen(self, *args, **kwargs):
        warnings.warn("BezierPath.drawToPointPen is not implemented.")

    # Shapes

    def arc(self, center, radius, startAngle, endAngle, clockwise):
        x, y = center
        self._path.add_arc(x, y, radius, startAngle, endAngle, clockwise)

    def arcTo(self, point1, point2, radius):
        warnings.warn("BezierPath.arcTo is not implemented.")

    def rect(self, x, y, w, h):
        sub = ui.Path().rect(x, y, w, h)
        self._path.append_path(sub)

    def oval(self, x, y, w, h):
        sub = ui.Path().oval(x, y, w, h)
        self._path.append_path(sub)

    def line(self, point1, point2):
        self.moveTo(point1)
        self.lineTo(point2)

    def polygon(self, *points, **kwargs):
        if len(points) <= 1:
            raise TypeError("polygon() expects more than a single point")
        doClose = kwargs.get("close", True)
        if (len(kwargs) == 1 and "close" not in kwargs) or len(kwargs) > 1:
            raise TypeError("unexpected keyword argument for this function")

        self.moveTo(points[0])
        for x, y in points[1:]:
            self.lineTo((x, y))
        if doClose:
            self.closePath()

    # Text

    def text(self, *args, **kwargs):
        warnings.warn("BezierPath.text is not implemented.")

    def textBox(self, *args, **kwargs):
        warnings.warn("BezierPath.textBox is not implemented.")

    # Path Testing and Properties

    def pointInside(self, point):
        x, y = point
        return self._path.hit_test(x, y)

    def bounds(self):
        return self._path.bounds

    def controlPointBounds(self):
        warnings.warn("BezierPath.controlPointBounds is not implemented.")

    # Trace

    def traceImage(self, *args, **kwargs):
        warnings.warn("BezierPath.traceImage is not implemented.")

    # Path Operations

    def optimizePath(self):
        warnings.warn("BezierPath.optimizePath is not implemented.")

    def copy(self):
        new = self.__class__()
        new.appendPath(self)
        return new

    def reverse(self):
        # XXX
        # this could be implemented by:
        # 1. make a new UIBezierPath with 
        #    self._path.objc_instance.bezierPathByReversingPath()
        # 2. clear this path with o_i.removeAllPoints()
        # 3. append the reversed path to this path
        warnings.warn("BezierPath.reverse is not implemented.")

    def appendPath(self, otherPath):
        self._path.append_path(otherPath._path)

    def __add__(self, otherPath):
        warnings.warn("BezierPath.__add__ is not implemented.")

    def __iadd__(self, other):
        self.appendPath(other)
        return self

    # NSBezierPath

    def getNSBezierPath(self, *args, **kwargs):
        return self._path.objc_instance

    def setNSBezierPath(self, *args, **kwargs):
        warnings.warn("BezierPath.setNSBezierPath is not implemented.")

    # Transformations

    def translate(self, x=0, y=0):
        self.transform((1, 0, 0, 1, x, y))

    def rotate(self, angle, center=(0, 0)):
        angle = math.radians(angle)
        c = math.cos(angle)
        s = math.sin(angle)
        self.transform((c, s, -s, c, 0, 0), center)

    def scale(self, x=1, y=None, center=(0, 0)):
        if y is None:
            y = x
        self.transform((x, 0, 0, y, 0, 0), center)

    def skew(self, angle1, angle2=0, center=(0, 0)):
        angle1 = math.radians(angle1)
        angle2 = math.radians(angle2)
        self.transform((1, math.tan(angle2), math.tan(angle1), 1, 0, 0), center)

    def transform(self, transformMatrix, center=(0, 0)):
        warnings.warn("BezierPath.transform is not implemented.")

    # Boolean Operations

    def union(self, other):
        warnings.warn("BezierPath.union is not implemented.")

    def removeOverlap(self):
        warnings.warn("BezierPath.removeOverlap is not implemented.")

    def difference(self, other):
        warnings.warn("BezierPath.difference is not implemented.")

    def intersection(self, other):
        warnings.warn("BezierPath.intersection is not implemented.")

    def xor(self, other):
        warnings.warn("BezierPath.xor is not implemented.")

    def intersectionPoints(self, other=None):
        warnings.warn("BezierPath.intersectionPoints is not implemented.")

    def expandStroke(self, width, lineCap="round", lineJoin="round", miterLimit=10):
        warnings.warn("BezierPath.expandStroke is not implemented.")

    def __mod__(self, other):
        warnings.warn("BezierPath.__mod__ is not implemented.")

    __rmod__ = __mod__

    def __imod__(self, other):
        warnings.warn("BezierPath.__imod__ is not implemented.")

    def __or__(self, other):
        warnings.warn("BezierPath.__or__ is not implemented.")

    __ror__ = __or__

    def __ior__(self, other):
        warnings.warn("BezierPath.__ior__ is not implemented.")

    def __and__(self, other):
        warnings.warn("BezierPath.__and__ is not implemented.")

    __rand__ = __and__

    def __iand__(self, other):
        warnings.warn("BezierPath.__iand__ is not implemented.")

    def __xor__(self, other):
        warnings.warn("BezierPath.__xor__ is not implemented.")

    __rxor__ = __xor__

    def __ixor__(self, other):
        warnings.warn("BezierPath.__ixor__ is not implemented.")

    # Points

    def _get_points(self):
        warnings.warn("BezierPath.points is not implemented.")

    points = property(_get_points)

    def _get_onCurvePoints(self):
        warnings.warn("BezierPath.onCurvePoints is not implemented.")

    onCurvePoints = property(_get_onCurvePoints)

    def _get_offCurvePoints(self):
        warnings.warn("BezierPath.offCurvePoints is not implemented.")

    offCurvePoints = property(_get_offCurvePoints)

    def _get_contours(self):
        warnings.warn("BezierPath.contours is not implemented.")

    contours = property(_get_contours)

#    def __len__(self):
#        warnings.warn("BezierPath.__len__ is not implemented.")

    def __getitem__(self, index):
        warnings.warn("BezierPath.__getitem__ is not implemented.")

    def __iter__(self):
        warnings.warn("BezierPath.__iter__ is not implemented.")


# ----
# Test
# ----

if __name__ == "__main__":
    bot = DrawBotDrawingTool()
    
    bot.fill(0, 0, 0, 1)
    bot.rect(0, 0, 10, 10)
    
    # rect
    bot.fill(1, 0, 0, 0.5)
    bot.rect(0, 0, 100, 100)
    
    # savedState
    with bot.savedState() as s1:
        bot.translate(100, 100)
        bot.fill(0, 1, 0, 0.5)
        bot.stroke(0, 0, 1, 0.25)
        bot.strokeWidth(20)
        bot.rect(0, 0, 100, 100)
        with bot.savedState() as s2:
            bot.translate(25, 25)
            bot.stroke(None)
            bot.fill(1, 1, 1, 0.5)
            bot.oval(0, 0, 50, 50)
    
    # rect
    bot.rect(200, 200, 100, 100)
    
    # textBox
    bot.font("Helvetica Bold", 24)
    bot.textBox("This is some text in a box.", (200, 200, 100, 100))
    
    
    # line
    bot.stroke(1, 1, 0, 0.5)
    bot.strokeWidth(50)
    bot.lineDash(2, 4)
    bot.line((0, 0), (300, 300))
    
    # polygon
    bot.fill(0, 0, 0, 0.1)
    bot.stroke(0, 0, 0, 0.3)
    bot.lineDash(None)
    bot.strokeWidth(30)
    bot.lineCap("round")
    bot.lineJoin("round")
    bot.polygon((50, 50), (0, 300), (250, 250), (300, 0), close=False)
    
    # scale
    bot.scale(3)
    bot.fill(None)
    bot.stroke(0, 0, 0, 1)
    bot.strokeWidth(1 / 3)
    bot.rect(0, 0, 100, 100)
    bot.endDrawing()
