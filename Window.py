#!/usr/bin/env python3
# Copyright © 2020 Qtrac Ltd. All rights reserved.

import wx

import Model
import WindowActions
import WindowUtil


class Window(wx.Frame, WindowActions.Mixin, WindowUtil.Mixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Title = wx.App.Get().AppName
        self.helpForm = None
        self.addIcons()
        self.makeWidgets()
        self.makeLayout()
        self.makeBindings()
        self.setPositionAndSize()
        self.descEdit.SetFocus()
        self.updateUi()
        wx.CallAfter(self.fixLayout)
        wx.CallLater(100, self.loadModel)


    def makeWidgets(self):
        self.panel = wx.Panel(self)
        self.descLabel = wx.StaticText(self.panel,
                                       label='Name and D&escription')
        self.descEdit = wx.TextCtrl(self.panel)
        self.descAllRadio = wx.RadioButton(self.panel, label='All &Words',
                                           style=wx.RB_GROUP)
        self.descAnyRadio = wx.RadioButton(self.panel, label='Any W&ords')
        self.nameLabel = wx.StaticText(self.panel, label='&Name Only')
        self.nameEdit = wx.TextCtrl(self.panel)
        self.nameAllRadio = wx.RadioButton(self.panel, label='All Wor&ds',
                                           style=wx.RB_GROUP)
        self.nameAnyRadio = wx.RadioButton(self.panel, label='Any Word&s')
        self.sectionLabel = wx.StaticText(self.panel, label='Se&ction')
        self.sectionChoice = wx.Choice(self.panel)
        self.librariesCheckbox = wx.CheckBox(self.panel,
                                             label='Include &Libraries')
        self.findButton = wx.Button(self.panel, wx.ID_FIND)
        self.refreshButton = wx.Button(self.panel, wx.ID_REFRESH)
        self.aboutButton = wx.Button(self.panel, wx.ID_ABOUT)
        self.helpButton = wx.Button(self.panel, wx.ID_HELP)
        self.quitButton = wx.Button(self.panel, wx.ID_EXIT)
        self.splitter = wx.SplitterWindow(self.panel, style=wx.SP_3DSASH)
        self.debsListCtrl = WindowUtil.ListCtrl(self.splitter)
        self.debTextCtrl = wx.TextCtrl(self.splitter,
                                       style=wx.TE_MULTILINE | wx.TE_RICH2)
        self.splitter.SplitVertically(self.debsListCtrl, self.debTextCtrl)
        self.CreateStatusBar()


    def makeLayout(self):
        flag = wx.ALL
        flagX = wx.ALL | wx.EXPAND
        border = 3
        grid = wx.GridBagSizer()
        grid.Add(self.descLabel, (0, 0), flag=flag, border=border)
        grid.Add(self.descEdit, (0, 1), (1, 2), flag=flagX, border=border)
        grid.Add(self.descAllRadio, (0, 3), flag=flag, border=border)
        grid.Add(self.descAnyRadio, (0, 4), flag=flag, border=border)
        grid.Add(self.quitButton, (0, 5), flag=flagX, border=border)
        grid.Add(self.nameLabel, (1, 0), flag=flag, border=border)
        grid.Add(self.nameEdit, (1, 1), (1, 2), flag=flagX, border=border)
        grid.Add(self.nameAllRadio, (1, 3), flag=flag, border=border)
        grid.Add(self.nameAnyRadio, (1, 4), flag=flag, border=border)
        grid.Add(self.refreshButton, (1, 5), flag=flagX, border=border)
        grid.Add(self.sectionLabel, (2, 0), flag=flag, border=border)
        grid.Add(self.sectionChoice, (2, 1), flag=flagX, border=border)
        grid.Add(self.librariesCheckbox, (2, 2), flag=flag, border=border)
        grid.Add(self.findButton, (2, 3), flag=flagX, border=border)
        grid.Add(self.helpButton, (2, 4), flag=flagX, border=border)
        grid.Add(self.aboutButton, (2, 5), flag=flagX, border=border)
        grid.Add(self.splitter, (3, 0), (1, 6), flag=flagX, border=border)
        grid.AddGrowableCol(1)
        grid.AddGrowableCol(2)
        grid.AddGrowableRow(3)
        self.panel.SetSizer(grid)
        self.panel.Fit()


    def makeBindings(self):
        # TODO when the user navigates the ListCtrl show the current Deb in
        # the TextCtrl (or blank it)
        self.findButton.Bind(wx.EVT_BUTTON, self.onFind)
        self.refreshButton.Bind(wx.EVT_BUTTON, self.onRefresh)
        self.aboutButton.Bind(wx.EVT_BUTTON, self.onAbout)
        self.helpButton.Bind(wx.EVT_BUTTON, self.onHelp)
        self.quitButton.Bind(wx.EVT_BUTTON, self.onQuit)
        self.Bind(wx.EVT_CLOSE, self.onQuit)
        self.Bind(wx.EVT_CHAR_HOOK, self.onChar)


    def onChar(self, event):
        code = event.GetKeyCode()
        key = chr(code)
        if code == wx.WXK_F1:
            self.onHelp()
        elif event.AltDown and key in 'cC':
            self.sectionChoice.SetFocus()
        else:
            event.Skip()


    def fixLayout(self):
        self.splitter.SetSashPosition(self.splitter.Size.width // 2)
        self.MinSize = self.BestSize


    def updateUi(self, enable=False):
        self.findButton.Enable(enable)
        self.refreshButton.Enable(enable)
        self.debsListCtrl.Enable(enable)
        self.debTextCtrl.Enable(enable)


    def loadModel(self):
        self.model = Model.Model(self.onReady)
        self.updateSections()


    def onReady(self, message, done):
        self.SetStatusText(message)
        if done:
            self.updateUi(True)


    def updateSections(self):
        self.sectionChoice.Set(sorted(self.model.allSections))
        self.sectionChoice.Insert(['(Any)'], 0)
        self.sectionChoice.Selection = 0
