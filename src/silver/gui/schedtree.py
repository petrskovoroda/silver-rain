#!/usr/bin/env python3
"""
Copyright (C) 2015 Petr Skovoroda <petrskovoroda@gmail.com>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public
License along with this program; if not, write to the
Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
Boston, MA 02110-1301 USA
"""

from gi.repository import Gtk, GdkPixbuf, Gdk
from datetime import datetime
import subprocess

import silver.config as config
from silver.gui.common import create_menuitem
from silver.gui.common import hex_to_rgba
from silver.msktz import MSK
from silver.schedule import SCHED_WEEKDAY_LIST

class SchedTree(Gtk.TreeView):
    """ Schedule TreeView """
    def __init__(self, sched):
        Gtk.TreeView.__init__(self)
        self.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)
        self.connect("button-release-event", self._on_button_release_event)
        self._weekday_filter = datetime.now(MSK()).strftime("%A")
        self._marked = False
        self._marked_pos = 0
        self._sched = sched
        # Init model
        self._init_model()
        # Icon
        renderer = Gtk.CellRendererPixbuf()
        column = Gtk.TreeViewColumn("", renderer, pixbuf=6,
                                    cell_background_rgba=7)
        column.set_fixed_width(100)
        renderer.set_alignment(1, 0.5)
        self.append_column(column)

        renderer = Gtk.CellRendererText()
        renderer.set_padding(10, 0)
        renderer.set_alignment(0.5, 0.5)
        renderer.set_property('height', 50)
        # Time
        column = Gtk.TreeViewColumn(_("Time"), renderer, text=2,
                                    background_rgba=7, foreground=8, font=9)
        column.set_alignment(0.5)
        column.set_min_width(10)
        self.append_column(column)
        # Title
        renderer.set_alignment(0, 0.5)
        renderer.set_property("wrap_mode", Gtk.WrapMode.WORD)
        renderer.set_property("wrap_width", 200)
        column = Gtk.TreeViewColumn(_("Title"), renderer, text=3,
                                    background_rgba=7, foreground=8, font=9)
        column.set_alignment(0.5)
        column.set_min_width(50)
        column.set_resizable(True)
        self.append_column(column)
        # Host
        column = Gtk.TreeViewColumn(_("Host"), renderer, text=5,
                                    background_rgba=7, foreground=8, font=9)
        column.set_alignment(0.5)
        column.set_min_width(50)
        column.set_resizable(True)
        self.append_column(column)

    def refilter(self, wd):
        """ Refilter model """
        self._weekday_filter = SCHED_WEEKDAY_LIST[wd]
        self._model.refilter()

    def reset_marked(self):
        """ Reset marked row """
        if not self._marked:
            # Nothing to reset
            return
        # Get current position
        path = Gtk.TreePath(self._marked_pos)
        iter = self._model.get_iter(path)
        # Set original colors and font
        dark = self._model[iter][10]
        bg_color = hex_to_rgba(config.bg_colors[dark])
        bg_color.alpha = config.bg_alpha[dark]
        self._model[iter][7] = bg_color
        self._model[iter][8] = config.font_color
        self._model[iter][9] = config.font
        self._marked = False

    def mark_current(self):
        """ Mark current event """
        # Get current position
        pos = self._sched.get_event_position()
        path = Gtk.TreePath(pos)
        iter = self._model.get_iter(path)
        # Set current row color
        marked_color = hex_to_rgba(config.selected_bg_color)
        marked_color.alpha = config.selected_alpha
        self._model[iter][7] = marked_color
        self._model[iter][8] = config.selected_font_color
        self._model[iter][9] = config.selected_font
        # Scroll to current cell
        self.scroll_to_cell(path, use_align=True, row_align=0.5)
        # Backup position
        self._marked = True
        self._marked_pos = pos

    def update_model(self):
        """ Create new model """
        self._init_model()

    def _init_model(self):
        """ Initialize TreeView model filled with schedule events """
        store = Gtk.TreeStore(str,              #  0 Weekday
                              bool,             #  1 IsParent
                              str,              #  2 Time
                              str,              #  3 Title
                              str,              #  4 URL
                              str,              #  5 Host
                              GdkPixbuf.Pixbuf, #  6 Icon
                              Gdk.RGBA,         #  7 BackgroundColor
                              str,              #  8 FontColor
                              str,              #  9 Font
                              bool,             # 10 IsDark
                              bool,             # 11 Recorder set
                              bool,             # 12 Playback set
                              bool)             # 13 IsMerged
        self._model = store.filter_new()
        self._model.set_visible_func(self._model_func)
        self._sched.fill_tree_store(store)
        self._marked = False
        self.set_model(self._model)

    def _model_func(self, model, iter, data):
        """ Filter by weekday """
        prev_day = SCHED_WEEKDAY_LIST.index(self._weekday_filter)
        prev_day = SCHED_WEEKDAY_LIST[prev_day - 1]
        return (model[iter][0] == self._weekday_filter) or \
                (model[iter][13] and model[iter][0] == prev_day)

    def _on_button_release_event(self, widget, event):
        """ Open menu on right click """
        if not event.button == 3:
            return
        selection = self.get_selection()
        model, iter = selection.get_selected()
        self._popup = Gtk.Menu()
        # Program url
        url = create_menuitem(_("Program page"), "web-browser")
        url.set_size_request(100, -1)
        event_url = model.get_value(iter, 4)
        url.connect("activate", self._on_url, event_url)
        self._popup.append(url)
        if model.get_value(iter, 1):
            # Play program
            if not model.get_value(iter, 12):
                play = create_menuitem(_("Play program"),
                                       "media-playback-start")
            else:
                play = create_menuitem(_("Don't play"), "gtk-cancel")
            play.connect("activate", self._on_play, model, iter)
            self._popup.append(play)
            # Record program
            if not model.get_value(iter, 11):
                rec = create_menuitem(_("Record program"), "media-record")
            else:
                rec = create_menuitem(_("Don't record"), "gtk-cancel")
            rec.connect("activate", self._on_record, model, iter)
            self._popup.append(rec)
        self._popup.show_all()
        self._popup.popup(None, None, None, None, event.button, event.time)

    def _on_record(self, button, model, iter):
        rec = not model.get_value(iter, 11)
        wd = SCHED_WEEKDAY_LIST.index(model.get_value(iter, 0))
        time = model.get_value(iter, 2)
        self._sched.set_record_status(rec, wd, time)
        model.set_value(iter, 11, rec)

    def _on_play(self, button, model, iter):
        play = not model.get_value(iter, 12)
        wd = SCHED_WEEKDAY_LIST.index(model.get_value(iter, 0))
        time = model.get_value(iter, 2)
        self._sched.set_play_status(play, wd, time)
        model.set_value(iter, 12, play)

    def _on_url(self, button, url):
        subprocess.Popen(["xdg-open", url], stdout=subprocess.PIPE)
