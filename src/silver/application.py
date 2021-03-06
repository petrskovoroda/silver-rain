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

from gi.repository import GObject, Gtk
import logging
import threading

import silver.config as config
from silver.gui.about import About
from silver.gui.controlpanel import ControlPanel
from silver.gui.dialog import show_dialog
from silver.gui.menubar import Menubar
from silver.gui.messenger import Messenger
from silver.gui.notifications import Notifications
from silver.gui.preferences import Preferences
from silver.gui.schedtree import SchedTree
from silver.gui.selection import Selection
from silver.gui.statusicon import StatusIcon
from silver.gui.window import MainWindow
from silver.player import SilverPlayer
from silver.player import SilverRecorder
from silver.schedule import SilverSchedule
from silver.timer import Timer

class SilverApp():
    """ Application """
    def __init__(self):
        # Initialize GStreamer
        self._player = SilverPlayer(self._on_player_error)
        self._recorder = SilverRecorder(self._on_recorder_error)
        # Schedule
        self._schedule = SilverSchedule()
        # On event timer
        self._t_event = Timer(self.update_now_playing)
        # Menubar
        self._menubar = Menubar(self)
        # Selection
        self._selection = Selection(self)
        # Controls
        self._panel = ControlPanel(self)
        # Main window
        self._window = MainWindow(self._menubar, self._selection, self._panel)
        # Don't show if should stay hidden
        if not config.start_hidden:
            self.show()
        # Messenger
        self._messenger = Messenger(self._window)
        # Notifications
        self._notifications = Notifications()
        # Satus icon
        self._status_icon = StatusIcon(self)
        # Update schedule
        self.update_schedule()
        # Autoplay
        if config.autoplay:
            self.play()

    def clean(self):
        self._t_event.cancel()
        self._player.clean()
        self._recorder.clean()

    def present(self):
        self._window.present()

# Application API
    def show(self):
        """ Show main window """
        self._window.show()
        self._window.hidden = False

    def hide(self):
        """ Hide main window """
        self._window.hide()
        self._window.hidden = True

    def toggle(self):
        """ Show/hide window """
        if self._window.hidden:
            self.show()
        else:
            self.hide()

    def about(self):
        """ Open about dialog """
        dialog = About(self._window)
        dialog.run()
        dialog.destroy()

    def im(self):
        """ Open messenger """
        self._messenger.show()

    def prefs(self):
        """ Open preferences window """
        dialog = Preferences(self._window)
        apply = []
        if dialog.run() == Gtk.ResponseType.APPLY:
            apply = dialog.apply_settings()
        dialog.destroy()
        # Apply settings
        if "IM" in apply:
            # Update messenger
            self._messenger.update_sender()
        if "APPEARANCE" in apply:
            # Update schedule
            self._dt = self._selection.update()
            self._sched_tree.update_model()
            self._sched_tree.mark_current()
            cover = self._schedule.get_event_cover()
            self._window.set_background(cover)
            # Update covers
            if config.background_image and not cover:
                self.update_schedule_covers()
        if "NETWORK" in apply:
            # Update player
            if self._player.playing:
                self.stop()
            self._player.reset_connection_settings()
            # Update recorder
            if self._recorder.playing:
                self.stop_record()
            self._recorder.reset_connection_settings()

    def play(self):
        """ Update interface, start player """
        # Update interface
        self._menubar.update_playback_menu(True)
        self._panel.update_playback_button(True)
        self._status_icon.update_playback_menu(True)
        # Play
        self._player.start()
        # Get current event
        title = self._schedule.get_event_title()
        host = self._schedule.get_event_host()
        img = self._schedule.get_event_icon()
        # Show notification
        self._notifications.show_playing(title, host, img)

    def stop(self):
        """ Update interface, stop player """
        # Update interface
        self._menubar.update_playback_menu(False)
        self._panel.update_playback_button(False)
        self._status_icon.update_playback_menu(False)
        # Stop player
        self._player.stop()
        # Show notification
        self._notifications.show_stopped()

    def set_volume(self, value):
        """ Set player volume """
        if value == 0:
            self.mute()
        elif self._player.muted:
            self.unmute(volume=value)
        else:
            self._player.set_volume(value)

    def volume_step(self, value):
        """ Increase player volume """
        volume = self._player.volume
        volume += value
        if volume > 100:
            volume = 100
        elif volume < 0:
            volume = 0
        self.set_volume(volume)
        if volume:
            self._panel.update_volume_scale(volume)

    def mute(self):
        """ Mute player, update interface """
        self._player.mute()
        # Update interface
        self._menubar.update_mute_menu(True)
        self._panel.update_mute_button(True)
        self._panel.update_volume_scale(0)
        self._status_icon.update_mute_menu(True)

    def unmute(self, volume=0):
        """ Unmute player, update interface """
        if not volume:
            self._player.unmute()
        else:
            self._player.set_volume(volume)
        # Update interface
        self._menubar.update_mute_menu(False)
        self._panel.update_mute_button(False)
        self._panel.update_volume_scale(self._player.volume)
        self._status_icon.update_mute_menu(False)

    def record(self):
        """ Update interface, start recorder """
        # Get name
        name = self._schedule.get_event_title()
        # Start recorder
        self._recorder.start(name)
        # Update interface
        self._menubar.update_recorder_menu(True)
        self._status_icon.update_recorder_menu(True)

    def stop_record(self):
        """ Update interface, stop recorder """
        # Stop recorder
        self._recorder.stop()
        # Update interface
        self._menubar.update_recorder_menu(False)
        self._status_icon.update_recorder_menu(False)

    def refilter(self, weekday):
        """ Refilter schedule """
        self._sched_tree.refilter(weekday)

    def update_schedule(self, refresh=False):
        """ Initialize schedule, create treeview and start timers
            This might take a while, so run in thread """
        def init_sched():
            # Initialize schedule
            if not self._schedule.update_schedule(refresh):
                GObject.idle_add(error)
            else:
                if not refresh:
                    # Initialize TreeView
                    self._sched_tree = SchedTree(self._schedule)
                    self._window.set_widget(self._sched_tree)
                else:
                    # Update TreeView
                    self._sched_tree.update_model()
                GObject.idle_add(cleanup)

        def cleanup():
            t.join()
            # Draw sched tree if just created
            if not refresh:
                self._sched_tree.show()
            # Update status icon tooltip
            title = self._schedule.get_event_title()
            host = self._schedule.get_event_host()
            time = self._schedule.get_event_time()
            img = self._schedule.get_event_icon()
            self._status_icon.update_event(title, host, time, img)
            # Reset status
            self._panel.status_set_playing()
            self._panel.status_set_text(title)
            # Start timer
            self._t_event.start(self._schedule.get_event_end())
            # Show agenda for today
            self._dt = self._selection.update()
            # Update treeview
            self._sched_tree.mark_current()
            # Set background
            if config.background_image:
                cover = self._schedule.get_event_cover()
                self._window.set_background(cover)
                # Update covers
                if not cover or refresh:
                    self.update_schedule_covers()

        def error():
            t.join()
            # Show error status
            self._panel.status_set_playing()
            self._panel.status_set_text(_("Couldn't update schedule"))
            def f():
                title = self._schedule.get_event_title()
                self._panel.status_set_text(title)
            GObject.timeout_add(10000, f)
            # Update status icon tooltip
            title = self._schedule.get_event_title()
            host = self._schedule.get_event_host()
            time = self._schedule.get_event_time()
            img = self._schedule.get_event_icon()
            self._status_icon.update_event(title, host, time, img)

        # Show updating status
        self._panel.status_set_updating()
        t = threading.Thread(target=init_sched)
        t.start()

    def update_schedule_covers(self):
        """ Update program covers """
        def update_covers():
            self._schedule.update_covers()
            GObject.idle_add(cleanup)

        def cleanup():
            t.join()
            # Set background
            self._window.set_background(self._schedule.get_event_cover())
            # Reset status
            self._panel.status_set_playing()
            title = self._schedule.get_event_title()
            self._panel.status_set_text(title)

        self._panel.status_set_downloading_covers()
        t = threading.Thread(target=update_covers)
        t.start()

    def update_now_playing(self):
        """ Update label, mark current event, show notifications """
        # Stop recorder
        if self._recorder.playing:
            self.stop_record()
        # Update event
        self._schedule.update_event()
        # Check if should be recorded
        if self._schedule.get_record_status():
            self.record()
        # Check if should start player
        if self._schedule.get_play_status():
            self.play()
        # Display current agenda
        self._dt = self._selection.update(dt=self._dt)
        # Reset TreeView line
        self._sched_tree.reset_marked()
        # Update treeview
        self._dt = self._selection.update()
        self._sched_tree.mark_current()
        # Update background
        self._window.set_background(self._schedule.get_event_cover())
        # Update statusicon tooltip
        title = self._schedule.get_event_title()
        host = self._schedule.get_event_host()
        time = self._schedule.get_event_time()
        img = self._schedule.get_event_icon()
        self._status_icon.update_event(title, host, time, img)
        # Update status
        self._panel.status_set_text(title)
        # Show notification
        self._notifications.show_playing(title, host, img)
        # Start timer
        self._t_event.start(self._schedule.get_event_end())

    def quit(self):
        """ Exit """
        Gtk.main_quit()

    def _on_player_error(self, type, msg):
        """ Player error callback """
        self._gstreamer_error_show(type, msg)
        self.stop()

    def _on_recorder_error(self, type, msg):
        """ Recorder error callback """
        self._gstreamer_error_show(type, msg)
        self.stop_record()

    def _gstreamer_error_show(self, type, msg):
        """ Show error dialog """
        if type == "warning":
            logging.warning(msg)
            show_dialog(self._window, "GStreamer warning",
                        "dialog-warning", msg)
        elif type == "error":
            logging.error(msg)
            show_dialog(self._window, "GStreamer error",
                        "dialog-error", msg)
