import sys
import os
import json
import uuid


class SVGtoTTF:
    def convert(self, directory, outdir, config, metadata=None):
        print("SVGtoTTF")
        """Convert a directory with SVG images to TrueType Font.

        Calls a subprocess to the run this script with Fontforge Python
        environment.

        Parameters
        ----------
        directory : str
            Path to directory with SVGs to be converted.
        outdir : str
            Path to output directory.
        config : str
            Path to config file.
        metadata : dict
            Dictionary containing the metadata (filename, family or style)
        """
        import subprocess
        import platform

        subprocess.run(
            (
                ["ffpython"]
                if platform.system() == "Windows"
                else ["fontforge", "-script"]
            )
            + [
                os.path.abspath(__file__),
                config,
                directory,
                outdir,
                json.dumps(metadata),
            ]
        )

    def set_properties(self):
        """Set metadata of the font from config."""
        props = self.config["props"]
        lang = props.get("lang", "English (US)")
        fontname = self.metadata.get("filename", None) or props.get(
            "filename", "Example"
        )
        family = self.metadata.get("family", None) or fontname
        style = self.metadata.get("style", None) or props.get("style", "Regular")

        self.font.familyname = fontname
        self.font.fontname = fontname + "-" + style
        self.font.fullname = fontname + " " + style
        self.font.encoding = props.get("encoding", "UnicodeFull")

        for k, v in props.items():
            if hasattr(self.font, k):
                if isinstance(v, list):
                    v = tuple(v)
                setattr(self.font, k, v)

        if self.config.get("sfnt_names", None):
            self.config["sfnt_names"]["Family"] = family
            self.config["sfnt_names"]["Fullname"] = family + " " + style
            self.config["sfnt_names"]["PostScriptName"] = family + "-" + style
            self.config["sfnt_names"]["SubFamily"] = style

        self.config["sfnt_names"]["UniqueID"] = family + " " + str(uuid.uuid4())

        for k, v in self.config.get("sfnt_names", {}).items():
            self.font.appendSFNTName(str(lang), str(k), str(v))

    def add_glyphs(self, directory):
        """Read and add SVG images as glyphs to the font.

        Walks through the provided directory and uses each ord(character).svg file
        as glyph for the character. Then using the provided config, set the font
        parameters and export TTF file to outdir.

        Parameters
        ----------
        directory : str
            Path to directory with SVGs to be converted.
        """

        # print("Note: If you leave a glyph blank, you'll get a FontForge error like \"I'm")
        # print("      sorry this file is too complex for me to understand (or is erroneous)\".")
        # print("      It's fine, the font still works!")

        import psMat
        for glyph_object in self.config["glyphs-fancy"]:
            if 'name' in glyph_object:
                name = glyph_object['name']
                if 'codepoint' in glyph_object:
                    cp = int(glyph_object['codepoint'], 16)
                else:
                    cp = 0

                # Create character glyph
                if cp == 0:
                    g = self.font.createChar(-1, name)
                else:
                    g = self.font.createChar(cp, name)
                # Get outlines
                src = "{}/{}.svg".format(name, name)
                src = directory + os.sep + src

                # importOutlines() will print FontForge errors for blank glyphs.
                # Prepend what glyph they refer to.
                print("", end=("\r" + name.ljust(9, " ") + " - "))
                g.importOutlines(src, ("removeoverlap", "correctdir"))
                g.removeOverlap()

                # Vertically center sitelen pona
                # UCSUR:   pu & ku suli                    historical                      `.` and `:`
                if         0xf1900 <= cp <= 0xf1988   or   0xf19a0 <= cp <= 0xf19a3   or   0xf199c <= cp <= 0xf199d:
                    bottom = g.boundingBox()[1]
                    top    = g.boundingBox()[3]
                    g.transform(psMat.translate(
                        0, 
                        self.font.ascent - top - (self.font.ascent + self.font.descent - (top - bottom)) / 2
                    ))

                # Horizontally center sitelen pona, middot, colon, letters
                # UCSUR:   pu & ku suli                    historical                      `.` and `:`                     aeijklmnoptsuw
                if         0xf1900 <= cp <= 0xf1988   or   0xf19a0 <= cp <= 0xf19a3   or   0xf199c <= cp <= 0xf199d   or   0x61 <= cp <= 0x7a:
                    left  = g.boundingBox()[0]
                    right = g.boundingBox()[2]
                    width = right - left
                    g.transform(psMat.translate(
                        700 - right - (700 - width) / 2, 
                        0
                    ))

        # get rid of stray metrics
        print("\r                                                ")

        # originally 800x1000, minus 50 margin on each side for scanning margin
        # ...though the vertical situation might be more complicated?
        for glyph in self.font:
            self.font[glyph].width = 700
            self.font[glyph].vwidth = 900  # What does this actually do? Does ascent/descent control everything?

            # # Test centering
            # g = self.font[glyph]
            # # "If the glyph is not in the font’s encoding then a number will be returned beyond the encoding size (or in some cases -1 will be returned)."
            # # https://fontforge.org/docs/scripting/python/fontforge.html#fontforge.glyph.encoding
            # if 0 < g.encoding < 0x110000:
            #     cp = g.encoding
            # else:
            #     cp = 0
            # print(chr(cp), g.glyphname.ljust(9), "- " \
            # #     -50ish                             750ish
            #       "left",   int(g.boundingBox()[0]), "right", int(g.boundingBox()[2]), \
            # #     -200ish                            800ish
            #       "bottom", int(g.boundingBox()[1]), "top",   int(g.boundingBox()[3]))

        # combining cartouche extension
        self.font[0xf1992].width = 0
        self.font[0xf1992].transform(psMat.translate(-700, 0))

        bang = self.font.createMappedChar(ord("!"))
        bang.width = 0
        space = self.font.createMappedChar(ord(" "))
        space.width = 350
        comma = self.font.createMappedChar(ord(","))
        comma.width = 0
        question = self.font.createMappedChar(ord("?"))
        question.width = 0
        ideographic_space = self.font.createMappedChar(ord("　"))
        ideographic_space.width = 700

    def set_bearings(self):
        """Add left and right bearing
        """

        for glyph in self.font:
            print(glyph)
            self.font[glyph].left_side_bearing = 0  # Generally a value between -100, 100.
            self.font[glyph].right_side_bearing = 0 # 0 makes the glyphs touch. Maybe add like 50

    def set_kerning(self, table):
        """Set kerning values in the font.

        Parameters
        ----------
        table : dict
            Config dictionary with kerning values/autokern bool.
        """
        rows = table["rows"]
        rows = [list(i) if i != None else None for i in rows]
        cols = table["cols"]
        cols = [list(i) if i != None else None for i in cols]

        self.font.addLookup("kern", "gpos_pair", 0, [["kern", [["latn", ["dflt"]]]]])

        if table.get("autokern", True):
            self.font.addKerningClass(
                "kern", "kern-1", table.get("seperation", 0), rows, cols, True
            )
        else:
            kerning_table = table.get("table", False)
            if not kerning_table:
                raise ValueError("Kerning offsets not found in the config file.")
            flatten_list = (
                lambda y: [x for a in y for x in flatten_list(a)]
                if type(y) is list
                else [y]
            )
            offsets = [0 if x is None else x for x in flatten_list(kerning_table)]
            self.font.addKerningClass("kern", "kern-1", rows, cols, offsets)

    def generate_font_file(self, filename, outdir, config_file):
        """Output TTF file.

        Additionally checks for multiple outputs and duplicates.

        Parameters
        ----------
        filename : str
            Output filename.
        outdir : str
            Path to output directory.
        config_file : str
            Path to config file.
        """
        if filename is None:
            raise NameError("filename not found in config file.")

        outfile = str(
            outdir
            + os.sep
            + (filename + ".ttf" if not filename.endswith(".ttf") else filename)
        )

        while os.path.exists(outfile):
            outfile = os.path.splitext(outfile)[0] + " (1).ttf"

        sys.stderr.write("\nGenerating %s...\n" % outfile)
        self.font.generate(outfile)
        self.font.save(outfile + ".sfd")

    def convert_main(self, config_file, directory, outdir, metadata):
        try:
            self.font = fontforge.font()
        except:
            import fontforge
            import psMat

# START OF KELLY ZONE

        # Now that FontForge is imported, thanks to surprisingly complicated incantations at the top of the file,
        # import the .sfd and examine its lookup tables.

        # structure code around glyph names, not codepoints
        # also fix vertical centering, and add FontForge file (.sfd) export

# END OF KELLY ZONE

        with open(config_file) as f:
            self.config = json.load(f)
        self.metadata = json.loads(metadata) or {}

        self.font = fontforge.font()
        self.set_properties()
        self.add_glyphs(directory)

        # bearing table
        # Bearings position the glyph relative to the edges of the glyph's drawing.
        # This is useful for variable-width fonts, but not for monospaced fonts.
        # self.set_bearings(self.config["typography_parameters"].get("bearing_table", {}))

        # kerning table
        # self.set_kerning(self.config["typography_parameters"].get("kerning_table", {}))

        # Generate font and save as a .ttf file
        filename = self.metadata.get("filename", None) or self.config["props"].get(
            "filename", None
        )
        self.generate_font_file(str(filename), outdir, config_file)


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise ValueError("Incorrect call to SVGtoTTF")
    SVGtoTTF().convert_main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
