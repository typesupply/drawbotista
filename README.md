# drawbotista

This is a port of a subset of the [DrawBot API](https://www.drawbot.com) to [Pythonista](http://omz-software.com/pythonista/index.html).


## To Do:

- `text`
- `lineDash`


## API

The API is currently focused on compatibility with DrawBot's static 2D image capabilities. PRs for more of the API is welcome.

### Extra API:

A couple of drawbotista specific functions have been added:

#### `displayImage(mode="screen")`

Display the generated image on screen. The display modes are:

- `"fullscreen"`
- `"sheet"`
- `"popover"`
- `"panel"`
- `"sidebar"`

#### `imageData(format="PNG")`

Returns image data. `"PNG"` is the only supported format.


### Supported DrawBot API:

Refer to the DrawBot documentation for details on these. Not all functionality for some of these is supported.

#### Functions

- `size`
- `width`
- `height`
- `save`
- `restore`
- `savedState`
- `fill`
- `stroke`
- `rect`
- `oval`
- `polygon`
- `line`
- `strokeWidth`
- `miterLimit`
- `lineJoin`
- `lineCap`
- `font`
- `fontSize`
- `textBox`
- `transform`
- `translate`
- `rotate`
- `scale`
- `skew`
- `BezierPath`

#### BezierPath

- `moveTo`
- `lineTo`
- `curveTo`
- `closePath`
- `endPath`
- `rect`
- `oval`
- `line`
- `polygon`
- `pointInside`
- `bounds`
- `copy`
- `appendPath`
- `translate`
- `rotate`
- `scale`
- `skew`
- `transform`
