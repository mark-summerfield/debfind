#!/usr/bin/env python3
# Copyright © 2020 Qtrac Ltd. All rights reserved.

import datetime
import platform
import sys

import wx
import wx.adv

import Const
import HelpForm
import Model


class Mixin:

    def onFind(self, _event=None):
        self.debTextCtrl.Clear()
        self.debsListCtrl.ClearAll()
        section = self.sectionChoice.GetString(
            self.sectionChoice.CurrentSelection)
        if section == Const.ANY_SECTION:
            section = ''
        descMatch = (Model.Match.ANY_WORD if self.descAnyRadio.Value else
                     Model.Match.ALL_WORDS)
        nameMatch = (Model.Match.ANY_WORD if self.nameAnyRadio.Value else
                     Model.Match.ALL_WORDS)
        query = Model.Query(
            section=section, descriptionWords=self.descEdit.Value,
            descriptionMatch=descMatch, nameWords=self.nameEdit.Value,
            nameMatch=nameMatch,
            includeLibraries=self.librariesCheckbox.Value)
        names = self.model.query(query)
        if names:
            if len(names) == 1:
                self.SetStatusText('Found one matching package.')
            else:
                self.SetStatusText(
                    f'Found {len(names):,d} matching packages.')
            self.debsListCtrl.AppendColumn('Name')
            self.debsListCtrl.AppendColumn('Description')
            self.debsListCtrl.AlternateRowColour = True
            self.debsListCtrl.setResizeColumn(1)
            for name in names:
                self.debsListCtrl.Append(
                    (name, self.model.descriptionFor(name)))
            # width = self.debsListCtrl.Size.width
            # self.debsListCtrl.resizeColumn(width // 4)
            # TODO adjust/expand columns
            # TODO select first (which should update debTextCtrl)
        else:
            self.SetStatusText('No matching packages found.')


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
