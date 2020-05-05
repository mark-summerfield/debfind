#!/usr/bin/env python3
# Copyright © 2020 Qtrac Ltd. All rights reserved.

import wx
import wx.lib.mixins.listctrl

import Icons


CONFIG_WINDOW_HEIGHT = 'Window/Height'
CONFIG_WINDOW_WIDTH = 'Window/Width'
CONFIG_WINDOW_X = 'Window/X'
CONFIG_WINDOW_Y = 'Window/Y'


class ListCtrl(wx.ListCtrl, wx.lib.mixins.listctrl.ListCtrlAutoWidthMixin):

    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES |
                 wx.LC_VRULES):
        super().__init__(parent, id, pos, size, style)
        wx.lib.mixins.listctrl.ListCtrlAutoWidthMixin.__init__(self)


class Window(wx.Frame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.MinSize = (320, 240)
        self.Title = wx.App.Get().AppName
        self.help_dialog = None
        self.add_icons()
        self.make_widgets()
        self.make_layout()
        self.make_bindings()
        self.set_position_and_size()
        self.desc_edit.SetFocus()
        wx.CallAfter(self.fixSplitter)


    def add_icons(self):
        icons = wx.IconBundle()
        icons.AddIcon(Icons.icon16.Icon)
        icons.AddIcon(Icons.icon32.Icon)
        icons.AddIcon(Icons.icon48.Icon)
        icons.AddIcon(Icons.icon256.Icon)
        self.SetIcons(icons)


    def make_widgets(self):
        self.panel = wx.Panel(self)
        self.desc_label = wx.StaticText(self.panel,
                                        label='Name and D&escription')
        self.desc_edit = wx.TextCtrl(self.panel)
        self.desc_all_radio = wx.RadioButton(self.panel, label='All &Words',
                                             style=wx.RB_GROUP)
        self.desc_any_radio = wx.RadioButton(self.panel, label='Any W&ords')
        self.name_label = wx.StaticText(self.panel, label='&Name Only')
        self.name_edit = wx.TextCtrl(self.panel)
        self.name_all_radio = wx.RadioButton(self.panel, label='All Wor&ds',
                                             style=wx.RB_GROUP)
        self.name_any_radio = wx.RadioButton(self.panel, label='Any Word&s')
        self.section_label = wx.StaticText(self.panel, label='Se&ction')
        self.section_choice = wx.Choice(self.panel)
        self.libraries_checkbox = wx.CheckBox(self.panel,
                                              label='Include &Libraries')
        self.find_button = wx.Button(self.panel, wx.ID_FIND)
        self.refresh_button = wx.Button(self.panel, wx.ID_REFRESH)
        self.about_button = wx.Button(self.panel, wx.ID_ABOUT)
        self.help_button = wx.Button(self.panel, wx.ID_HELP)
        self.quit_button = wx.Button(self.panel, wx.ID_EXIT)
        self.splitter = wx.SplitterWindow(self.panel, style=wx.SP_3DSASH)
        self.debs_listctrl = ListCtrl(self.splitter)
        self.deb_textctrl = wx.TextCtrl(self.splitter,
                                        style=wx.TE_MULTILINE | wx.TE_RICH2)
        self.splitter.SplitVertically(self.debs_listctrl, self.deb_textctrl)
        self.CreateStatusBar()


    def make_layout(self):
        flag = wx.ALL
        flag_x = wx.ALL | wx.EXPAND
        border = 3
        grid = wx.GridBagSizer()
        grid.Add(self.desc_label, (0, 0), flag=flag, border=border)
        grid.Add(self.desc_edit, (0, 1), (1, 2), flag=flag_x, border=border)
        grid.Add(self.desc_all_radio, (0, 3), flag=flag, border=border)
        grid.Add(self.desc_any_radio, (0, 4), flag=flag, border=border)
        grid.Add(self.quit_button, (0, 5), flag=flag, border=border)
        grid.Add(self.name_label, (1, 0), flag=flag, border=border)
        grid.Add(self.name_edit, (1, 1), (1, 2), flag=flag_x, border=border)
        grid.Add(self.name_all_radio, (1, 3), flag=flag, border=border)
        grid.Add(self.name_any_radio, (1, 4), flag=flag, border=border)
        grid.Add(self.refresh_button, (1, 5), flag=flag, border=border)
        grid.Add(self.section_label, (2, 0), flag=flag, border=border)
        grid.Add(self.section_choice, (2, 1), flag=flag_x, border=border)
        grid.Add(self.libraries_checkbox, (2, 2), flag=flag, border=border)
        grid.Add(self.find_button, (2, 3), flag=flag, border=border)
        grid.Add(self.help_button, (2, 4), flag=flag, border=border)
        grid.Add(self.about_button, (2, 5), flag=flag, border=border)
        grid.Add(self.splitter, (3, 0), (1, 6), flag=flag_x, border=border)
        grid.AddGrowableCol(1)
        grid.AddGrowableCol(2)
        grid.AddGrowableRow(3)
        self.panel.SetSizer(grid)
        self.panel.Fit()


    def make_bindings(self):
        # TODO
        self.quit_button.Bind(wx.EVT_BUTTON, self.on_quit)
        self.Bind(wx.EVT_CLOSE, self.on_quit)


    def set_position_and_size(self):
        config = wx.Config(wx.App.Get().AppName)
        x = config.ReadInt(CONFIG_WINDOW_X, 0)
        y = config.ReadInt(CONFIG_WINDOW_Y, 0)
        self.Position = (x, y)
        width = config.ReadInt(CONFIG_WINDOW_WIDTH, 320)
        height = config.ReadInt(CONFIG_WINDOW_HEIGHT, 240)
        self.Size = (width, height)


    def fixSplitter(self):
        self.splitter.SetSashPosition(self.splitter.Size.width // 2)


    def on_quit(self, _event=None):
        config = wx.Config(wx.App.Get().AppName)
        config.WriteInt(CONFIG_WINDOW_X, self.Position.x)
        config.WriteInt(CONFIG_WINDOW_Y, self.Position.y)
        config.WriteInt(CONFIG_WINDOW_WIDTH, self.Size.Width)
        config.WriteInt(CONFIG_WINDOW_HEIGHT, self.Size.Height)
        if self.help_dialog:
            self.help_dialog.Destroy()
        self.Destroy()
