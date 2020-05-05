#!/usr/bin/env python3
# Copyright © 2020 Qtrac Ltd. All rights reserved.

import wx
import wx.lib.mixins.listctrl

import Const
import Icons


class ListCtrl(wx.ListCtrl, wx.lib.mixins.listctrl.ListCtrlAutoWidthMixin):

    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES |
                 wx.LC_VRULES):
        super().__init__(parent, id, pos, size, style)
        wx.lib.mixins.listctrl.ListCtrlAutoWidthMixin.__init__(self)


class Mixin:

    def addIcons(self):
        icons = wx.IconBundle()
        icons.AddIcon(Icons.icon16.Icon)
        icons.AddIcon(Icons.icon32.Icon)
        icons.AddIcon(Icons.icon48.Icon)
        icons.AddIcon(Icons.icon256.Icon)
        self.SetIcons(icons)


    def setPositionAndSize(self):
        config = wx.Config(wx.App.Get().AppName)
        x = config.ReadInt(Const.CONFIG_WINDOW_X, 0)
        y = config.ReadInt(Const.CONFIG_WINDOW_Y, 0)
        self.Position = (x, y)
        width = config.ReadInt(Const.CONFIG_WINDOW_WIDTH, 320)
        height = config.ReadInt(Const.CONFIG_WINDOW_HEIGHT, 240)
        self.Size = (width, height)
