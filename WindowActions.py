#!/usr/bin/env python3
# Copyright © 2020 Qtrac Ltd. All rights reserved.

import datetime
import platform
import sys

import wx
import wx.adv

import Const
import HelpForm


class Mixin:

    def onFind(self, _event=None):
        print('onFind') # TODO


    def onRefresh(self, _event=None):
        self.updateUi()
        self.sectionChoice.Clear()
        self.SetStatusText('Refreshing…')
        wx.CallLater(100, self.refresh)


    def refresh(self):
        self.model.load(self.onReady, refresh=True)
        self.updateSections()


    def onAbout(self, _event=None):
        app = wx.App.Get()
        info = wx.adv.AboutDialogInfo()
        info.Name = app.AppName
        info.Version = app.AppVersion
        info.Description = f'''\
A GUI application for finding Debian packages on Debian and Debian-based \
systems (such as Ubuntu).

Python {sys.version.split(None, 1)[0]}
wxPython {wx.version()}
{platform.platform()}
'''
        today = datetime.date.today()
        year = '2020' if today.year == 2020 else f'2020-{today:%y}'
        info.Copyright = f'''\
Copyright © {year} Qtrac Ltd. All Rights Reserved.
License: GPL-3.0.'''
        info.WebSite = 'https://github.com/mark-summerfield/debfind'
        wx.adv.AboutBox(info)


    def onHelp(self, _event=None):
        if self.helpForm is None:
            self.helpForm = HelpForm.Form(self)
        self.helpForm.Show()
        self.helpForm.Raise()
        self.helpForm.RequestUserAttention()


    def onQuit(self, _event=None):
        config = wx.Config(wx.App.Get().AppName)
        config.WriteInt(Const.CONFIG_WINDOW_X, self.Position.x)
        config.WriteInt(Const.CONFIG_WINDOW_Y, self.Position.y)
        config.WriteInt(Const.CONFIG_WINDOW_WIDTH, self.Size.Width)
        config.WriteInt(Const.CONFIG_WINDOW_HEIGHT, self.Size.Height)
        if self.helpForm:
            self.helpForm.Destroy()
        self.Destroy()
