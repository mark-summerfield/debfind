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
        size = sizeof_fmt(deb.size, decs=0)
        shortDesc, desc = deb.desc.split('\n', 1)
        shortDesc = html.escape(shortDesc)
        desc = ('<p>' + html.escape(desc).replace('\v+', '<ul>')
                .replace('\t', '<li>').replace('\v-', '</ul>')
                .replace('\n', '</p><p>') + '</p>')
        self.SetPage(DEB.format(
            name=html.escape(deb.name), version=html.escape(deb.version),
            size=size, url=deb.url, section=html.escape(deb.section),
            shortDesc=shortDesc, desc=desc))


def sizeof_fmt(num, *, decs=3, suffix='B'):
    for unit in ('', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi'):
        if abs(num) < 1024.0:
            return f'{num:3.{decs}f}{unit}{suffix}'
        num /= 1024.0
    return f'{num:3.{decs}f}Yi{suffix}'


UNSELECTED_HTML = '''<html><body><body style="background-color: white;">
<p><center><font color="gray">(No package selected.)</font></center></p>
</body></html>'''

DEB = '''<html><body><body style="background-color: white;">
<p><center><font color="navy"><b>{name}</b></font></center></p>
<p><center><font color="navy">{shortDesc}</font></center></p>
{desc}
<hr>
<center>v{version} &bull; {size} &bull; {section}</center>
</body></html>'''
