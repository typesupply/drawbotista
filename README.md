# drawbotista

This is a port of as much of the [DrawBot API](https://www.drawbot.com) to [Pythonista](http://omz-software.com/pythonista/index.html) as possible/needed.

To do:
- This currently wraps UIView as thedrawoing context. That means taht images can't be saved. An upgrade would be to use Imageas the context. An even better upgrade would be to wrap CoreGraphics as the context. That might be possible with objc_util and ctypes.
- I've only implemented very basic things so far. I've been more focused on getting this working than making it complete.
