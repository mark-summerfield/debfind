#!/usr/bin/env python3
# Copyright © 2020 Qtrac Ltd. All rights reserved.

import html
import webbrowser

import wx
import wx.html


class DebView(wx.html.HtmlWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'gtk2' in wx.PlatformInfo or 'gtk3' in wx.PlatformInfo:
            self.SetStandardFonts()
        self.clear()


    def clear(self):
        self.SetPage(UNSELECTED_HTML)


    def OnCellClicked(self, cell, x, y, event):
        if isinstance(cell, wx.html.HtmlWordCell):
            selection = wx.html.HtmlSelection()
            text = cell.ConvertToText(selection)
            if text.startswith(('http://', 'https://')):
                webbrowser.open(text)
        return super().OnCellClicked(cell, x, y, event)


    def showDeb(self, deb):
        size = deb.size # TODO B | KB | MB | GB
        description = ('<p>' + html.escape(deb.description)
                                   .replace('\n\n', '</p><p>') + '</p>')
        self.SetPage(DEB.format(
            name=html.escape(deb.name), version=html.escape(deb.ver),
            size=size, url=deb.url, section=html.escape(deb.section),
            description=description))


UNSELECTED_HTML = '''<html><body><body style="background-color: white;">
<p><center><font color="gray">(No package selected.)</font></center></p>
</body></html>'''

DEB = '''<html><body><body style="background-color: white;">
<p><center><font color="navy"><b>{name}</b></font></center></p>
<p><center>v{version} &bull; {size}</center></p>
<p><center><font color="darkgreen"><u>{url}</u></font></center></p>
<p><center>Section: {section}</center></p>
{description}
</body></html>'''
