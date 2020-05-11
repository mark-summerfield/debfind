#!/usr/bin/env python3
# Copyright © 2020 Qtrac Ltd. All rights reserved.

import wx
import wx.html


HTML_TEXT = '''<html><body style="background-color: {bg};">
<h2><center><b><font color="white">DebFind</font></b></center></h2>
<p>
<font color="brown"><b>
A GUI application for finding Debian packages on Debian and Debian-based
systems (such as Ubuntu).</b>
</p>
</font>
</p>
<p>
<font color="navy">
The easiest way to use DebFind is to enter one or more words in the Name
and Description line editor and click Find. By default only those packages
whose name and description contains <i>all</i> the (stemmed) words are
found. Click Any Words if any matching word will do.
</p>
<p>
If you want to search within a particular section choose a section; if you
want to find libraries as well as applications, check the Include Libraries
check box.
</p>
<p>
At startup on the first run of the session, DebFind reads and indexes all
the Debian Packages files. On subsequent runs in the same session DebFind
will use a cache to speed up loading. If you update the Debian packages and
want DebFind to use fresh data, click Refresh.
</p>
</font>
</p>
</body></html>'''


class Form(wx.Dialog):

    def __init__(self, *args, **kwargs):
        style = kwargs.get('style', wx.DEFAULT_DIALOG_STYLE)
        style |= wx.RESIZE_BORDER
        kwargs['style'] = style
        super().__init__(*args, **kwargs)
        self.Title = 'Help — ' + wx.App.Get().AppName
        self.makeWidgets()
        self.makeLayout()
        self.makeBindings()
        self.okButton.SetFocus()
        self.MinSize = (200, 200)
        self.Size = (400, 450)


    def makeWidgets(self):
        bg = wx.SystemSettings.GetColour(
            wx.SYS_COLOUR_BTNFACE).GetAsString(wx.C2S_HTML_SYNTAX)
        self.htmlLabel = wx.html.HtmlWindow(self)
        if 'gtk2' in wx.PlatformInfo or 'gtk3' in wx.PlatformInfo:
            self.htmlLabel.SetStandardFonts()
        self.htmlLabel.SetPage(HTML_TEXT.format(bg=bg))
        self.okButton = wx.Button(self, wx.ID_OK)


    def makeLayout(self):
        flag = wx.ALL | wx.EXPAND
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.htmlLabel, 1, flag=flag, border=3)
        sizer.Add(self.okButton, 0, flag=wx.ALL | wx.ALIGN_CENTER,
                  border=3)
        self.SetSizer(sizer)
        self.Fit()


    def makeBindings(self):
        self.Bind(wx.EVT_CHAR_HOOK, self.on_char)
        self.Bind(wx.EVT_CLOSE, self.on_close)


    def on_char(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_ESCAPE:
            self.on_close()
        else:
            event.Skip()


    def on_close(self, _event=None):
        self.Hide()
