#!/usr/bin/env python3
"""
Copyright (C) 2015 Petr Skovoroda <petrskovoroda@gmail.com>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public
License along with this program; if not, write to the
Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
Boston, MA 02110-1301 USA
"""

from gi.repository import Gtk

from silver.translations import _

def create_menuitem(self, text, icon):
    """ Create menu item with icon """
    icontheme = Gtk.IconTheme.get_default()
    icon = icontheme.load_icon(icon, 16, 0)
    img = Gtk.Image()
    img.set_from_pixbuf(icon)
    menuitem = Gtk.ImageMenuItem()
    menuitem.set_image(img)
    menuitem.set_label(text)
    return menuitem

def create_toolbutton(self, icon):
    """ Toolbar button """
    button = Gtk.ToolButton()
    button.set_icon_name(icon)
    return button

def rgba_to_hex(rgba):
    """ Return #RRGGBB """
    r = int(rgba.red * 255)
    g = int(rgba.green * 255)
    b = int(rgba.blue * 255)
    return "#{0:02x}{1:02x}{2:02x}".format(r, g, b)

def get_playback_label(play=True):
    """ Return text and icon for playback menu/button """
    if play:
        text = _("Play")
        icon = "media-playback-start"
    else:
        text = _("Stop")
        icon = "media-playback-stop"
    return text, icon

def get_record_label(play=True):
    """ Return text and icon for record menu/button """
    if play:
        text = _("Record program")
        icon = "media-record"
    else:
        text = _("Stop recording")
        icon = "media-playback-stop"
    return text, icon

def get_volume_icon(muted=False):
    """ Return icon for mute button """
    if muted:
        icon = "audio-volume-muted"
    else:
        icon = "audio-volume-high"
    return icon