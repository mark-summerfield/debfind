#!/usr/bin/env python3
# Copyright © 2020 Qtrac Ltd. All rights reserved.

import wx

import Icons


CONFIG_WINDOW_HEIGHT = 'Window/Height'
CONFIG_WINDOW_WIDTH = 'Window/Width'
CONFIG_WINDOW_X = 'Window/X'
CONFIG_WINDOW_Y = 'Window/Y'


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
        self.make_widgets()
        self.make_status_bar()
        self.make_layout()
        self.make_bindings()
        self.set_position_and_size()
        # TODO load config (win size/pos)


    def add_icons(self):
        icons = wx.IconBundle()
        icons.AddIcon(Icons.icon16.Icon)
        icons.AddIcon(Icons.icon32.Icon)
        icons.AddIcon(Icons.icon48.Icon)
        icons.AddIcon(Icons.icon256.Icon)
        self.SetIcons(icons)


    def make_widgets(self):
        self.panel = wx.Panel(self)
        self.desc_label = wx.StaticText(self, label='Name and D&escription')
        self.desc_edit = wx.TextCtrl(self)
        self.desc_all_radio = wx.RadioButton(self, name='All &Words',
                                             style=wx.RB_GROUP)
        self.desc_any_radio = wx.RadioButton(self, name='Any W&ords')
        self.name_label = wx.StaticText(self, label='&Name Only')
        self.name_edit = wx.TextCtrl(self)
        self.name_all_radio = wx.RadioButton(self, name='All Wor&ds',
                                             style=wx.RB_GROUP)
        self.name_any_radio = wx.RadioButton(self, name='Any Word&s')
        self.section_label = wx.StaticText(self, label='Se&ction')
        # TODO


    def make_status_bar(self):
        pass # TODO


    def make_layout(self):
        pass # TODO


    def make_bindings(self):
        pass # TODO


    def set_position_and_size(self):
        config = wx.Config(wx.App.Get().AppName)
        x = config.ReadInt(CONFIG_WINDOW_X, 0)
        y = config.ReadInt(CONFIG_WINDOW_Y, 0)
        self.Position = (x, y)
        width = config.ReadInt(CONFIG_WINDOW_WIDTH, 320)
        height = config.ReadInt(CONFIG_WINDOW_HEIGHT, 240)
        self.Size = (width, height)

    # TODO save size/pos
