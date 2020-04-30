#!/usr/bin/env python3
# Copyright © 2020 Qtrac Ltd. All rights reserved.

import wx

import Window


def main():
    app = wx.App()
    app.AppName = 'DebFind'
    app.AppVersion = '1.0.0'
    app.VendorName = 'Qtrac Ltd.'
    window = Window.Window(None)
    window.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()
