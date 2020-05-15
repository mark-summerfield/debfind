#!/usr/bin/env python3
# Copyright © 2020 Qtrac Ltd. All rights reserved.

import html
import webbrowser

import wx
import wx.html


class DebView(wx.html.HtmlWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        desc = ('<p>' + html.escape(deb.desc).replace('\n', '</p><p>') +
                '</p>')
        self.SetPage(DEB.format(
            name=html.escape(deb.name), version=html.escape(deb.version),
            size=size, url=deb.url, section=html.escape(deb.section),
            desc=desc))


UNSELECTED_HTML = '''<html><body><body style="background-color: white;">
<p><center><font color="gray">(No package selected.)</font></center></p>
</body></html>'''

DEB = '''<html><body><body style="background-color: white;">
<p><center><font color="navy"><b>{name}</b></font></center></p>
<p><center>v{version} &bull; {size}</center></p>
<p><center><font color="darkgreen"><u>{url}</u></font></center></p>
{desc}
<hr>
<center>Section: {section}</center>
</body></html>'''
