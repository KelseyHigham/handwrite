from PIL import Image, ImageChops
import os
import shutil
import subprocess


class PotraceNotFound(Exception):
    pass


class PNGtoSVG:
    """Converter class to convert character PNGs to BMPs and SVGs."""

    def convert(self, directory):
        print("PNGtoSVG", end="\r")
        """Call converters on each .png in the provider directory.

        Walk through the custom directory containing all .png files
        from sheettopng and convert them to png -> bmp -> svg.
        """
        num_characters = 0
        path = os.walk(directory)
        for root, dirs, files in path:
            for f in files:
                if f.endswith(".png"):
                    num_characters += 1
                    print("PNGtoSVG", str(f[0:-4]).ljust(14, " ")[:14], "".join("." for i in range(num_characters//8)), end="\r")
                    self.pngToBmp(root + "/" + f)
                    # self.trim(root + "/" + f[0:-4] + ".bmp")
                    self.bmpToSvg(root + "/" + f[0:-4] + ".bmp")
        print("PNGtoSVG                                                                      ")

    def bmpToSvg(self, path):
        """Convert .bmp image to .svg using potrace.

        Converts the passed .bmp file to .svg using the potrace
        (http://potrace.sourceforge.net/). Each .bmp is passed as
        a parameter to potrace which is called as a subprocess.

        Parameters
        ----------
        path : str
            Path to the bmp file to be converted.

        Raises
        ------
        PotraceNotFound
            Raised if potrace not found in path by shutil.which()
        """
        if shutil.which("potrace") is None:
            raise PotraceNotFound("Potrace is either not installed or not in path")
        else:
            subprocess.run(["potrace", path, "--backend", "svg", "--output", path[0:-4] + ".svg",])
            # note: the --margin parameter doesn't help me here

    def pngToBmp(self, path):
        """Convert .bmp image to .svg using potrace.

        Converts the passed .bmp file to .svg using the potrace
        (http://potrace.sourceforge.net/). Each .bmp is passed as
        a parameter to potrace which is called as a subprocess.

        Parameters
        ----------
        path : str
            Path to the bmp file to be converted.

        Raises
        ------
        PotraceNotFound
            Raised if potrace not found in path by shutil.which()
        """
        glyph_width  = 100
        glyph_height = 125
        img = Image.open(path).convert("RGBA").resize((glyph_width, glyph_height))
        # print("size:", glyph_width, glyph_height)

        # Threshold image to convert each pixel to either black or white
        threshold = 200
        data = []
        for pix in list(img.getdata()):
            if pix[0] >= threshold and pix[1] >= threshold and pix[3] >= threshold:
                data.append((255, 255, 255, 0))
            else:
                data.append((0, 0, 0, 1))
        img.putdata(data)
        img.save(path[0:-4] + ".bmp")

    def trim(self, im_path):
        im = Image.open(im_path)
        bg = Image.new(im.mode, im.size, im.getpixel((0, 0)))
        diff = ImageChops.difference(im, bg)
        bbox = list(diff.getbbox())
        bbox[0] -= 1
        bbox[1] -= 1
        bbox[2] += 1
        bbox[3] += 1
        cropped_im = im.crop(bbox)
        cropped_im.save(im_path)
