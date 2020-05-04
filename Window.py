#!/usr/bin/env python3
# Copyright © 2020 Qtrac Ltd. All rights reserved.

import wx

import Icons


class Window(wx.Frame):

    def __init__(self, *args, **kwargs):
        style = kwargs.get('style', wx.DEFAULT_DIALOG_STYLE)
        style |= wx.RESIZE_BORDER
        kwargs['style'] = style
        super().__init__(*args, **kwargs)
        self.MinSize = (320, 240)
        self.Title = wx.App.Get().AppName
        self.help_dialog = None
        self.add_icons()
        # TODO self.make_widgets()
        # TODO self.make_status_bar()
        # TODO self.make_layout()
        # TODO self.make_bindings()
        # TODO load config (win size/pos)


    def add_icons(self):
        icons = wx.IconBundle()
        icons.AddIcon(Icons.icon16.Icon)
        icons.AddIcon(Icons.icon32.Icon)
        icons.AddIcon(Icons.icon48.Icon)
        icons.AddIcon(Icons.icon256.Icon)
        self.SetIcons(icons)
