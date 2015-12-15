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

from gi.repository import Gtk

from silver.gui.common import create_menuitem
from silver.translations import _

class Menubar(Gtk.MenuBar):
    def __init__(self, app):
        Gtk.MenuBar.__init__(self)
        self._app = app
        self.accel_group = Gtk.AccelGroup()
        ## Music
        music_menu = Gtk.Menu()
        music = Gtk.MenuItem(_("Music"))
        music.set_submenu(music_menu)
        # Play
        self._menubar_play = create_menuitem(_("Play"), "media-playback-start")
        self._menubar_play.set_size_request(90, -1)
        self._menubar_play.connect("activate", self._on_play)
        key, mod = Gtk.accelerator_parse("F6")
        self._menubar_play.add_accelerator("activate", self.accel_group,
                                          key, mod, Gtk.AccelFlags.VISIBLE)
        # Stop
        self._menubar_stop = create_menuitem(_("Stop"), "media-playback-stop")
        self._menubar_stop.set_sensitive(False)
        self._menubar_stop.connect("activate", self._on_stop)
        key, mod = Gtk.accelerator_parse("F7")
        self._menubar_stop.add_accelerator("activate", self.accel_group,
                                          key, mod, Gtk.AccelFlags.VISIBLE)
        # Record
        self._menubar_record = create_menuitem(_("Record program"),
                                          "media-record")
        self._menubar_record.connect("activate", self._on_record)
        key, mod = Gtk.accelerator_parse("F8")
        self._menubar_record.add_accelerator("activate", self.accel_group,
                                          key, mod, Gtk.AccelFlags.VISIBLE)
        # Stop recording
        self._menubar_stop_recording = create_menuitem(_("Stop recording"),
                                          "media-playback-stop")
        self._menubar_stop_recording.set_sensitive(False)
        self._menubar_stop_recording.connect("activate", self._on_stop_record)
        key, mod = Gtk.accelerator_parse("F9")
        self._menubar_stop_recording.add_accelerator("activate", self.accel_group,
                                          key, mod, Gtk.AccelFlags.VISIBLE)
        # Mute
        self._menubar_mute = Gtk.CheckMenuItem(_("Mute"))
        self._menubar_mute.connect("toggled", self._on_mute)
        key, mod = Gtk.accelerator_parse("<Control>M")
        self._menubar_mute.add_accelerator("activate", self.accel_group,
                                          key, mod, Gtk.AccelFlags.VISIBLE)
        # Refresh
        refresh = create_menuitem(_("Update schedule"), "gtk-refresh")
        refresh.connect("activate", self._on_refresh)
        key, mod = Gtk.accelerator_parse("F5")
        refresh.add_accelerator("activate", self.accel_group,
                                          key, mod, Gtk.AccelFlags.VISIBLE)
        # Messenger
        msg = create_menuitem(_("Send message"), "gtk-edit")
        msg.connect("activate", self._on_im)
        key, mod = Gtk.accelerator_parse("<Control>S")
        msg.add_accelerator("activate", self.accel_group,
                                          key, mod, Gtk.AccelFlags.VISIBLE)
        # Preferences
        prefs = create_menuitem(_("Preferences"), "gtk-preferences")
        prefs.connect("activate", self._on_prefs)
        key, mod = Gtk.accelerator_parse("<Control>P")
        prefs.add_accelerator("activate", self.accel_group,
                                          key, mod, Gtk.AccelFlags.VISIBLE)
        # Quit
        quit = create_menuitem(_("Quit"), "gtk-quit")
        quit.connect("activate", self._on_quit)
        key, mod = Gtk.accelerator_parse("<Control>Q")
        quit.add_accelerator("activate", self.accel_group,
                                          key, mod, Gtk.AccelFlags.VISIBLE)
        # Separator
        sep = []
        for i in range(5):
            sep.append(Gtk.SeparatorMenuItem())
        # Pack
        for item in [ self._menubar_play,
                      self._menubar_stop,
                      self._menubar_record,
                      self._menubar_stop_recording,
                      sep[0],
                      self._menubar_mute,
                      sep[1],
                      refresh,
                      sep[2],
                      msg,
                      sep[3],
                      prefs,
                      sep[4],
                      quit ]:
            music_menu.append(item)
        ## Help
        help_menu = Gtk.Menu()
        help = Gtk.MenuItem(_("Help"))
        help.set_submenu(help_menu)
        # About
        about = create_menuitem("About", "gtk-about")
        about.set_size_request(90, -1)
        about.connect("activate", self._on_about)
        key, mod = Gtk.accelerator_parse("F1")
        about.add_accelerator("activate", self.accel_group, key,
                              mod, Gtk.AccelFlags.VISIBLE)
        help_menu.append(about)

        self.append(music)
        self.append(help)
        self.show_all()

    def update_playback_menu(self, playing):
        self._menubar_play.set_sensitive(not playing)
        self._menubar_stop.set_sensitive(playing)

    def update_recorder_menu(self, recording):
        self._menubar_record.set_sensitive(not recording)
        self._menubar_stop_recording.set_sensitive(recording)

    def _on_play(self, button):
        self._app.play()

    def _on_stop(self, button):
        self._app.stop()

    def _on_record(self, button):
        self._app.record()

    def _on_stop_record(self, button):
        self._app.stop_record()

    def _on_mute(self, button):
        self._app.mute()

    def _on_refresh(self, button):
        self._app.update_schedule(refresh=True)

    def _on_prefs(self, button):
        self._app.prefs()

    def _on_im(self, button):
        self._app.im()

    def _on_quit(self, button):
        self._app.quit()

    def _on_about(self, button):
        self._app.about()