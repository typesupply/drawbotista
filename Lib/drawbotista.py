import math
import random
import warnings
import ui
import dialogs

# ------
# Bridge
# ------
#
# Great examples here:
# https://github.com/zacbir/geometriq/blob/master/geometriq/backends/_quartz.py

import ctypes
import objc_util
from objc_util import ObjCClass, ObjCInstance

cBool = ctypes.c_bool
cInt = ctypes.c_size_t
cUInt = ctypes.c_uint
cUInt32 = ctypes.c_uint32
cStrOrVoid = ctypes.c_wchar_p
cIntOrVoid = ctypes.c_void_p

def ObjCConstant(name):
    return ObjCInstance(ctypes.c_void_p.in_dll(objc_util.c, name))

# Quartz

quartz = objc_util.c

CGFloat = objc_util.CGFloat
CGPoint = objc_util.CGPoint
CGSize = objc_util.CGSize
CGRect = objc_util.CGRect
CGAffineTransform = objc_util.CGAffineTransform
CGBitmapInfo = cUInt32

kCGLineJoinMiter = 0
kCGLineJoinRound = 1
kCGLineJoinBevel = 2
kCGLineCapButt = 0
kCGLineCapRound = 1
kCGLineCapSquare = 2

CGContextConcatCTM = quartz.CGContextConcatCTM
CGContextConcatCTM.restype = None
CGContextConcatCTM.argtypes = [
    cIntOrVoid,
    CGAffineTransform
]

CGContextSaveGState = quartz.CGContextSaveGState
CGContextSaveGState.restype = None
CGContextSaveGState.argtypes = [cIntOrVoid]

CGContextRestoreGState = quartz.CGContextRestoreGState
CGContextRestoreGState.restype = None
CGContextRestoreGState.argtypes = [cIntOrVoid]

# Foundation

NSMutableData = objc_util.NSMutableData
NSColor = ObjCClass("NSColor")
NSAttributedString = ObjCClass("NSAttributedString")
NSFont = ObjCClass("NSFont")
NSFontAttributeName = ObjCConstant("NSFontAttributeName")
NSForegroundColorAttributeName = ObjCConstant("NSForegroundColorAttributeName")

# UIKit

UIBezierPath = ObjCClass("UIBezierPath")
UIImage = ObjCClass("UIImage")

UIGraphicsBeginImageContext = quartz.UIGraphicsBeginImageContext
UIGraphicsBeginImageContext.restype = None
UIGraphicsBeginImageContext.argtypes = [CGSize]

UIGraphicsEndImageContext = quartz.UIGraphicsEndImageContext
UIGraphicsEndImageContext.restype = None
UIGraphicsEndImageContext.argtypes = []

UIGraphicsGetCurrentContext = quartz.UIGraphicsGetCurrentContext
UIGraphicsGetCurrentContext.restype = cIntOrVoid
UIGraphicsGetCurrentContext.argtypes = []

UIGraphicsGetImageFromCurrentImageContext = quartz.UIGraphicsGetImageFromCurrentImageContext
UIGraphicsGetImageFromCurrentImageContext.restype = cIntOrVoid
UIGraphicsGetImageFromCurrentImageContext.argtypes = []

def UIImagePNGRepresentation(image):
    return ObjCInstance(quartz.UIImagePNGRepresentation(image))

quartz.UIImagePNGRepresentation.restype = cIntOrVoid
quartz.UIImagePNGRepresentation.argtypes = [cIntOrVoid]

# ---------
# API Magic
# ---------

def _getmodulecontents(module, names=None):
    d = {}
    if names is None:
        names = [name for name in dir(module) if not name.startswith("_")]
    for name in names:
        d[name] = getattr(module, name)
    return d


# ------------
# Drawing Tool
# ------------

class DrawBotDrawingTool(object):

    def __init__(self):
        self._width = 500
        self._height = 500
        self._instructionStack = []

    def _get__all__(self):
        return [i for i in dir(self) if not i.startswith("_")]

    __all__ = property(_get__all__)

    def _addToNamespace(self, namespace):
        namespace.update(_getmodulecontents(self, self.__all__))
        namespace.update(_getmodulecontents(random, ["random", "randint", "choice", "shuffle"]))
        namespace.update(_getmodulecontents(math))

    # ---------
    # Internals
    # ---------

    def _addInstruction(self, callback, *args, **kwargs):
        if not self._instructionStack:
            self._instructionStack.append([])
        self._instructionStack[-1].append((callback, args, kwargs))

    def _drawInContext(self, context):
        for instructionSet in self._instructionStack:
            for callback, args, kwargs in instructionSet:
                method = getattr(context, callback)
                method(*args, **kwargs)

    # ----------
    # Image Data
    # ----------

    def imageData(self, format, *args, **kwargs):
        if format == "PNG":
            context = PNGContext(self._width, self._height)
        else:
            raise NotImplementedError("format '%s' is not supported" % fileType)
        self._drawInContext(context)
        return context.imageData()

    # -------------
    # Display Image
    # -------------

    def displayImage(self, mode="fullscreen"):
        data = self.imageData("PNG")
        if data is None:
            return
        DrawBotView(data, mode)

    # ------
    # Canvas
    # ------

    def size(self, width, height=None):
        if width == "screen":
            width, height = ui.get_screen_size()
        if height is None:
            height = width
        self._width = int(width)
        self._height = int(height)

    def width(self):
        return self._width

    def height(self):
        return self._height

    def newDrawing(self):
        self._instructionStack = []

    def endDrawing(self):
        pass

    # ------
    # States
    # ------

    def save(self):
        self._addInstruction("save")

    def restore(self):
        self._addInstruction("restore")

    def savedState(self):
        return SavedStateContextManager(self)

    # ------
    # Colors
    # ------

    def fill(self, r, g=None, b=None, alpha=1):
        self._addInstruction("fill", r, g, b, alpha)

    def stroke(self, r, g=None, b=None, alpha=1):
        self._addInstruction("stroke", r, g, b, alpha)

    # ------
    # Shapes
    # ------

    def drawPath(self, path=None):
        assert path is not None
        self._addInstruction("drawPath", path)

    def rect(self, x, y, w, h):
        path = BezierPath()
        path.rect(x, y, w, h)
        self.drawPath(path)

    def oval(self, x, y, w, h):
        path = BezierPath()
        path.oval(x, y, w, h)
        self.drawPath(path)

    def polygon(self, *points, **kwargs):
        path = BezierPath()
        path.polygon(*points, **kwargs)
        self.drawPath(path)

    def line(self, point1, point2):
        path = BezierPath()
        path.line(point1, point2)
        self.drawPath(path)

    # Path Properties

    def strokeWidth(self, value):
        self._addInstruction("strokeWidth", value)

    def miterLimit(self, value):
        self._addInstruction("miterLimit", value)

    def lineJoin(self, value):
        self._addInstruction("lineJoin", value)

    def lineCap(self, value):
        self._addInstruction("lineCap", value)

    def lineDash(self, *value):
        if not value:
            raise DrawBotError("lineDash must be a list of dashes or None")
        if isinstance(value[0], (list, tuple)):
            value = value[0]
        self._addInstruction("lineDash", value)

    # ----
    # Text
    # ----

    def font(self, fontName, fontSize=None):
        self._addInstruction("font", fontName, fontSize)

    def fontSize(self, fontSize):
        self._addInstruction("fontSize", fontSize)

    def textBox(self, txt, box, align=None):
        if not isinstance(txt, str):
            raise TypeError("expected 'str', got '%s'" % type(txt).__name__)
        assert align is None
        self._addInstruction("textBox", txt, box)

    # ---------------
    # Transformations
    # ---------------

    def transform(self, matrix, center=(0, 0)):
        if center != (0, 0):
            warnings.warn("center is not implemented.")
        self._addInstruction("transform", matrix)

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
            path = UIBezierPath.bezierPath()
        self._path = path

    # Pen

    def moveTo(self, point):
        self._path.moveToPoint_(CGPoint(*point))

    def lineTo(self, point):
        self._path.lineToPoint_(CGPoint(*point))

    def curveTo(self, *points):
        self._path.curveToPoint_controlPoint1_controlPoint2_(CGPoint(*points[2]), *points[0], *points[1])

    def closePath(self):
        self._path.closePath()

    def endPath(self):
        pass

    # Shapes

    def rect(self, x, y, w, h):
        sub = UIBezierPath.bezierPathWithRect_(CGRect(CGPoint(x, y), CGSize(w, h)))
        self._path.appendPath_(sub)

    def oval(self, x, y, w, h):
        sub = UIBezierPath.bezierPathWithOvalInRect_(CGRect(CGPoint(x, y), CGSize(w, h)))
        self._path.appendPath_(sub)

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

    # Path Testing and Properties

    def pointInside(self, point):
        return self._path.containsPoint_(CGPoint(*point))

    def bounds(self):
        (x, y), (w, h) = self._path.bounds()
        return (x, y, w, h)

    # Path Operations

    def copy(self):
        new = self.__class__()
        new.appendPath(self)
        return new

    def appendPath(self, otherPath):
        self._path.appendPath_(otherPath._path)

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
        if center != (0, 0):
            warnings.warn("center is not implemented.")
        transform = CGAffineTransform(*transformMatrix)
        self._path.applyTransform_(transform)


# -------
# Context
# -------

lineJoinStyles = dict(
    miter=kCGLineJoinMiter,
    round=kCGLineJoinRound,
    bevel=kCGLineJoinBevel
)
lineCapStyles = dict(
    butt=kCGLineCapButt,
    round=kCGLineCapRound,
    square=kCGLineCapSquare
)

class BaseContext(object):

    def __init__(self):
        self.stateStack = []
        self.state = GraphicsState()

    # ------------
    # Instructions
    # ------------

    # Colors

    def fill(self, r, g=None, b=None, a=1):
        if r is None:
            self.state.fillColor = None
            return
        self.state.fillColor = (r, g, b, a)

    def stroke(self, r, g=None, b=None, a=1):
        if r is None:
            self.state.strokeColor = None
            return
        self.state.strokeColor = (r, g, b, a)

    # Paths

    def drawPath(self, path):
        state = self.state
        if path is not None:
            state.path = path
        if state.path:
            path = state.path._path
            path.setMiterLimit_(state.miterLimit)
            path.setLineJoinStyle_(lineJoinStyles[state.lineJoin])
            path.setLineCapStyle_(lineCapStyles[state.lineCap])
            #if state.lineDash is not None:
            #    dash = state.lineDash
            #    count = len(dash)
            #    phase = 0
            #    path.setLineDash_count_phase_(dash, count, phase)
            if state.fillColor is not None:
                fillColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(*state.fillColor)
                fillColor.set()
                path.fill()
            if state.strokeColor is not None:
                strokeColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(*state.strokeColor)
                strokeColor.set()
                if state.strokeWidth is not None:
                    path.setLineWidth_(state.strokeWidth)
                path.stroke()

    # Path Properties

    def strokeWidth(self, value):
        self.state.strokeWidth = value

    def miterLimit(self, value):
        self.state.miterLimit = value

    def lineJoin(self, value):
        self.state.lineJoin = value

    def lineCap(self, value):
        self.state.lineCap = value

    def lineDash(self, value):
        if value[0] is None:
            value = None
        self.state.lineDash = value

    # Text

    def font(self, fontName, fontSize):
        self.state.text_fontName = fontName
        if fontSize is not None:
            self.state.text_fontSize = fontSize

    def fontSize(self, fontSize):
        self.state.text_fontSize = fontSize

    def textBox(self, txt, box):
        CGContextSaveGState(self._context)
        x, y, w, h = box
        self.transform((1, 0, 0, 1, x, y + h))
        self.transform((1, 0, 0, -1, 0, 0))
        font = None
        if self.state.text_fontName is not None:
            font = NSFont.fontWithName_size_(
                self.state.text_fontName,
                self.state.text_fontSize
            )
        if font is None:
            font = NSFont.systemFontOfSize_(self.state.text_fontSize)
        r, g, b, a = self.state.fillColor
        fillColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, a)
        attrs = {
            NSFontAttributeName : font,
            NSForegroundColorAttributeName : fillColor
        }
        string = NSAttributedString.alloc().initWithString_attributes_(txt, attrs)
        string.drawInRect_(((0, 0), (w, h)))
        CGContextRestoreGState(self._context)

    # States

    def save(self):
        self.stateStack.append(self.state.copy())
        CGContextSaveGState(self._context)

    def restore(self):
        if not self.stateStack:
            raise DrawBotError("can't restore graphics state: no matching save()'")
        self.state = self.stateStack.pop()
        CGContextRestoreGState(self._context)

    # Transformations

    def transform(self, transformMatrix):
        transform = CGAffineTransform(*transformMatrix)
        CGContextConcatCTM(self._context, transform)


class PNGContext(BaseContext):

    def __init__(self, width, height):
        super(PNGContext, self).__init__()
        UIGraphicsBeginImageContext(CGSize(width, height))
        self._context = UIGraphicsGetCurrentContext()
        self.transform((1, 0, 0, -1, 0, height))

    def imageData(self):
        image = UIGraphicsGetImageFromCurrentImageContext()
        UIGraphicsEndImageContext()
        png = UIImagePNGRepresentation(image)
        data = objc_util.nsdata_to_bytes(png)
        return data


# ----
# View
# ----

class DrawBotView(object):

    def __init__(self, imageData, mode):
        modes = dict(
            fullscreen="full_screen",
            sheet="sheet",
            popover="popover",
            panel="panel",
            sidebar="sidebar"
        )
        mode = modes[mode]
        self.image = ui.Image.from_data(imageData)
        width, height = self.image.size
        self.imageView = ui.ImageView(
            frame=(0, 0, width, height),
            background_color=1
        )
        self.imageView.image = self.image
        self.imageView.content_mode = ui.CONTENT_CENTER
        self.shareButton = ui.ButtonItem(
            image=ui.Image.named("iow:ios7_upload_outline_32")
        )
        self.shareButton.action = self.shareButtonCallback
        self.imageView.right_button_items = [self.shareButton]
        self.imageView.present(mode)

    def shareButtonCallback(self, sender):
        dialogs.share_image(self.image)


# ----
# Main
# ----

_drawBotDrawingTool = DrawBotDrawingTool()
_drawBotDrawingTool._addToNamespace(globals())

# ----
# Test
# ----

if __name__ == "__main__":
    bot = _drawBotDrawingTool

    bot.newDrawing()

    # origin
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

    # BezierPath
    path = BezierPath()
    for i in range(20):
        x = 300 * random()
        y = 300 * random()
        if i == 0:
            path.moveTo((x, y))
        else:
            path.lineTo((x, y))
    path.endPath()
    bot.fill(None)
    bot.stroke(1, 0, 0, 0.25)
    bot.strokeWidth(10)
    bot.drawPath(path)

    # scale
    bot.scale(3)
    bot.fill(None)
    bot.stroke(0, 0, 0, 1)
    bot.strokeWidth(1 / 3)
    bot.rect(0, 0, 100, 100)
    bot.endDrawing()

    # display
    bot.displayImage("sheet")
