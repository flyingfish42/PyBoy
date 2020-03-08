#
# License: See LICENSE file
# GitHub: https://github.com/Baekalfen/PyBoy
#

"""
This class gives access to the frame buffer and other screen parameters of PyBoy.
"""

import numpy as np
from PIL import Image
from pyboy.logger import logger

from .constants import COLS, ROWS


class Screen:
    """
    As part of the emulation, we generate a screen buffer in 32-bit RGBA format. This class has several helper methods
    to make it possible to read this buffer out.

    If you're making an AI or bot, it's highly recommended to _not_ use this class for detecting objects on the screen.
    It's much more efficient to use `pyboy.PyBoy.get_tilemap_background`, `pyboy.PyBoy.get_tilemap_window`, and
    `pyboy.PyBoy.get_sprite` instead.
    """
    def __init__(self, mb):
        self.mb = mb

    def get_tilemap_position(self):
        """
        These coordinates define the offset in the tile map from where the top-left corner of the screen is place. Note
        that the tile map defines 256x256 pixels, but the screen can only show 160x144 pixels. When the offset is closer
        to the right or bottom edge than 160x144 pixels, the screen will wrap around and render from the opposite site
        of the tile map.

        For more details, see "7.4 Viewport" in the [report](https://github.com/Baekalfen/PyBoy/raw/master/PyBoy.pdf),
        or the Pan Docs under [LCD Position and Scrolling](http://bgb.bircd.org/pandocs.htm#lcdpositionandscrolling).

        Returns:
            ((int, int), (int, int)): Returns the registers (SCX, SCY), (WX - 7, WY)
        """
        return (self.mb.lcd.getviewport(), self.mb.lcd.getwindowpos())

    def get_tilemap_position_list(self):
        """
        This function provides the screen (SCX, SCY) and window (WX. WY) position for each horizontal line in the
        screen buffer. These parameters are often used for visual effects, and some games will reset the registers at
        the end of each call to `pyboy.PyBoy.tick()`. For such games, `Screen.get_tilemap_position` becomes useless.

        See `Screen.get_tilemap_position` for more information.

        Returns:
            numpy.ndarray: SCX, SCY, WX and WY for each scanline (144, 4).
        """
        return np.vstack(
            [
                np.array([line[0], line[1], line[2], line[3]], dtype=np.uint8)
                for line in self.mb.renderer._scanlineparameters
                ]
            )

    def get_raw_screen_buffer(self):
        """
        Provides a raw, unfiltered `bytes` object with the data from the screen. Check
        `Screen.get_raw_screen_buffer_format` to see which dataformat is used. The returned type and dataformat are
        subject to change.

        Use this, only if you need to bypass the overhead of `Screen.get_screen_image` or `Screen.get_screen_ndarray`.

        Returns:
            bytes: 92160 bytes of screen data in a `bytes` object.
        """
        return self.mb.renderer._screenbuffer_raw.tobytes()

    def get_raw_screen_buffer_dims(self):
        """
        Returns the dimensions of the raw screen buffer.

        Returns:
            tuple: A two-tuple of the buffer dimensions. E.g. (160, 144).
        """
        return self.mb.renderer.buffer_dims

    def get_raw_screen_buffer_format(self):
        """
        Returns the color format of the raw screen buffer.

        Returns:
            str: Color format of the raw screen buffer. E.g. 'RGB'.
        """
        return self.mb.renderer.color_format

    def get_screen_ndarray(self):
        """
        Provides the screen data in NumPy format. The dataformat is always RGB.

        Returns:
            numpy.ndarray: Screendata in `ndarray` of bytes with shape (160, 144, 3)
        """
        return np.frombuffer(self.get_raw_screen_buffer(), dtype=np.uint8).reshape(ROWS, COLS, 4)[:, :, 1:]
        # return self.mb.renderer.get_screen_buffer_as_ndarray()

    def get_screen_image(self):
        """
        Generates a PIL Image from the screen buffer.

        Convenient for screen captures, but might be a bottleneck, if you use it to train a neural network. In which
        case, read up on the `pyboy.botsupport` features, [Pan Docs](http://bgb.bircd.org/pandocs.htm) on tiles/sprites,
        and join our Discord channel for more help.

        Returns:
            PIL.Image: RGB image of (160, 144) pixels
        """
        if not Image:
            logger.warning("Cannot generate screen image. Missing dependency \"Pillow\".")
            return None

        # NOTE: Might have room for performance improvement
        # It's not possible to use the following, as the byte-order (endianess) isn't supported in Pillow
        # Image.frombytes('RGBA', self.buffer_dims, self.get_screen_buffer()).show()
        return Image.fromarray(self.get_screen_ndarray(), 'RGB')
