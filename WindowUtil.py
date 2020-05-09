#!/usr/bin/env python3
# Copyright © 2020 Qtrac Ltd. All rights reserved.

import wx

import Const
import Icons


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
