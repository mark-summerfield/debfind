#!/usr/bin/env python3
# Copyright © 2020 Qtrac Ltd. All rights reserved.

import wx


class Window(wx.Frame):#, WindowActions.Mixin, WindowUi.Mixin):

    def __init__(self, *args, **kwargs):
        style = kwargs.get('style', wx.DEFAULT_DIALOG_STYLE)
        style |= wx.RESIZE_BORDER
        kwargs['style'] = style
        super().__init__(*args, **kwargs)
        self.MinSize = (640, 800)
        self.Title = wx.App.Get().AppName
        self.help_dialog = None
        #self.add_icons()
        #self.make_widgets()
        #self.make_status_bar()
        #self.make_layout()
        #self.make_bindings()
