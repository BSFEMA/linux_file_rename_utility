"""
Application:  Linux File Rename Utility
Author:  BSFEMA
Note:  I would appreciate it if you kept my attribution as the original author in any fork or remix that is made.
Purpose:  To provide Linux with a good file rename utility.
          I didn't particularly like any of the existing rename utilities available on Linux and I didn't like having to run a Windows one in Wine either...
          This was also a good excuse to learn Gtk and Glade programming with Python.
Command Line Parameters:  There is just 1:
                          It is the folder path that will be used to start renaming files from.
                          If this value isn't provided, then the starting path will be where this application file is located.
                          The intention is that you can call this application from a context menu from a file browser (e.g. Nemo) and it would automatically load up that folder.
                          If you pass it a path to a file, it will use the folder that the file resides in instead.
"""


import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
import sys
import os
import re
import datetime
from operator import itemgetter


default_folder_path = ""  # The path for the filechooser and data grid to work against.  This is the base folder to work against.
application_Settings = []  # Holds user's custom widget defaults specified in ~/.config/BSFEMA/settings.txt
files_Full = []  # Holds all of the file information
files = []  # Holds only the file information for displaying in the data grid
directory_counts = dict()  # Holds the all of the sub-directories used and the counts (for the 'Per Folder' option).
rename_pairs = []  # Holds the current name, new name, status, full path, type
rename_pairs_from_file = {}  # Holds an imported dictionary of:  <original file name>/<new file name>
settings_file_to_load = ""   # The path to the default settings file.
rename_pairs_file_to_load = ""  # The path to the rename pair file to import.
konami_code = []  # Easter Egg to see if the Konami code has been entered in the About dialog.
previous_selection = [[], 0, "", True]  # [ [list of selected rows], len(model), "default_folder_path", [Boolean = should it treeview_Data_Grid_selection_changed] ]


class Main():
    def __init__(self):
        # Setup Glade Gtk
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join(sys.path[0], "linux_file_rename_utility.glade"))  # Looking where the python script is located
        self.builder.connect_signals(self)
        # Get UI components
        window = self.builder.get_object("main_window")
        window.connect("delete-event", gtk.main_quit)
        window.set_title('Linux File Rename Utility')
        window.set_default_icon_from_file(os.path.join(sys.path[0], "linux_file_rename_utility.svg"))  # Setting the "default" icon makes it usable in the about dialog. (This will take .ico, .png, and .svg images.)
        window.show()
        # Initialize "Box (1-8)" booleans to False, this is to tell if they are modified later. This needs to happen here before any of the Box options are called/modified
        self.box_1 = False
        self.box_2 = False
        self.box_3 = False
        self.box_4 = False
        self.box_5 = False
        self.box_6 = False
        self.box_7 = False
        self.box_8 = False
        self.rename_pairs_file = False
        # This allows the use css styling
        provider = gtk.CssProvider()
        provider.load_from_path(os.path.join(sys.path[0], "linux_file_rename_utility.css"))  # Looking where the python script is located
        gtk.StyleContext().add_provider_for_screen(gdk.Screen.get_default(), provider, gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        # Set filechooser_Folder_Selecter and entry_Folder_path values to the default_folder_path
        filechooser_Folder_Selecter = self.builder.get_object("filechooser_Folder_Selecter")
        filechooser_Folder_Selecter.set_current_folder(default_folder_path)
        entry_Folder_path = self.builder.get_object("entry_Folder_path")
        entry_Folder_path.set_text(default_folder_path)
        # Set spinner direction default to "HORIZONTAL"
        self.set_spinner_orientation("HORIZONTAL")  # "HORIZONTAL" is the default (for smaller screens)
        # Set verious objects to their defaults:
        # Set combo_Extension to default value (1st entry)
        combo_Extension = self.builder.get_object("combo_Extension")
        combo_Extension.set_entry_text_column(0)
        combo_Extension.set_active(0)
        # Set combo_Numbering to default value (1st entry)
        combo_Numbering = self.builder.get_object("combo_Numbering")
        combo_Numbering.set_entry_text_column(0)
        combo_Numbering.set_active(0)
        # Set combo_Append_Folder_Name to default value (1st entry)
        combo_Append_Folder_Name = self.builder.get_object("combo_Append_Folder_Name")
        combo_Append_Folder_Name.set_entry_text_column(0)
        combo_Append_Folder_Name.set_active(0)
        # Set combo_Remove_Crop to default value (1st entry)
        combo_Remove_Crop = self.builder.get_object("combo_Remove_Crop")
        combo_Remove_Crop.set_entry_text_column(0)
        combo_Remove_Crop.set_active(0)
        # Set combo_Case to default value (1st entry)
        combo_Case = self.builder.get_object("combo_Case")
        combo_Case.set_entry_text_column(0)
        combo_Case.set_active(0)
        # Set combo_Name to default value (1st entry)
        combo_Name = self.builder.get_object("combo_Name")
        combo_Name.set_entry_text_column(0)
        combo_Name.set_active(0)
        # Set the checkboxes in the box_Files section
        checkbox_Folders = self.builder.get_object("checkbox_Folders")
        checkbox_Folders.set_active(True)
        checkbox_Subfolders = self.builder.get_object("checkbox_Subfolders")
        checkbox_Files = self.builder.get_object("checkbox_Files")
        checkbox_Files.set_active(True)
        checkbox_Hidden = self.builder.get_object("checkbox_Hidden")
        # Setup the data grid
        treeview_Data_Grid = self.builder.get_object("treeview_Data_Grid")
        treeview_Data_Grid.get_selection().set_mode(gtk.SelectionMode.MULTIPLE)  # Now it can multiselect rows
        treeview_Data_Grid.get_selection().connect("changed", self.treeview_Data_Grid_selection_changed)
        self.clear_Data_Grid()
        populate_files_Full(self.builder.get_object("entry_Mask").get_text(),
                            self.builder.get_object("checkbox_Folders").get_active(),
                            self.builder.get_object("checkbox_Subfolders").get_active(),
                            self.builder.get_object("checkbox_Files").get_active(),
                            self.builder.get_object("checkbox_Hidden").get_active(),
                            self.builder.get_object("spin_File_Name_Min").get_value_as_int(),
                            self.builder.get_object("spin_File_Name_Max").get_value_as_int(),
                            )
        self.load_Data_Grid()
        self.resize_column_widths()
        # Set the default data grid height (400)
        self.set_scrollwindow_Data_Grid_height(400)  # "400" is the default value
        # Setup the Status Labels
        box_Status = self.builder.get_object("box_Status")
        box_Status.get_style_context().add_class('grey-border')
        label_Status_Rows = self.builder.get_object("label_Status_Rows")
        label_Status_Rows.set_text("")
        label_Status_Rows.get_style_context().add_class('grey-border')
        label_Status_Selected = self.builder.get_object("label_Status_Selected")
        label_Status_Selected.set_text("")
        label_Status_Selected.get_style_context().add_class('grey-border')
        label_Status_Renamed = self.builder.get_object("label_Status_Renamed")
        label_Status_Renamed.set_text("")
        label_Status_Renamed.get_style_context().add_class('grey-border')
        label_Status_Failed = self.builder.get_object("label_Status_Failed")
        label_Status_Failed.set_text("")
        label_Status_Failed.get_style_context().add_class('grey-border')
        self.update_status_labels()
        # Apply custom user application settings
        self.apply_application_settings()
        global previous_selection
        selection = treeview_Data_Grid.get_selection()
        model, items = selection.get_selected_rows()
        previous_selection = [[], len(model), default_folder_path, True]  # Set the row count and path, This saves a full loop in treeview_Data_Grid_selection_changed later

    """ ************************************************************************************************************ """
    #  These are the various widget's signal handler functions:  UI elements other than buttons & dialogs
    """ ************************************************************************************************************ """

    def box_9_files_section_changed(self, widget):  # Clear and rebuild data grid
        self.clear_Data_Grid()
        populate_files_Full(self.builder.get_object("entry_Mask").get_text(),
                            self.builder.get_object("checkbox_Folders").get_active(),
                            self.builder.get_object("checkbox_Subfolders").get_active(),
                            self.builder.get_object("checkbox_Files").get_active(),
                            self.builder.get_object("checkbox_Hidden").get_active(),
                            self.builder.get_object("spin_File_Name_Min").get_value_as_int(),
                            self.builder.get_object("spin_File_Name_Max").get_value_as_int(),
                            )
        self.load_Data_Grid()
        self.resize_column_widths()
        self.update_status_labels()

    def entry_Extension_changed(self, widget):
        self.check_settings_for_box_8()
        self.treeview_Data_Grid_selection_changed("Nothing")  # The function takes a "treeselection_object" parameter, but it doesn't use it, so I'm passing it "Nothing"...

    def combo_Extension_changed(self, widget):
        entry_Extension = self.builder.get_object("entry_Extension")
        if widget.get_text() in ('Fixed', 'Extra'):
            entry_Extension.set_editable(True)
        else:
            entry_Extension.set_text("")
            entry_Extension.set_editable(False)
        self.check_settings_for_box_8()
        self.treeview_Data_Grid_selection_changed("Nothing")  # The function takes a "treeselection_object" parameter, but it doesn't use it, so I'm passing it "Nothing"...

    def widgets_Numbering_changed(self, widget):  # This is for all "Numbering" widgets except "combo_Numbering"
        self.check_settings_for_box_7()
        self.treeview_Data_Grid_selection_changed("Nothing")  # The function takes a "treeselection_object" parameter, but it doesn't use it, so I'm passing it "Nothing"...

    def entry_Remove_Crop_changed(self, widget):
        self.check_settings_for_box_4()
        self.treeview_Data_Grid_selection_changed("Nothing")  # The function takes a "treeselection_object" parameter, but it doesn't use it, so I'm passing it "Nothing"...

    def combo_Remove_Crop_changed(self, widget):
        entry_Remove_Crop = self.builder.get_object("entry_Remove_Crop")
        if widget.get_text() in ('Before First', 'Before Last', 'After First', 'After Last'):
            entry_Remove_Crop.set_editable(True)
        else:
            entry_Remove_Crop.set_text("")
            entry_Remove_Crop.set_editable(False)
        self.check_settings_for_box_4()
        self.treeview_Data_Grid_selection_changed("Nothing")  # The function takes a "treeselection_object" parameter, but it doesn't use it, so I'm passing it "Nothing"...

    def combo_Numbering_changed(self, widget):
        spin_Numbering_At = self.builder.get_object("spin_Numbering_At")
        if widget.get_text() == 'Insert':
            spin_Numbering_At.set_editable(True)
            spin_Numbering_At.set_value(0)
        else:
            spin_Numbering_At.set_editable(False)
            spin_Numbering_At.set_value(0)
        self.check_settings_for_box_7()
        self.treeview_Data_Grid_selection_changed("Nothing")  # The function takes a "treeselection_object" parameter, but it doesn't use it, so I'm passing it "Nothing"...

    def combo_Append_Folder_Name_changed(self, widget):
        entry_Append_Folder_Name_Separator = self.builder.get_object("entry_Append_Folder_Name_Separator")
        if widget.get_text() == 'None':
            entry_Append_Folder_Name_Separator.set_text('')
            entry_Append_Folder_Name_Separator.set_editable(False)
        else:
            entry_Append_Folder_Name_Separator.set_editable(True)
        self.check_settings_for_box_6()
        self.treeview_Data_Grid_selection_changed("Nothing")  # The function takes a "treeselection_object" parameter, but it doesn't use it, so I'm passing it "Nothing"...

    def entry_Append_Folder_Name_Separator_changed(self, widget):
        self.check_settings_for_box_6()
        self.treeview_Data_Grid_selection_changed("Nothing")  # The function takes a "treeselection_object" parameter, but it doesn't use it, so I'm passing it "Nothing"...

    def entry_Add_changed(self, widget):  # This is for all "entry_Add" and "spin_Add" widgets
        self.check_settings_for_box_5()
        self.treeview_Data_Grid_selection_changed("Nothing")  # The function takes a "treeselection_object" parameter, but it doesn't use it, so I'm passing it "Nothing"...

    def spin_Remove_changed(self, widget):  # This is for all "spin_Remove" widgets
        spin_Remove_From = self.builder.get_object("spin_Remove_From")
        spin_Remove_To = self.builder.get_object("spin_Remove_To")
        if spin_Remove_From.get_value() > spin_Remove_To.get_value():  # Make sure that To is >= From
            spin_Remove_To.set_value(spin_Remove_From.get_value())
        self.check_settings_for_box_4()
        self.treeview_Data_Grid_selection_changed("Nothing")  # The function takes a "treeselection_object" parameter, but it doesn't use it, so I'm passing it "Nothing"...

    def combo_Case_changed(self, widget):
        self.check_settings_for_box_3()
        self.treeview_Data_Grid_selection_changed("Nothing")  # The function takes a "treeselection_object" parameter, but it doesn't use it, so I'm passing it "Nothing"...

    def combo_Name_changed(self, widget):
        entry_Name_Fixed = self.builder.get_object("entry_Name_Fixed")
        if widget.get_text() == 'Fixed':
            entry_Name_Fixed.set_editable(True)
        else:
            entry_Name_Fixed.set_text('')
            entry_Name_Fixed.set_editable(False)
        self.check_settings_for_box_1()
        self.treeview_Data_Grid_selection_changed("Nothing")  # The function takes a "treeselection_object" parameter, but it doesn't use it, so I'm passing it "Nothing"...

    def entry_Name_Fixed_changed(self, widget):
        self.check_settings_for_box_1()
        self.treeview_Data_Grid_selection_changed("Nothing")  # The function takes a "treeselection_object" parameter, but it doesn't use it, so I'm passing it "Nothing"...

    def entry_Replace_Search_changed(self, widget):  # This is for all "entry_Replace" widgets
        self.check_settings_for_box_2()
        self.treeview_Data_Grid_selection_changed("Nothing")  # The function takes a "treeselection_object" parameter, but it doesn't use it, so I'm passing it "Nothing"...

    def filechooser_Folder_Selecter_fileset(self, widget):
        entry_Folder_path = self.builder.get_object("entry_Folder_path")
        entry_Folder_path.set_text(widget.get_filename())

    def entry_Folder_Path_changed(self, widget):
        current_path = widget.get_text()
        if os.path.isdir(current_path):
            widget.get_style_context().remove_class('red-foreground')
            # widget.get_style_context().add_class('black-foreground')
            # Reload the data grid now that a new (real) folder is selected
            global default_folder_path
            if current_path[-1:] == "/":  # remove the final "/" from a path
                current_path = current_path[:-1]
            default_folder_path = current_path  # Now that the edited text is a folder, set the default_folder_path to use that
            self.clear_Data_Grid()
            populate_files_Full(self.builder.get_object("entry_Mask").get_text(),
                                self.builder.get_object("checkbox_Folders").get_active(),
                                self.builder.get_object("checkbox_Subfolders").get_active(),
                                self.builder.get_object("checkbox_Files").get_active(),
                                self.builder.get_object("checkbox_Hidden").get_active(),
                                self.builder.get_object("spin_File_Name_Min").get_value_as_int(),
                                self.builder.get_object("spin_File_Name_Max").get_value_as_int(),
                                )
            self.load_Data_Grid()
            self.resize_column_widths()
        else:
            # widget.get_style_context().remove_class('black-foreground')
            widget.get_style_context().add_class('red-foreground')

    def checkbox_Save_History_toggled(self, widget):
        # This doesn't really have any 'action' at the moment, as it's just a setting to be toggled
        pass

    def treeview_Data_Grid_select_all(self, event):
        treeview_Data_Grid = self.builder.get_object("treeview_Data_Grid")
        treeselection = treeview_Data_Grid.get_selection()
        treeselection.select_all()


    def treeview_Data_Grid_select_none(self, event):
        treeview_Data_Grid = self.builder.get_object("treeview_Data_Grid")
        treeselection = treeview_Data_Grid.get_selection()
        treeselection.unselect_all()

    def treeview_Data_Grid_select_inverse(self, event):
        treeview_Data_Grid = self.builder.get_object("treeview_Data_Grid")
        treeselection = treeview_Data_Grid.get_selection()
        model, items = treeselection.get_selected_rows()
        temp_indexes = []  # Holds the rows indexes of the currently selected rows
        temp_treepaths = []  # Holds the TreePath objects of the currently selected rows
        if len(model) > 0:
            for item in items:  # Build list of the currently selected rows
                temp_indexes.append(int(str(item)))
                temp_treepaths.append(item)
            for x in range(len(temp_treepaths)):  # Unselect the currently selected rows
                treeselection.unselect_path(temp_treepaths[x])
            for x in range(len(model)):  # Select the currently unselected rows
                if x not in temp_indexes:
                    treeselection.select_path(x)

    def treeview_Data_Grid_toggle_full_path(self, event):
        treeviewcolumn_Full_Path = self.builder.get_object("treeviewcolumn_Full_Path")
        if treeviewcolumn_Full_Path.get_visible():
            treeviewcolumn_Full_Path.set_visible(False)
        else:
            treeviewcolumn_Full_Path.set_visible(True)

    def treeview_Data_Grid_toggle_local_path(self, event):
        treeviewcolumn_Local_Path = self.builder.get_object("treeviewcolumn_Local_Path")
        if treeviewcolumn_Local_Path.get_visible():
            treeviewcolumn_Local_Path.set_visible(False)
        else:
            treeviewcolumn_Local_Path.set_visible(True)

    def treeview_Data_Grid_toggle_file_type(self, event):
        treeviewcolumn_Type = self.builder.get_object("treeviewcolumn_Type")
        if treeviewcolumn_Type.get_visible():
            treeviewcolumn_Type.set_visible(False)
        else:
            treeviewcolumn_Type.set_visible(True)

    def treeview_Data_Grid_toggle_hidden(self, event):
        treeviewcolumn_Hidden = self.builder.get_object("treeviewcolumn_Hidden")
        if treeviewcolumn_Hidden.get_visible():
            treeviewcolumn_Hidden.set_visible(False)
        else:
            treeviewcolumn_Hidden.set_visible(True)

    def treeview_Data_Grid_toggle_size(self, event):
        treeviewcolumn_Size = self.builder.get_object("treeviewcolumn_Size")
        if treeviewcolumn_Size.get_visible():
            treeviewcolumn_Size.set_visible(False)
        else:
            treeviewcolumn_Size.set_visible(True)

    def treeview_Data_Grid_toggle_date_modified(self, event):
        treeviewcolumn_Date_Modified = self.builder.get_object("treeviewcolumn_Date_Modified")
        if treeviewcolumn_Date_Modified.get_visible():
            treeviewcolumn_Date_Modified.set_visible(False)
        else:
            treeviewcolumn_Date_Modified.set_visible(True)

    def treeview_Data_Grid_button_press_event(self, widget, event):
        # event.button == 1  # Is mouse left click
        # event.button == 2  # Is mouse scrollwheel click
        # event.button == 3  # Is mouse right click
        if event.button == 3:  # right click
            # print(str(int(event.x)) + " x " + str(int(event.x)))  # Where clicked
            # model, path = treeview.get_path_at_pos(int(event.x), int(event.y))
            menu = gtk.Menu()
            # Select All
            select_all = gtk.MenuItem(label="Select All")
            select_all.connect("activate", self.treeview_Data_Grid_select_all)
            select_all.show()
            menu.append(select_all)
            # Select None
            select_none = gtk.MenuItem(label="Select None")
            select_none.connect("activate", self.treeview_Data_Grid_select_none)
            select_none.show()
            menu.append(select_none)
            # Select Inverse
            select_inverse = gtk.MenuItem(label="Select Inverse")
            select_inverse.connect("activate", self.treeview_Data_Grid_select_inverse)
            select_inverse.show()
            menu.append(select_inverse)
            # Separator_1
            separator_1 = gtk.SeparatorMenuItem()
            separator_1.show()
            menu.append(separator_1)
            # Data Grid - treeviewcolumn_Size
            file_size = gtk.MenuItem(label="Toggle \'Size\' column")
            file_size.connect("activate", self.treeview_Data_Grid_toggle_size)
            file_size.show()
            menu.append(file_size)
            # Data Grid - treeviewcolumn_Date_Modified
            date_modified = gtk.MenuItem(label="Toggle \'Date Modified\' column")
            date_modified.connect("activate", self.treeview_Data_Grid_toggle_date_modified)
            date_modified.show()
            menu.append(date_modified)
            # Separator_2
            separator_2 = gtk.SeparatorMenuItem()
            separator_2.show()
            menu.append(separator_2)
            # Data Grid - treeviewcolumn_Full_Path
            full_path = gtk.MenuItem(label="Toggle \'Full Path\' column")
            full_path.connect("activate", self.treeview_Data_Grid_toggle_full_path)
            full_path.show()
            menu.append(full_path)
            # Data Grid - treeviewcolumn_Local_Path
            local_path = gtk.MenuItem(label="Toggle \'Local Path\' column")
            local_path.connect("activate", self.treeview_Data_Grid_toggle_local_path)
            local_path.show()
            menu.append(local_path)
            # Data Grid - treeviewcolumn_Type
            file_type = gtk.MenuItem(label="Toggle \'Type\' column")
            file_type.connect("activate", self.treeview_Data_Grid_toggle_file_type)
            file_type.show()
            menu.append(file_type)
            # Data Grid - treeviewcolumn_Hidden
            file_hidden = gtk.MenuItem(label="Toggle \'Hidden\' column")
            file_hidden.connect("activate", self.treeview_Data_Grid_toggle_hidden)
            file_hidden.show()
            menu.append(file_hidden)
            menu.popup(None, None, None, None, event.button, event.time)

    def set_spinner_orientation(self, direction):  # set the direction of all spinner widgets to Horizontal or Tertical
        spin_Remove_First = self.builder.get_object("spin_Remove_First")
        spin_Remove_Last = self.builder.get_object("spin_Remove_Last")
        spin_Remove_From = self.builder.get_object("spin_Remove_From")
        spin_Remove_To = self.builder.get_object("spin_Remove_To")
        spin_Add_Insert = self.builder.get_object("spin_Add_Insert")
        spin_Numbering_At = self.builder.get_object("spin_Numbering_At")
        spin_Numbering_Start = self.builder.get_object("spin_Numbering_Start")
        spin_Numbering_Increment = self.builder.get_object("spin_Numbering_Increment")
        spin_Numbering_Padding = self.builder.get_object("spin_Numbering_Padding")
        spin_File_Name_Min = self.builder.get_object("spin_File_Name_Min")
        spin_File_Name_Max = self.builder.get_object("spin_File_Name_Max")
        if direction.upper() == "HORIZONTAL":
            spin_Remove_First.set_orientation(gtk.Orientation.HORIZONTAL)
            spin_Remove_Last.set_orientation(gtk.Orientation.HORIZONTAL)
            spin_Remove_From.set_orientation(gtk.Orientation.HORIZONTAL)
            spin_Remove_To.set_orientation(gtk.Orientation.HORIZONTAL)
            spin_Add_Insert.set_orientation(gtk.Orientation.HORIZONTAL)
            spin_Numbering_At.set_orientation(gtk.Orientation.HORIZONTAL)
            spin_Numbering_Start.set_orientation(gtk.Orientation.HORIZONTAL)
            spin_Numbering_Increment.set_orientation(gtk.Orientation.HORIZONTAL)
            spin_Numbering_Padding.set_orientation(gtk.Orientation.HORIZONTAL)
            spin_File_Name_Min.set_orientation(gtk.Orientation.HORIZONTAL)
            spin_File_Name_Max.set_orientation(gtk.Orientation.HORIZONTAL)
        elif direction.upper() == "VERTICAL":
            spin_Remove_First.set_orientation(gtk.Orientation.VERTICAL)
            spin_Remove_Last.set_orientation(gtk.Orientation.VERTICAL)
            spin_Remove_From.set_orientation(gtk.Orientation.VERTICAL)
            spin_Remove_To.set_orientation(gtk.Orientation.VERTICAL)
            spin_Add_Insert.set_orientation(gtk.Orientation.VERTICAL)
            spin_Numbering_At.set_orientation(gtk.Orientation.VERTICAL)
            spin_Numbering_Start.set_orientation(gtk.Orientation.VERTICAL)
            spin_Numbering_Increment.set_orientation(gtk.Orientation.VERTICAL)
            spin_Numbering_Padding.set_orientation(gtk.Orientation.VERTICAL)
            spin_File_Name_Min.set_orientation(gtk.Orientation.VERTICAL)
            spin_File_Name_Max.set_orientation(gtk.Orientation.VERTICAL)
        else:  # "HORIZONTAL" is the default
            spin_Remove_First.set_orientation(gtk.Orientation.HORIZONTAL)
            spin_Remove_Last.set_orientation(gtk.Orientation.HORIZONTAL)
            spin_Remove_From.set_orientation(gtk.Orientation.HORIZONTAL)
            spin_Remove_To.set_orientation(gtk.Orientation.HORIZONTAL)
            spin_Add_Insert.set_orientation(gtk.Orientation.HORIZONTAL)
            spin_Numbering_At.set_orientation(gtk.Orientation.HORIZONTAL)
            spin_Numbering_Start.set_orientation(gtk.Orientation.HORIZONTAL)
            spin_Numbering_Increment.set_orientation(gtk.Orientation.HORIZONTAL)
            spin_Numbering_Padding.set_orientation(gtk.Orientation.HORIZONTAL)
            spin_File_Name_Min.set_orientation(gtk.Orientation.HORIZONTAL)
            spin_File_Name_Max.set_orientation(gtk.Orientation.HORIZONTAL)

    def set_scrollwindow_Data_Grid_height(self, new_height):  # Set the height of the data grid
        scrollwindow_Data_Grid = self.builder.get_object("scrollwindow_Data_Grid")
        if int(new_height) >= 0:
            scrollwindow_Data_Grid.set_size_request(scrollwindow_Data_Grid.get_allocated_width(), int(new_height))
        else:
            scrollwindow_Data_Grid.set_size_request(scrollwindow_Data_Grid.get_allocated_width(), 400)  # Default is 400

    """ ************************************************************************************************************ """
    #  These are the various widget's signal handler functions:  UI elements that are buttons & dialogs
    """ ************************************************************************************************************ """

    def button_Rename_Pairs_clicked(self, widget):
        global rename_pairs_from_file
        global rename_pairs_file_to_load
        # Clear out the existing rename_pairs_from_file and remove the red border from the button
        rename_pairs_from_file.clear()
        self.rename_pairs_file = False
        button_Rename_Pairs = self.builder.get_object("button_Rename_Pairs")
        button_Rename_Pairs.get_style_context().remove_class('red-border')
        open_dialog = gtk.FileChooserDialog(title="Please choose a rename pairs \'.txt\' file", parent=None, action=gtk.FileChooserAction.OPEN)
        open_dialog.set_current_folder(default_folder_path)
        open_dialog.add_buttons(gtk.STOCK_CANCEL, gtk.ResponseType.CANCEL, gtk.STOCK_OPEN, gtk.ResponseType.OK)
        open_dialog.set_local_only(False)
        open_dialog.set_modal(True)
        # *.txt filter
        filter = gtk.FileFilter()
        filter.set_name("txt files")
        filter.add_pattern("*.txt")
        open_dialog.add_filter(filter)
        response = open_dialog.run()
        file = ""
        if response == gtk.ResponseType.OK:
            file = open_dialog.get_filename()
        elif response == gtk.ResponseType.CANCEL:
            file = ""
        open_dialog.destroy()
        if file != "":
            rename_pairs_file_to_load = file  # Update path the rename pairs file
            read_in_rename_pairs_file()  # Read in the rename pairs file
            if len(rename_pairs_from_file) > 0:  # If rename_pairs_from_file has any rename pairs, set the border of the button to red
                button_Rename_Pairs.get_style_context().add_class('red-border')
                self.rename_pairs_file = True

    def button_Refresh_clicked(self, widget):
        self.clear_Data_Grid()
        populate_files_Full(self.builder.get_object("entry_Mask").get_text(),
                            self.builder.get_object("checkbox_Folders").get_active(),
                            self.builder.get_object("checkbox_Subfolders").get_active(),
                            self.builder.get_object("checkbox_Files").get_active(),
                            self.builder.get_object("checkbox_Hidden").get_active(),
                            self.builder.get_object("spin_File_Name_Min").get_value_as_int(),
                            self.builder.get_object("spin_File_Name_Max").get_value_as_int(),
                            )
        self.load_Data_Grid()
        self.resize_column_widths()
        self.update_status_labels()

    def button_Refresh_and_Reselect_clicked(self, widget):
        # Save selected rows
        treeview_Data_Grid = self.builder.get_object("treeview_Data_Grid")
        treeselection = treeview_Data_Grid.get_selection()
        model, items = treeselection.get_selected_rows()
        temp_indexes = []  # Holds the rows indexes of the currently selected rows
        temp_treepaths = []  # Holds the TreePath objects of the currently selected rows
        if len(model) > 0:
            for item in items:  # Build list of the currently selected rows
                temp_indexes.append(int(str(item)))
                temp_treepaths.append(item)
        self.clear_Data_Grid()
        populate_files_Full(self.builder.get_object("entry_Mask").get_text(),
                            self.builder.get_object("checkbox_Folders").get_active(),
                            self.builder.get_object("checkbox_Subfolders").get_active(),
                            self.builder.get_object("checkbox_Files").get_active(),
                            self.builder.get_object("checkbox_Hidden").get_active(),
                            self.builder.get_object("spin_File_Name_Min").get_value_as_int(),
                            self.builder.get_object("spin_File_Name_Max").get_value_as_int(),
                            )
        self.load_Data_Grid()
        self.resize_column_widths()
        self.update_status_labels()
        # Re-select selected rows
        for x in range(len(temp_treepaths)):  # Unselect the currently selected rows
            treeselection.select_path(temp_treepaths[x])
        for x in range(len(model)):  # Select the currently unselected rows
            if x in temp_indexes:
                treeselection.select_path(x)

    def button_Reset_clicked(self, widget):
        # I need to get all box 1-9 elements and manually reset them to default... I wish there was a better way...
        # Set data grid selection to none, that will speed this up
        treeview_Data_Grid = self.builder.get_object("treeview_Data_Grid")
        treeselection = treeview_Data_Grid.get_selection()
        treeselection.unselect_all()
        # box 1
        combo_Name = self.builder.get_object("combo_Name")
        combo_Name_Entry = self.builder.get_object("combo_Name_Entry")
        combo_Name.set_entry_text_column(0)
        combo_Name.set_active(0)
        entry_Name_Fixed = self.builder.get_object("entry_Name_Fixed")
        entry_Name_Fixed.set_text("")
        # box 2
        entry_Replace_Search = self.builder.get_object("entry_Replace_Search")
        entry_Replace_Search.set_text("")
        checkbox_Replace_Case = self.builder.get_object("checkbox_Replace_Case")
        checkbox_Replace_Case.set_active(False)  # Default is unchecked (i.e. case inseneitive)
        entry_Replace_With = self.builder.get_object("entry_Replace_With")
        entry_Replace_With.set_text("")
        # box 3
        combo_Case = self.builder.get_object("combo_Case")
        combo_Case_Entry = self.builder.get_object("combo_Case_Entry")
        combo_Case.set_entry_text_column(0)
        combo_Case.set_active(0)
        # box 4
        spin_Remove_First = self.builder.get_object("spin_Remove_First")
        spin_Remove_First.set_value(0)
        spin_Remove_Last = self.builder.get_object("spin_Remove_Last")
        spin_Remove_Last.set_value(0)
        spin_Remove_From = self.builder.get_object("spin_Remove_From")
        spin_Remove_From.set_value(0)
        spin_Remove_To = self.builder.get_object("spin_Remove_To")
        spin_Remove_To.set_value(0)
        combo_Remove_Crop = self.builder.get_object("combo_Remove_Crop")
        combo_Remove_Crop_Entry = self.builder.get_object("combo_Remove_Crop_Entry")
        combo_Remove_Crop.set_entry_text_column(0)
        combo_Remove_Crop.set_active(0)
        entry_Remove_Crop = self.builder.get_object("entry_Remove_Crop")
        entry_Remove_Crop.set_text("")
        # box 5
        entry_Add_Insert = self.builder.get_object("entry_Add_Insert")
        entry_Add_Insert.set_text("")
        entry_Add_Suffix = self.builder.get_object("entry_Add_Suffix")
        entry_Add_Suffix.set_text("")
        entry_Add_Prefix = self.builder.get_object("entry_Add_Prefix")
        entry_Add_Prefix.set_text("")
        spin_Add_Insert = self.builder.get_object("spin_Add_Insert")
        spin_Add_Insert.set_value(0)
        # box 6
        combo_Append_Folder_Name = self.builder.get_object("combo_Append_Folder_Name")
        combo_Append_Folder_Name_Entry = self.builder.get_object("combo_Append_Folder_Name_Entry")
        combo_Append_Folder_Name.set_entry_text_column(0)
        combo_Append_Folder_Name.set_active(0)
        entry_Append_Folder_Name_Separator = self.builder.get_object("entry_Append_Folder_Name_Separator")
        entry_Append_Folder_Name_Separator.set_text("")
        # box 7
        combo_Numbering = self.builder.get_object("combo_Numbering")
        combo_Numbering_Entry = self.builder.get_object("combo_Numbering_Entry")
        combo_Numbering.set_entry_text_column(0)
        combo_Numbering.set_active(0)
        spin_Numbering_At = self.builder.get_object("spin_Numbering_At")
        spin_Numbering_At.set_value(0)
        spin_Numbering_Increment = self.builder.get_object("spin_Numbering_Increment")
        spin_Numbering_Increment.set_value(1)
        spin_Numbering_Padding = self.builder.get_object("spin_Numbering_Padding")
        spin_Numbering_Padding.set_value(1)
        spin_Numbering_Start = self.builder.get_object("spin_Numbering_Start")
        spin_Numbering_Start.set_value(1)
        checkbox_Numbering_Per_Folder = self.builder.get_object("checkbox_Numbering_Per_Folder")
        checkbox_Numbering_Per_Folder.set_active(False)
        entry_Numbering_Separator = self.builder.get_object("entry_Numbering_Separator")
        entry_Numbering_Separator.set_text("")
        # box 8
        combo_Extension = self.builder.get_object("combo_Extension")
        combo_Extension_entry = self.builder.get_object("combo_Extension_entry")
        combo_Extension.set_entry_text_column(0)
        combo_Extension.set_active(0)
        entry_Extension = self.builder.get_object("entry_Extension")
        entry_Extension.set_text("")
        # box 9
        checkbox_Folders = self.builder.get_object("checkbox_Folders")
        checkbox_Folders.set_active(True)
        checkbox_Subfolders = self.builder.get_object("checkbox_Subfolders")
        checkbox_Subfolders.set_active(False)
        checkbox_Files = self.builder.get_object("checkbox_Files")
        checkbox_Files.set_active(True)
        checkbox_Hidden = self.builder.get_object("checkbox_Hidden")
        checkbox_Hidden.set_active(False)
        entry_Mask = self.builder.get_object("entry_Mask")
        entry_Mask.set_text("*.*")
        spin_File_Name_Min = self.builder.get_object("spin_File_Name_Min")
        spin_File_Name_Min.set_value(0)
        spin_File_Name_Max = self.builder.get_object("spin_File_Name_Max")
        spin_File_Name_Max.set_value(0)
        # Import Rename Pairs button
        global rename_pairs_from_file
        rename_pairs_from_file.clear()
        button_Rename_Pairs = self.builder.get_object("button_Rename_Pairs")
        button_Rename_Pairs.get_style_context().remove_class('red-border')
        # Re-Apply custom settings
        self.apply_application_settings()
        self.update_status_labels()

    def button_Rename_clicked(self, widget):
        # Map between model[item][] and files_Full[]
        # model[item][0] = files_Full[4] = Current_Name
        # model[item][1] = files_Full[5] = New_Name
        # model[item][2] = files_Full[2] = Sub_Directory
        # model[item][3] = files_Full[6] = Size
        # model[item][4] = files_Full[7] = Date_Modified
        # model[item][5] = files_Full[9] = Status
        # model[item][6] = files_Full[0] = Full_Path
        # model[item][7] = files_Full[1] = Local_Path
        # model[item][8] = files_Full[3] = Type
        # model[item][9] = files_Full[8] = Hidden
        global directory_counts
        global rename_pairs
        for data in directory_counts:
            directory_counts[data] = 0
        # Clear out the rename_pairs
        rename_pairs.clear()
        # Get selected rows and rename them
        treeview_Data_Grid = self.builder.get_object("treeview_Data_Grid")
        selection = treeview_Data_Grid.get_selection()
        model, items = selection.get_selected_rows()
        if len(items) > 0:  # Don't bother renaming if there isn't at least one selected item
            if items:
                for item in items:
                    # Populate the rename_pairs with the selected rows
                    if model[item][5] != "No change...":  # Don't need to include rows are "No change..."
                        rename_pairs.append([model[item][0], model[item][1], model[item][5], model[item][6], model[item][8]])
            # Call the rename function
            self.rename_files()
            # Update the Status column with the status (file rename success) from rename_files()
            if items:
                for item in items:
                    # Loop through all of the rename_pairs matching Full Path to then get Status
                    for loop in range(len(rename_pairs)):
                        if rename_pairs[loop][3] == model[item][6]:  # If the rename_pairs[Full_Path] == model[item][Full_Path]
                            model[item][5] = rename_pairs[loop][2]  # Update Status to the rename_pairs[Status]
                            if model[item][5] == "Renamed!":
                                model[item][0] = rename_pairs[loop][1]  # Update Current Name to the  rename_pairs[New Name]
                                model[item][6] = update_full_path_with_new_name(model[item][6], model[item][0], model[item][8])  # Update Full Path to the new full path with the updated  rename_pairs[New Name]
                                model[item][7] = update_local_path_with_new_value(model[item][6], model[item][0], model[item][8])  # Update Local Path
            self.save_history()
        self.update_status_labels()

    def button_About_clicked(self, widget):  # Creates the About Dialog
        about = gtk.AboutDialog()
        about.connect("key-press-event", self.about_dialog_key_press)  # Easter Egg:  Check to see if Konami code has been entered
        about.set_program_name("Linux File Rename Utility")
        about.set_version("Version 1.4")
        about.set_copyright("Copyright (c) BSFEMA")
        about.set_comments("Python application using Gtk and Glade for renaming files/folders in Linux")
        about.set_license_type(gtk.License(7))  # License = MIT_X11
        about.set_website("https://github.com/BSFEMA/linux_file_rename_utility")
        about.set_website_label("https://github.com/BSFEMA/linux_file_rename_utility")
        about.set_authors(["BSFEMA"])
        about.set_artists(["BSFEMA"])
        about.set_documenters(["BSFEMA"])
        about.run()
        about.destroy()

    def about_dialog_key_press(self, widget, event):  # Easter Egg:  Check to see if Konami code has been entered
        global konami_code
        keyname = gdk.keyval_name(event.keyval)
        if len(konami_code) == 10:
            konami_code.pop(0)
            konami_code.append(keyname)
        else:
            konami_code.append(keyname)
        if (konami_code == ['Up', 'Up', 'Down', 'Down', 'Left', 'Right', 'Left', 'Right', 'b', 'a']) or (konami_code == ['Up', 'Up', 'Down', 'Down', 'Left', 'Right', 'Left', 'Right', 'B', 'A']):
            self.dialog_BSFEMA(self)
            # print("Konami code entered:  " + str(konami_code))
            konami_code.clear()

    def dialog_BSFEMA(self, widget):  # Creates the "BSFEMA" dialog that just spins my logo
        dialog = gtk.Dialog(title="BSFEMA", parent=None)
        dialog.add_buttons(gtk.STOCK_OK, gtk.ResponseType.OK)
        dialog.set_modal(True)
        # dialog.set_default_size(200, 200)
        area = dialog.get_content_area()
        dialog.image = gtk.Image()
        dialog.image.set_from_file(os.path.join(sys.path[0], "linux_file_rename_utility.svg"))
        dialog.image.get_style_context().add_class('spinner')
        area.add(dialog.image)
        dialog.show_all()
        dialog.run()
        dialog.destroy()

    def button_Open_Settings_clicked(self, widget):
        global settings_file_to_load
        open_dialog = gtk.FileChooserDialog(title="Please choose a \'settings.txt\' file", parent=None, action=gtk.FileChooserAction.OPEN)
        open_dialog.set_current_folder(os.path.expanduser("~/.config/BSFEMA/"))
        open_dialog.add_buttons(gtk.STOCK_CANCEL, gtk.ResponseType.CANCEL, gtk.STOCK_OPEN, gtk.ResponseType.OK)
        open_dialog.set_local_only(False)
        open_dialog.set_modal(True)
        # *.txt filter
        filter = gtk.FileFilter()
        filter.set_name("txt files")
        filter.add_pattern("*.txt")
        open_dialog.add_filter(filter)
        response = open_dialog.run()
        file = ""
        if response == gtk.ResponseType.OK:
            file = open_dialog.get_filename()
        elif response == gtk.ResponseType.CANCEL:
            file = ""
        open_dialog.destroy()
        if file != "":
            settings_file_to_load = file  # Update path the application settings
            read_in_application_settings()  # Read in new application settings
            self.apply_application_settings()  # Apply custom user application settings

    def button_SaveAs_Settings_clicked(self, widget):  # Saves Settings to settings.txt
        saveas_dialog = gtk.FileChooserDialog(title="Please save a \'settings.txt\' file", parent=None, action=gtk.FileChooserAction.SAVE)
        saveas_dialog.set_current_folder(os.path.expanduser("~/.config/BSFEMA/"))
        saveas_dialog.add_buttons(gtk.STOCK_CANCEL, gtk.ResponseType.CANCEL, gtk.STOCK_SAVE_AS, gtk.ResponseType.OK)
        saveas_dialog.set_local_only(False)
        saveas_dialog.set_modal(True)
        # *.txt filter
        filter = gtk.FileFilter()
        filter.set_name("txt files")
        filter.add_pattern("*.txt")
        saveas_dialog.add_filter(filter)
        response = saveas_dialog.run()
        if response == gtk.ResponseType.OK:
            file = saveas_dialog.get_filename()
        elif response == gtk.ResponseType.CANCEL:
            file = ""
        saveas_dialog.destroy()
        if file != "":
            # make sure that the file ends in .txt
            if file[-4:] != ".txt":
                file = file + ".txt"
            global application_Settings
            file = open(os.path.expanduser(file), "w", encoding='utf-8-sig')
            # box 1
            file.write("# box 1\n")
            combo_Name = self.builder.get_object("combo_Name")
            combo_Name_Entry = self.builder.get_object("combo_Name_Entry")
            file.write("combo_Name=" + combo_Name_Entry.get_text() + "\n")
            entry_Name_Fixed = self.builder.get_object("entry_Name_Fixed")
            file.write("entry_Name_Fixed=" + entry_Name_Fixed.get_text() + "\n")
            # box 2
            file.write("# box 2\n")
            entry_Replace_Search = self.builder.get_object("entry_Replace_Search")
            file.write("entry_Replace_Search=" + entry_Replace_Search.get_text() + "\n")
            checkbox_Replace_Case = self.builder.get_object("checkbox_Replace_Case")
            file.write("checkbox_Replace_Case=" + str(checkbox_Replace_Case.get_active()) + "\n")
            entry_Replace_With = self.builder.get_object("entry_Replace_With")
            file.write("entry_Replace_With=" + entry_Replace_With.get_text() + "\n")
            # box 3
            file.write("# box 3\n")
            combo_Case = self.builder.get_object("combo_Case")
            combo_Case_Entry = self.builder.get_object("combo_Case_Entry")
            file.write("combo_Case=" + combo_Case_Entry.get_text() + "\n")
            # box 4
            file.write("# box 4\n")
            spin_Remove_First = self.builder.get_object("spin_Remove_First")
            file.write("spin_Remove_First=" + str(int(spin_Remove_First.get_value())) + "\n")
            spin_Remove_Last = self.builder.get_object("spin_Remove_Last")
            file.write("spin_Remove_Last=" + str(int(spin_Remove_Last.get_value())) + "\n")
            spin_Remove_From = self.builder.get_object("spin_Remove_From")
            file.write("spin_Remove_From=" + str(int(spin_Remove_From.get_value())) + "\n")
            spin_Remove_To = self.builder.get_object("spin_Remove_To")
            file.write("spin_Remove_To=" + str(int(spin_Remove_To.get_value())) + "\n")
            combo_Remove_Crop = self.builder.get_object("combo_Remove_Crop")
            combo_Remove_Crop_Entry = self.builder.get_object("combo_Remove_Crop_Entry")
            file.write("combo_Remove_Crop=" + combo_Remove_Crop_Entry.get_text() + "\n")
            entry_Remove_Crop = self.builder.get_object("entry_Remove_Crop")
            file.write("entry_Remove_Crop=" + entry_Remove_Crop.get_text() + "\n")
            # box 5
            file.write("# box 5\n")
            entry_Add_Insert = self.builder.get_object("entry_Add_Insert")
            file.write("entry_Add_Insert=" + entry_Add_Insert.get_text() + "\n")
            entry_Add_Suffix = self.builder.get_object("entry_Add_Suffix")
            file.write("entry_Add_Suffix=" + entry_Add_Suffix.get_text() + "\n")
            entry_Add_Prefix = self.builder.get_object("entry_Add_Prefix")
            file.write("entry_Add_Prefix=" + entry_Add_Prefix.get_text() + "\n")
            spin_Add_Insert = self.builder.get_object("spin_Add_Insert")
            file.write("spin_Add_Insert=" + str(int(spin_Add_Insert.get_value())) + "\n")
            # box 6
            file.write("# box 6\n")
            combo_Append_Folder_Name = self.builder.get_object("combo_Append_Folder_Name")
            combo_Append_Folder_Name_Entry = self.builder.get_object("combo_Append_Folder_Name_Entry")
            file.write("combo_Append_Folder_Name=" + combo_Append_Folder_Name_Entry.get_text() + "\n")
            entry_Append_Folder_Name_Separator = self.builder.get_object("entry_Append_Folder_Name_Separator")
            file.write("entry_Append_Folder_Name_Separator=" + entry_Append_Folder_Name_Separator.get_text() + "\n")
            # box 7
            file.write("# box 7\n")
            combo_Numbering = self.builder.get_object("combo_Numbering")
            combo_Numbering_Entry = self.builder.get_object("combo_Numbering_Entry")
            file.write("combo_Numbering=" + combo_Numbering_Entry.get_text() + "\n")
            spin_Numbering_At = self.builder.get_object("spin_Numbering_At")
            file.write("spin_Numbering_At=" + str(int(spin_Numbering_At.get_value())) + "\n")
            spin_Numbering_Increment = self.builder.get_object("spin_Numbering_Increment")
            file.write("spin_Numbering_Increment=" + str(int(spin_Numbering_Increment.get_value())) + "\n")
            spin_Numbering_Padding = self.builder.get_object("spin_Numbering_Padding")
            file.write("spin_Numbering_Padding=" + str(int(spin_Numbering_Padding.get_value())) + "\n")
            spin_Numbering_Start = self.builder.get_object("spin_Numbering_Start")
            file.write("spin_Numbering_Start=" + str(int(spin_Numbering_Start.get_value())) + "\n")
            checkbox_Numbering_Per_Folder = self.builder.get_object("checkbox_Numbering_Per_Folder")
            file.write("checkbox_Numbering_Per_Folder=" + str(checkbox_Numbering_Per_Folder.get_active()) + "\n")
            entry_Numbering_Separator = self.builder.get_object("entry_Numbering_Separator")
            file.write("entry_Numbering_Separator=" + entry_Numbering_Separator.get_text() + "\n")
            # box 8
            file.write("# box 8\n")
            combo_Extension = self.builder.get_object("combo_Extension")
            combo_Extension_entry = self.builder.get_object("combo_Extension_entry")
            file.write("combo_Extension=" + combo_Extension_entry.get_text() + "\n")
            entry_Extension = self.builder.get_object("entry_Extension")
            file.write("entry_Extension=" + entry_Extension.get_text() + "\n")
            # box 9
            file.write("# box 9\n")
            checkbox_Folders = self.builder.get_object("checkbox_Folders")
            file.write("checkbox_Folders=" + str(checkbox_Folders.get_active()) + "\n")
            checkbox_Subfolders = self.builder.get_object("checkbox_Subfolders")
            file.write("checkbox_Subfolders=" + str(checkbox_Subfolders.get_active()) + "\n")
            checkbox_Files = self.builder.get_object("checkbox_Files")
            file.write("checkbox_Files=" + str(checkbox_Files.get_active()) + "\n")
            checkbox_Hidden = self.builder.get_object("checkbox_Hidden")
            file.write("checkbox_Hidden=" + str(checkbox_Hidden.get_active()) + "\n")
            entry_Mask = self.builder.get_object("entry_Mask")
            file.write("entry_Mask=" + entry_Mask.get_text() + "\n")
            spin_File_Name_Min = self.builder.get_object("spin_File_Name_Min")
            file.write("spin_File_Name_Min=" + str(int(spin_File_Name_Min.get_value())) + "\n")
            spin_File_Name_Max = self.builder.get_object("spin_File_Name_Max")
            file.write("spin_File_Name_Max=" + str(int(spin_File_Name_Max.get_value())) + "\n")
            # Save History
            file.write("# Save History\n")
            checkbox_Save_History = self.builder.get_object("checkbox_Save_History")
            file.write("checkbox_Save_History=" + str(checkbox_Save_History.get_active()) + "\n")
            # Data Grid
            file.write("# Data Grid\n")
            treeviewcolumn_Size = self.builder.get_object("treeviewcolumn_Size")
            file.write("treeviewcolumn_Size=" + str(treeviewcolumn_Size.get_visible()) + "\n")
            treeviewcolumn_Date_Modified = self.builder.get_object("treeviewcolumn_Date_Modified")
            file.write("treeviewcolumn_Date_Modified=" + str(treeviewcolumn_Date_Modified.get_visible()) + "\n")
            treeviewcolumn_Full_Path = self.builder.get_object("treeviewcolumn_Full_Path")
            file.write("treeviewcolumn_Full_Path=" + str(treeviewcolumn_Full_Path.get_visible()) + "\n")
            treeviewcolumn_Local_Path = self.builder.get_object("treeviewcolumn_Local_Path")
            file.write("treeviewcolumn_Local_Path=" + str(treeviewcolumn_Local_Path.get_visible()) + "\n")
            treeviewcolumn_Type = self.builder.get_object("treeviewcolumn_Type")
            file.write("treeviewcolumn_Type=" + str(treeviewcolumn_Type.get_visible()) + "\n")
            treeviewcolumn_Hidden = self.builder.get_object("treeviewcolumn_Hidden")
            file.write("treeviewcolumn_Hidden=" + str(treeviewcolumn_Hidden.get_visible()) + "\n")
            # Done
            file.close()

    def button_Save_Settings_clicked(self, widget):  # Saves Settings to settings.txt
        global application_Settings
        file = open(os.path.expanduser("~/.config/BSFEMA/settings.txt"), "w", encoding='utf-8-sig')
        # box 1
        file.write("# box 1\n")
        combo_Name = self.builder.get_object("combo_Name")
        combo_Name_Entry = self.builder.get_object("combo_Name_Entry")
        file.write("combo_Name=" + combo_Name_Entry.get_text() + "\n")
        entry_Name_Fixed = self.builder.get_object("entry_Name_Fixed")
        file.write("entry_Name_Fixed=" + entry_Name_Fixed.get_text() + "\n")
        # box 2
        file.write("# box 2\n")
        entry_Replace_Search = self.builder.get_object("entry_Replace_Search")
        file.write("entry_Replace_Search=" + entry_Replace_Search.get_text() + "\n")
        checkbox_Replace_Case = self.builder.get_object("checkbox_Replace_Case")
        file.write("checkbox_Replace_Case=" + str(checkbox_Replace_Case.get_active()) + "\n")
        entry_Replace_With = self.builder.get_object("entry_Replace_With")
        file.write("entry_Replace_With=" + entry_Replace_With.get_text() + "\n")
        # box 3
        file.write("# box 3\n")
        combo_Case = self.builder.get_object("combo_Case")
        combo_Case_Entry = self.builder.get_object("combo_Case_Entry")
        file.write("combo_Case=" + combo_Case_Entry.get_text() + "\n")
        # box 4
        file.write("# box 4\n")
        spin_Remove_First = self.builder.get_object("spin_Remove_First")
        file.write("spin_Remove_First=" + str(int(spin_Remove_First.get_value())) + "\n")
        spin_Remove_Last = self.builder.get_object("spin_Remove_Last")
        file.write("spin_Remove_Last=" + str(int(spin_Remove_Last.get_value())) + "\n")
        spin_Remove_From = self.builder.get_object("spin_Remove_From")
        file.write("spin_Remove_From=" + str(int(spin_Remove_From.get_value())) + "\n")
        spin_Remove_To = self.builder.get_object("spin_Remove_To")
        file.write("spin_Remove_To=" + str(int(spin_Remove_To.get_value())) + "\n")
        combo_Remove_Crop = self.builder.get_object("combo_Remove_Crop")
        combo_Remove_Crop_Entry = self.builder.get_object("combo_Remove_Crop_Entry")
        file.write("combo_Remove_Crop=" + combo_Remove_Crop_Entry.get_text() + "\n")
        entry_Remove_Crop = self.builder.get_object("entry_Remove_Crop")
        file.write("entry_Remove_Crop=" + entry_Remove_Crop.get_text() + "\n")
        # box 5
        file.write("# box 5\n")
        entry_Add_Insert = self.builder.get_object("entry_Add_Insert")
        file.write("entry_Add_Insert=" + entry_Add_Insert.get_text() + "\n")
        entry_Add_Suffix = self.builder.get_object("entry_Add_Suffix")
        file.write("entry_Add_Suffix=" + entry_Add_Suffix.get_text() + "\n")
        entry_Add_Prefix = self.builder.get_object("entry_Add_Prefix")
        file.write("entry_Add_Prefix=" + entry_Add_Prefix.get_text() + "\n")
        spin_Add_Insert = self.builder.get_object("spin_Add_Insert")
        file.write("spin_Add_Insert=" + str(int(spin_Add_Insert.get_value())) + "\n")
        # box 6
        file.write("# box 6\n")
        combo_Append_Folder_Name = self.builder.get_object("combo_Append_Folder_Name")
        combo_Append_Folder_Name_Entry = self.builder.get_object("combo_Append_Folder_Name_Entry")
        file.write("combo_Append_Folder_Name=" + combo_Append_Folder_Name_Entry.get_text() + "\n")
        entry_Append_Folder_Name_Separator = self.builder.get_object("entry_Append_Folder_Name_Separator")
        file.write("entry_Append_Folder_Name_Separator=" + entry_Append_Folder_Name_Separator.get_text() + "\n")
        # box 7
        file.write("# box 7\n")
        combo_Numbering = self.builder.get_object("combo_Numbering")
        combo_Numbering_Entry = self.builder.get_object("combo_Numbering_Entry")
        file.write("combo_Numbering=" + combo_Numbering_Entry.get_text() + "\n")
        spin_Numbering_At = self.builder.get_object("spin_Numbering_At")
        file.write("spin_Numbering_At=" + str(int(spin_Numbering_At.get_value())) + "\n")
        spin_Numbering_Increment = self.builder.get_object("spin_Numbering_Increment")
        file.write("spin_Numbering_Increment=" + str(int(spin_Numbering_Increment.get_value())) + "\n")
        spin_Numbering_Padding = self.builder.get_object("spin_Numbering_Padding")
        file.write("spin_Numbering_Padding=" + str(int(spin_Numbering_Padding.get_value())) + "\n")
        spin_Numbering_Start = self.builder.get_object("spin_Numbering_Start")
        file.write("spin_Numbering_Start=" + str(int(spin_Numbering_Start.get_value())) + "\n")
        checkbox_Numbering_Per_Folder = self.builder.get_object("checkbox_Numbering_Per_Folder")
        file.write("checkbox_Numbering_Per_Folder=" + str(checkbox_Numbering_Per_Folder.get_active()) + "\n")
        entry_Numbering_Separator = self.builder.get_object("entry_Numbering_Separator")
        file.write("entry_Numbering_Separator=" + entry_Numbering_Separator.get_text() + "\n")
        # box 8
        file.write("# box 8\n")
        combo_Extension = self.builder.get_object("combo_Extension")
        combo_Extension_entry = self.builder.get_object("combo_Extension_entry")
        file.write("combo_Extension=" + combo_Extension_entry.get_text() + "\n")
        entry_Extension = self.builder.get_object("entry_Extension")
        file.write("entry_Extension=" + entry_Extension.get_text() + "\n")
        # box 9
        file.write("# box 9\n")
        checkbox_Folders = self.builder.get_object("checkbox_Folders")
        file.write("checkbox_Folders=" + str(checkbox_Folders.get_active()) + "\n")
        checkbox_Subfolders = self.builder.get_object("checkbox_Subfolders")
        file.write("checkbox_Subfolders=" + str(checkbox_Subfolders.get_active()) + "\n")
        checkbox_Files = self.builder.get_object("checkbox_Files")
        file.write("checkbox_Files=" + str(checkbox_Files.get_active()) + "\n")
        checkbox_Hidden = self.builder.get_object("checkbox_Hidden")
        file.write("checkbox_Hidden=" + str(checkbox_Hidden.get_active()) + "\n")
        entry_Mask = self.builder.get_object("entry_Mask")
        file.write("entry_Mask=" + entry_Mask.get_text() + "\n")
        spin_File_Name_Min = self.builder.get_object("spin_File_Name_Min")
        file.write("spin_File_Name_Min=" + str(int(spin_File_Name_Min.get_value())) + "\n")
        spin_File_Name_Max = self.builder.get_object("spin_File_Name_Max")
        file.write("spin_File_Name_Max=" + str(int(spin_File_Name_Max.get_value())) + "\n")
        # Save History
        file.write("# Save History\n")
        checkbox_Save_History = self.builder.get_object("checkbox_Save_History")
        file.write("checkbox_Save_History=" + str(checkbox_Save_History.get_active()) + "\n")
        # Data Grid
        file.write("# Data Grid\n")
        treeviewcolumn_Size = self.builder.get_object("treeviewcolumn_Size")
        file.write("treeviewcolumn_Size=" + str(treeviewcolumn_Size.get_visible()) + "\n")
        treeviewcolumn_Date_Modified = self.builder.get_object("treeviewcolumn_Date_Modified")
        file.write("treeviewcolumn_Date_Modified=" + str(treeviewcolumn_Date_Modified.get_visible()) + "\n")
        treeviewcolumn_Full_Path = self.builder.get_object("treeviewcolumn_Full_Path")
        file.write("treeviewcolumn_Full_Path=" + str(treeviewcolumn_Full_Path.get_visible()) + "\n")
        treeviewcolumn_Local_Path = self.builder.get_object("treeviewcolumn_Local_Path")
        file.write("treeviewcolumn_Local_Path=" + str(treeviewcolumn_Local_Path.get_visible()) + "\n")
        treeviewcolumn_Type = self.builder.get_object("treeviewcolumn_Type")
        file.write("treeviewcolumn_Type=" + str(treeviewcolumn_Type.get_visible()) + "\n")
        treeviewcolumn_Hidden = self.builder.get_object("treeviewcolumn_Hidden")
        file.write("treeviewcolumn_Hidden=" + str(treeviewcolumn_Hidden.get_visible()) + "\n")
        # Done
        file.close()

    """ ************************************************************************************************************ """
    # These are the various class functions
    """ ************************************************************************************************************ """

    def apply_application_settings(self):  # Applies the user's default or custom widget settings
        global application_Settings
        for setting in application_Settings:
            # HIDDEN SETTINGS
            if setting[0] == "window_maximize" and setting[1] == "True":
                window = self.builder.get_object("main_window")
                window.maximize()
            if setting[0] == "scrollwindow_Data_Grid" and setting[1] != "" and int(setting[1]):
                self.set_scrollwindow_Data_Grid_height(setting[1])
            if setting[0] == "spinner_orientation" and setting[1] != "":
                self.set_spinner_orientation(setting[1])
            if setting[0] == "button_Rename_image" and setting[1] == "True":
                button_Rename = self.builder.get_object("button_Rename")
                button_Rename.set_always_show_image(True)
                self.button_Rename_image = gtk.Image()
                self.button_Rename_image.set_from_file(os.path.join(sys.path[0], "linux_file_rename_utility.svg"))
                self.button_Rename_image.get_style_context().add_class('spinner')
                button_Rename.set_image(self.button_Rename_image)
                button_Rename.set_image_position(gtk.PositionType.TOP)
            # Buttons
            if setting[0] == "checkbox_Save_History" and setting[1] == "False":
                checkbox_Save_History = self.builder.get_object(setting[0])
                checkbox_Save_History.set_active(False)
            # Data Grid:
            if setting[0] == "treeviewcolumn_Full_Path" and setting[1] == "True":
                treeviewcolumn_Full_Path = self.builder.get_object(setting[0])
                treeviewcolumn_Full_Path.set_visible(True)
            if setting[0] == "treeviewcolumn_Local_Path" and setting[1] == "True":
                treeviewcolumn_Local_Path = self.builder.get_object(setting[0])
                treeviewcolumn_Local_Path.set_visible(True)
            if setting[0] == "treeviewcolumn_Type" and setting[1] == "True":
                treeviewcolumn_Type = self.builder.get_object(setting[0])
                treeviewcolumn_Type.set_visible(True)
            if setting[0] == "treeviewcolumn_Hidden" and setting[1] == "True":
                treeviewcolumn_Hidden = self.builder.get_object(setting[0])
                treeviewcolumn_Hidden.set_visible(True)
            if setting[0] == "treeviewcolumn_Size" and setting[1] == "False":
                treeviewcolumn_Size = self.builder.get_object(setting[0])
                treeviewcolumn_Size.set_visible(False)
            if setting[0] == "treeviewcolumn_Date_Modified" and setting[1] == "False":
                treeviewcolumn_Date_Modified = self.builder.get_object(setting[0])
                treeviewcolumn_Date_Modified.set_visible(False)
            # Box_9
            if setting[0] == "checkbox_Folders" and setting[1] == "True":
                checkbox_Folders = self.builder.get_object(setting[0])
                checkbox_Folders.set_active(True)
            elif setting[0] == "checkbox_Folders" and setting[1] == "False":
                checkbox_Folders = self.builder.get_object(setting[0])
                checkbox_Folders.set_active(False)
            if setting[0] == "checkbox_Subfolders" and setting[1] == "True":
                checkbox_Subfolders = self.builder.get_object(setting[0])
                checkbox_Subfolders.set_active(True)
            elif setting[0] == "checkbox_Subfolders" and setting[1] == "False":
                checkbox_Subfolders = self.builder.get_object(setting[0])
                checkbox_Subfolders.set_active(False)
            if setting[0] == "checkbox_Files" and setting[1] == "True":
                checkbox_Files = self.builder.get_object(setting[0])
                checkbox_Files.set_active(True)
            elif setting[0] == "checkbox_Files" and setting[1] == "False":
                checkbox_Files = self.builder.get_object(setting[0])
                checkbox_Files.set_active(False)
            if setting[0] == "checkbox_Hidden" and setting[1] == "True":
                checkbox_Hidden = self.builder.get_object(setting[0])
                checkbox_Hidden.set_active(True)
            elif setting[0] == "checkbox_Hidden" and setting[1] == "False":
                checkbox_Hidden = self.builder.get_object(setting[0])
                checkbox_Hidden.set_active(False)
            if setting[0] == "checkbox_Save_History" and setting[1] == "True":
                checkbox_Save_History = self.builder.get_object(setting[0])
                checkbox_Save_History.set_active(True)
            if setting[0] == "entry_Mask" and setting[1] != "":
                entry_Mask = self.builder.get_object(setting[0])
                entry_Mask.set_text(setting[1])
            if setting[0] == "spin_File_Name_Min" and setting[1] != "":
                spin_File_Name_Min = self.builder.get_object(setting[0])
                try:
                    spin_File_Name_Min.set_value(int(setting[1]))
                except Exception:
                    print("\"spin_File_Name_Min\" in the settings.txt file probably not set to an integer value")
            if setting[0] == "spin_File_Name_Max" and setting[1] != "":
                spin_File_Name_Max = self.builder.get_object(setting[0])
                try:
                    spin_File_Name_Max.set_value(int(setting[1]))
                except Exception:
                    print("\"spin_File_Name_Min\" in the settings.txt file probably not set to an integer value")
            # Box_1
            if setting[0] == "combo_Name" and setting[1] != "":  # [Keep], Removed, Fixed
                combo_Name = self.builder.get_object(setting[0])
                if setting[1] == "Keep":
                    # combo_Name.set_entry_text_column(0)
                    combo_Name.set_active(0)
                elif setting[1] == "Remove":
                    # combo_Name.set_entry_text_column(1)
                    combo_Name.set_active(1)
                elif setting[1] == "Fixed":
                    #combo_Name.set_entry_text_column(2)
                    combo_Name.set_active(2)
                else:  # Default
                    # combo_Name.set_entry_text_column(0)
                    combo_Name.set_active(0)
            if setting[0] == "entry_Name_Fixed" and setting[1] != "":
                entry_Name_Fixed = self.builder.get_object(setting[0])
                if entry_Name_Fixed.get_editable():
                    entry_Name_Fixed.set_text(setting[1])
           # Box_2
            if setting[0] == "entry_Replace_Search" and setting[1] != "":
                entry_Replace_Search = self.builder.get_object(setting[0])
                entry_Replace_Search.set_text(setting[1])
            if setting[0] == "checkbox_Replace_Case" and setting[1] == "True":
                checkbox_Folders = self.builder.get_object(setting[0])
                checkbox_Folders.set_active(True)
            elif setting[0] == "checkbox_Replace_Case" and setting[1] == "False":
                checkbox_Folders = self.builder.get_object(setting[0])
                checkbox_Folders.set_active(False)
            if setting[0] == "entry_Replace_With" and setting[1] != "":
                entry_Replace_With = self.builder.get_object(setting[0])
                entry_Replace_With.set_text(setting[1])
            # Box_3
            if setting[0] == "combo_Case" and setting[1] != "":  # [Same], Upper, Lower, Title, Sentence
                combo_Case = self.builder.get_object(setting[0])
                if setting[1] == "Keep":
                    # combo_Case.set_entry_text_column(0)
                    combo_Case.set_active(0)
                elif setting[1] == "Upper":
                    # combo_Case.set_entry_text_column(1)
                    combo_Case.set_active(1)
                elif setting[1] == "Lower":
                    # combo_Case.set_entry_text_column(2)
                    combo_Case.set_active(2)
                elif setting[1] == "Title":
                    # combo_Case.set_entry_text_column(3)
                    combo_Case.set_active(3)
                elif setting[1] == "Sentence":
                    # combo_Case.set_entry_text_column(4)
                    combo_Case.set_active(4)
                else:  # Default
                    # combo_Case.set_entry_text_column(0)
                    combo_Case.set_active(0)
            # Box_4
            if setting[0] == "spin_Remove_First" and setting[1] != "":
                spin_Remove_First = self.builder.get_object(setting[0])
                try:
                    spin_Remove_First.set_value(int(setting[1]))
                except Exception:
                    print("\"spin_Remove_First\" in the settings.txt file probably not set to an integer value")
            if setting[0] == "spin_Remove_Last" and setting[1] != "":
                spin_Remove_Last = self.builder.get_object(setting[0])
                try:
                    spin_Remove_Last.set_value(int(setting[1]))
                except Exception:
                    print("\"spin_Remove_Last\" in the settings.txt file probably not set to an integer value")
            if setting[0] == "spin_Remove_From" and setting[1] != "":
                spin_Remove_From = self.builder.get_object(setting[0])
                try:
                    spin_Remove_From.set_value(int(setting[1]))
                except Exception:
                    print("\"spin_Remove_From\" in the settings.txt file probably not set to an integer value")
            if setting[0] == "spin_Remove_To" and setting[1] != "":
                spin_Remove_To = self.builder.get_object(setting[0])
                try:
                    spin_Remove_To.set_value(int(setting[1]))
                except Exception:
                    print("\"spin_Remove_To\" in the settings.txt file probably not set to an integer value")
            if setting[0] == "combo_Remove_Crop" and setting[1] != "":  # [None], Before First, Before Last, After First, After Last
                combo_Remove_Crop = self.builder.get_object(setting[0])
                if setting[1] == "None":
                    combo_Remove_Crop.set_active(0)
                elif setting[1] == "Before First":
                    combo_Remove_Crop.set_active(1)
                elif setting[1] == "Before Last":
                    combo_Remove_Crop.set_active(2)
                elif setting[1] == "After First":
                    combo_Remove_Crop.set_active(3)
                elif setting[1] == "After Last":
                    combo_Remove_Crop.set_active(4)
                else:  # Default
                    combo_Remove_Crop.set_active(0)
            if setting[0] == "entry_Remove_Crop" and setting[1] != "":
                entry_Remove_Crop = self.builder.get_object(setting[0])
                if entry_Remove_Crop.get_editable():
                    entry_Remove_Crop.set_text(setting[1])
            # Box_5
            if setting[0] == "entry_Add_Prefix" and setting[1] != "":
                entry_Add_Prefix = self.builder.get_object(setting[0])
                entry_Add_Prefix.set_text(setting[1])
            if setting[0] == "entry_Add_Suffix" and setting[1] != "":
                entry_Add_Suffix = self.builder.get_object(setting[0])
                entry_Add_Suffix.set_text(setting[1])
            if setting[0] == "entry_Add_Insert" and setting[1] != "":
                entry_Add_Insert = self.builder.get_object(setting[0])
                entry_Add_Insert.set_text(setting[1])
            if setting[0] == "spin_Add_Insert" and setting[1] != "":
                spin_Add_Insert = self.builder.get_object(setting[0])
                try:
                    spin_Add_Insert.set_value(int(setting[1]))
                except Exception:
                    print("\"spin_Remove_To\" in the settings.txt file probably not set to an integer value")
            # Box_6
            if setting[0] == "combo_Append_Folder_Name" and setting[1] != "":  # [None], Prefix, Suffix
                combo_Append_Folder_Name = self.builder.get_object(setting[0])
                if setting[1] == "None":
                    # combo_Append_Folder_Name.set_entry_text_column(0)
                    combo_Append_Folder_Name.set_active(0)
                elif setting[1] == "Prefix":
                    # combo_Append_Folder_Name.set_entry_text_column(1)
                    combo_Append_Folder_Name.set_active(1)
                elif setting[1] == "Suffix":
                    # combo_Append_Folder_Name.set_entry_text_column(2)
                    combo_Append_Folder_Name.set_active(2)
                else:  # Default
                    # combo_Append_Folder_Name.set_entry_text_column(0)
                    combo_Append_Folder_Name.set_active(0)
            if setting[0] == "entry_Append_Folder_Name_Separator" and setting[1] != "":
                entry_Append_Folder_Name_Separator = self.builder.get_object(setting[0])
                if entry_Append_Folder_Name_Separator.get_editable():
                    entry_Append_Folder_Name_Separator.set_text(setting[1])
            # Box_7
            if setting[0] == "combo_Numbering" and setting[1] != "":  # [None], Prefix, Suffix, Insert
                combo_Numbering = self.builder.get_object(setting[0])
                if setting[1] == "None":
                    # combo_Numbering.set_entry_text_column(0)
                    combo_Numbering.set_active(0)
                elif setting[1] == "Prefix":
                    # combo_Numbering.set_entry_text_column(1)
                    combo_Numbering.set_active(1)
                elif setting[1] == "Suffix":
                    # combo_Numbering.set_entry_text_column(2)
                    combo_Numbering.set_active(2)
                elif setting[1] == "Insert":
                    # combo_Numbering.set_entry_text_column(3)
                    combo_Numbering.set_active(3)
                else:  # Default
                    # combo_Numbering.set_entry_text_column(0)
                    combo_Numbering.set_active(0)
            if setting[0] == "spin_Numbering_At" and setting[1] != "":
                spin_Numbering_At = self.builder.get_object(setting[0])
                try:
                    spin_Numbering_At.set_value(int(setting[1]))
                except Exception:
                    print("\"spin_Numbering_At\" in the settings.txt file probably not set to an integer value")
            if setting[0] == "spin_Numbering_Increment" and setting[1] != "":
                spin_Numbering_Increment = self.builder.get_object(setting[0])
                try:
                    spin_Numbering_Increment.set_value(int(setting[1]))
                except Exception:
                    print("\"spin_Numbering_Increment\" in the settings.txt file probably not set to an integer value")
            if setting[0] == "spin_Numbering_Padding" and setting[1] != "":
                spin_Numbering_Padding = self.builder.get_object(setting[0])
                try:
                    spin_Numbering_Padding.set_value(int(setting[1]))
                except Exception:
                    print("\"spin_Numbering_Padding\" in the settings.txt file probably not set to an integer value")
            if setting[0] == "spin_Numbering_Start" and setting[1] != "":
                spin_Numbering_Start = self.builder.get_object(setting[0])
                try:
                    spin_Numbering_Start.set_value(int(setting[1]))
                except Exception:
                    print("\"spin_Numbering_Start\" in the settings.txt file probably not set to an integer value")
            if setting[0] == "checkbox_Numbering_Per_Folder" and setting[1] == "True":
                checkbox_Numbering_Per_Folder = self.builder.get_object(setting[0])
                checkbox_Numbering_Per_Folder.set_active(True)
            if setting[0] == "entry_Numbering_Separator" and setting[1] != "":
                entry_Numbering_Separator = self.builder.get_object(setting[0])
                entry_Numbering_Separator.set_text(setting[1])
            # Box_8
            if setting[0] == "combo_Extension" and setting[1] != "":  # [Same], Upper, Lower, Fixed, Extra, Remove
                combo_Extension = self.builder.get_object(setting[0])
                if setting[1] == "Same":
                    # combo_Extension.set_entry_text_column(0)
                    combo_Extension.set_active(0)
                elif setting[1] == "Upper":
                    # combo_Extension.set_entry_text_column(1)
                    combo_Extension.set_active(1)
                elif setting[1] == "Lower":
                    # combo_Extension.set_entry_text_column(2)
                    combo_Extension.set_active(2)
                elif setting[1] == "Fixed":
                    # combo_Extension.set_entry_text_column(3)
                    combo_Extension.set_active(3)
                elif setting[1] == "Extra":
                    # combo_Extension.set_entry_text_column(4)
                    combo_Extension.set_active(4)
                elif setting[1] == "Remove":
                    # combo_Extension.set_entry_text_column(5)
                    combo_Extension.set_active(5)
                else:  # Default
                    # combo_Extension.set_entry_text_column(0)
                    combo_Extension.set_active(0)
            if setting[0] == "entry_Extension" and setting[1] != "":
                entry_Extension = self.builder.get_object(setting[0])
                if entry_Extension.get_editable():
                    entry_Extension.set_text(setting[1])

    def update_status_labels(self):  # This updates the 'status bar' labels
        treeview_Data_Grid = self.builder.get_object("treeview_Data_Grid")
        selection = treeview_Data_Grid.get_selection()
        model, items = selection.get_selected_rows()
        label_Status_Rows = self.builder.get_object("label_Status_Rows")
        label_Status_Rows.set_text(str(len(model)) + " objects displayed")
        label_Status_Selected = self.builder.get_object("label_Status_Selected")
        label_Status_Selected.set_text(str(len(items)) + " rows selected")
        renamed = 0
        failed = 0
        if items:
            for item in items:  # items = selected rows
                if model[item][5] == "Renamed!":
                    renamed = renamed + 1
                elif model[item][5] == "New Name path already exists" or model[item][5] == "FAILED TO RENAME!" or model[item][5] == "Current Name's Full Path doesn't exist":
                    failed = failed + 1
        label_Status_Renamed = self.builder.get_object("label_Status_Renamed")
        label_Status_Renamed.set_text(str(renamed) + " objects successfully renamed")
        label_Status_Failed = self.builder.get_object("label_Status_Failed")
        label_Status_Failed.set_text(str(failed) + " objects failed to be renamed")
        if failed > 0:
            label_Status_Failed.get_style_context().add_class('red-blink-text')
        else:
            label_Status_Failed.get_style_context().remove_class('red-blink-text')

    def rename_files(self):  # This is the function that actually does the file renaming action
        global default_folder_path
        global rename_pairs
        # rename_pairs[0] = Current Name
        # rename_pairs[1] = New Name
        # rename_pairs[2] = Status
        # rename_pairs[3] = Full Path
        # rename_pairs[4] = Type
        folder_rename_pairs = []
        for loop in range(len(rename_pairs)):  # Loop through renaming the Files and making a list of the Folders
            if rename_pairs[loop][4] == "File":
                if rename_pairs[loop][3][-1:] == "/":  # Remove the final '/' from a folder, if it exists
                    temp = rename_pairs[loop][3][:-1]
                else:
                    temp = rename_pairs[loop][3]
                temp = temp.split('/')
                current_name_test = temp[len(temp) - 1]
                default_folder_path_temp = "/".join(temp[:len(temp) - 1]) + "/"
                if default_folder_path_temp[-1:] != "/":  # Add a final '/' to the default folder, if it doesn't exist
                    default_folder_path_temp = default_folder_path_temp[:-1]
                new_name_path = os.path.join(default_folder_path_temp, rename_pairs[loop][1])
                # Test and perform rename
                if os.path.exists(rename_pairs[loop][3]):  # Does the current file's full path still exist?
                    if os.path.exists(new_name_path):  # Does the new file's full path already exist?
                        rename_pairs[loop][2] = "New Name path already exists"
                    else:  # New file's full path doesn't exist, try to rename
                        try:  # Try to rename the file
                            os.rename(rename_pairs[loop][3], new_name_path)
                            rename_pairs[loop][2] = "Renamed!"
                        except Exception:  # Catch exception on file rename operation
                            rename_pairs[loop][2] = "FAILED TO RENAME!"
                else:  # Current file's full path doesn't exist
                    rename_pairs[loop][2] = "Current Name's Full Path doesn't exist"
            else:
                folder_rename_pairs.append(rename_pairs[loop])
        # Sort folder_rename_pairs do the longest path is first. This should guarantee that the subfolders are renamed before the parent folders.
        folder_rename_pairs.sort(key=lambda x: len(x[3]), reverse=True)  # Sort on full_path, longest path first
        # Loop through renaming folders
        for loop in range(len(folder_rename_pairs)):
            if folder_rename_pairs[loop][3][-1:] == "/":  # Remove the final '/' from a folder, if it exists
                temp = folder_rename_pairs[loop][3][:-1]
            else:
                temp = folder_rename_pairs[loop][3]
            temp = temp.split('/')
            current_name_test = temp[len(temp) - 1]
            default_folder_path_temp = "/".join(temp[:len(temp) - 1]) + "/"
            if default_folder_path_temp[-1:] != "/":  # Add a final '/' to the default folder, if it doesn't exist
                default_folder_path_temp = default_folder_path_temp[:-1]
            new_name_path = os.path.join(default_folder_path_temp, folder_rename_pairs[loop][1])
            # Test and perform rename
            if os.path.exists(folder_rename_pairs[loop][3]):  # Does the current file's full path still exist?
                if os.path.exists(new_name_path):  # Does the new file's full path already exist?
                    folder_rename_pairs[loop][2] = "New Name path already exists"
                else:  # New file's full path doesn't exist, try to rename
                    try:  # Try to rename the file
                        os.rename(folder_rename_pairs[loop][3], new_name_path)
                        folder_rename_pairs[loop][2] = "Renamed!"
                    except Exception:  # Catch exception on file rename operation
                        folder_rename_pairs[loop][2] = "FAILED TO RENAME!"
            else:  # Current file's full path doesn't exist
                folder_rename_pairs[loop][2] = "Current Name's Full Path doesn't exist"

    def save_history(self):  # This saves a pipe delimited list of "Type|Full Path|New Name|Status" to ~/.local/share/BSFEMA/
        checkbox_Save_History = self.builder.get_object("checkbox_Save_History")
        # Possibly add what settings were used to perform rename ?????
        if checkbox_Save_History.get_active() == True:
            full_path = os.path.expanduser("~/.local/share/BSFEMA/")
            current_time = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
            filename = str(current_time) + ".txt"
            file = open(os.path.join(full_path, filename), "w", encoding='utf-8-sig')
            for loop in range(len(rename_pairs)):
                # [type]|[full path]|[new name]|[status]
                file.write(str(rename_pairs[loop][4]) + "|" + str(rename_pairs[loop][3]) + "|" + str(rename_pairs[loop][1]) + "|" + str(rename_pairs[loop][2]) + "\n")
            file.close()

    def resize_column_widths(self):  # have the data grid columns automatically resize
        treeviewcolumn_Current_Name = self.builder.get_object("treeviewcolumn_Current_Name")
        treeviewcolumn_Current_Name.queue_resize()
        treeviewcolumn_New_Name = self.builder.get_object("treeviewcolumn_New_Name")
        treeviewcolumn_New_Name.queue_resize()
        treeviewcolumn_Sub_Directory = self.builder.get_object("treeviewcolumn_Sub_Directory")
        treeviewcolumn_Sub_Directory.queue_resize()
        treeviewcolumn_Size = self.builder.get_object("treeviewcolumn_Size")
        treeviewcolumn_Size.queue_resize()
        treeviewcolumn_Date_Modified = self.builder.get_object("treeviewcolumn_Date_Modified")
        treeviewcolumn_Date_Modified.queue_resize()
        treeviewcolumn_Status = self.builder.get_object("treeviewcolumn_Status")
        treeviewcolumn_Status.queue_resize()
        treeviewcolumn_Full_Path = self.builder.get_object("treeviewcolumn_Full_Path")
        treeviewcolumn_Full_Path.queue_resize()
        treeviewcolumn_Local_Path = self.builder.get_object("treeviewcolumn_Local_Path")
        treeviewcolumn_Local_Path.queue_resize()
        treeviewcolumn_Type = self.builder.get_object("treeviewcolumn_Type")
        treeviewcolumn_Type.queue_resize()
        treeviewcolumn_Hidden = self.builder.get_object("treeviewcolumn_Hidden")
        treeviewcolumn_Hidden.queue_resize()

    def treeview_Data_Grid_selection_changed(self, treeselection_object):  # For selected row create & display new name and status
        # Map between model[item][] and files_Full[]
        # model[item][0] = files_Full[4] = Current_Name
        # model[item][1] = files_Full[5] = New_Name
        # model[item][2] = files_Full[2] = Sub_Directory
        # model[item][3] = files_Full[6] = Size
        # model[item][4] = files_Full[7] = Date_Modified
        # model[item][5] = files_Full[9] = Status
        # model[item][6] = files_Full[0] = Full_Path
        # model[item][7] = files_Full[1] = Local_Path
        # model[item][8] = files_Full[3] = Type
        # model[item][9] = files_Full[8] = Hidden
        global directory_counts
        for data in directory_counts:
            directory_counts[data] = 0
        treeview_Data_Grid = self.builder.get_object("treeview_Data_Grid")
        selection = treeview_Data_Grid.get_selection()
        model, items = selection.get_selected_rows()
        # This  part clears out just the "New Name" and "Status" columns for the previously selected rows to save on performance
        global previous_selection
        if previous_selection[3]:  # This means that clear_Data_Grid was NOT called, so we need to refresh values based on previous_selection
            if previous_selection[2][-1:] == "/":
                previous_selection[2] = previous_selection[2][:-1]
            if default_folder_path[-1:] == "/":
                temp_default_folder_path = default_folder_path[:-1]
            else:
                temp_default_folder_path = default_folder_path
            if len(model) == previous_selection[1]:  # Do row totals match?
                if previous_selection[2] == temp_default_folder_path:  # Do previous path matches the default path?
                    for row in previous_selection[0]:
                        model[row][1] = ""  # Set the New Name to nothing
                        model[row][5] = ""  # Set the Status to nothing
                else:  # previous path doesn't match the default path
                    # This isn't needed since if the default path has changed the grid would be entirely new...
                    pass
            else:
                # This isn't needed since if the row totals don't match, the grid would be entirely new from a box_9 change...
                pass
            # This part builds the "New Name" and "Status" columns of the currently selected rows
            previous_selection[0].clear()  # Clear out current previously selected rows
            if items:
                for item in items:  # items = selected rows
                    # Columns to file_Full format conversion
                    row_data = [model[item][6], model[item][7], model[item][2], model[item][8], model[item][0], model[item][1], model[item][3], model[item][4], model[item][9], model[item][5]]
                    # Set the new name value to the calculated new name for the individual row
                    model[item][1] = self.update_row_in_data_grid_with_new_name(row_data)
                    if model[item][0] != model[item][1]:
                        model[item][5] = "To be changed"
                    else:
                        model[item][5] = "No change..."
                    previous_selection[0].append(item[0])  # Append currently selected row to list
            previous_selection[1] = len(model)  # Set the current number of rows
            previous_selection[2] = default_folder_path  # Set the current default_folder_path
        else:  # This means that clear_Data_Grid was called, so no need to refresh values
            # Do nothing since previous_selection[3] == False
            pass
        self.update_status_labels()

    def clear_Data_Grid(self):  # Clears out the data grid and global files lists
        global previous_selection
        previous_selection[3] = False  # Don't treeview_Data_Grid_selection_changed, this drastically helps with performance!
        # treeview_Data_Grid = Select None
        treeview_Data_Grid = self.builder.get_object("treeview_Data_Grid")
        selection = treeview_Data_Grid.get_selection()
        selection.unselect_all()
        # Do the rest of the original clear_Data_Grid bits
        liststore_Data_Grid = self.builder.get_object("liststore_Data_Grid")
        liststore_Data_Grid.clear()
        global files
        global files_Full
        files.clear()
        files_Full.clear()
        model, items = selection.get_selected_rows()
        previous_selection = [[], len(model), default_folder_path, True]  # Do treeview_Data_Grid_selection_changed, using default values

    def load_Data_Grid(self):  # Loads data grid with files list
        # Reset the directory_counts dictionary
        global directory_counts
        directory_counts.clear()
        directory_counts["/"] = 0
        # files_Full[0] = full path to file/folder
        # files_Full[1] = local path to file/folder
        # files_Full[2] = sub directory path
        # files_Full[3] = file/folder type
        # files_Full[4] = current file/folder name
        # files_Full[5] = new file/folder name
        # files_Full[6] = size
        # files_Full[7] = date modified
        # files_Full[8] = hidden
        # files_Full[9] = status
        liststore_Data_Grid = self.builder.get_object("liststore_Data_Grid")
        global files
        # Build files from files_Full
        for file in files_Full:
            # files.append([current, new, sub dir, size, modified, status, full_path, local_path, type, hidden])
            files.append([file[4],file[5],file[2],file[6],file[7],file[9],file[0],file[1],file[3],str(file[8])])
        # Build data grid from files
        for file in files:
            liststore_Data_Grid.append(file)
            # Keep a list of all the different sub directories
            directory_counts["/"] = 0  # There will always be a root level (default_folder_path)
            if file[2] != "" and file[2] != "/":
                if file[2] not in directory_counts:
                    directory_counts[file[2]] = 0

    def update_row_in_data_grid_with_new_name(self, row_data):  #  The main process by which box_1-8 are applied to the current name
        # row_data[0] = full path to file/folder
        # row_data[1] = local path to file/folder
        # row_data[2] = sub directory path
        # row_data[3] = file/folder type
        # row_data[4] = current file/folder name
        # row_data[5] = new file/folder name
        # row_data[6] = size
        # row_data[7] = date modified
        # row_data[8] = hidden
        # row_data[9] = status
        new_name = row_data[4]  # Set "new_name" to the "current name"
        # Check to see if Box_1-8 and rename_pairs_file have been modified, and it so, get the new_name modification from update_new_name_section_#
        if self.box_1:  # There is something changed and therefore needs to be run
            if row_data[3] == "File":  # This box applies only to Files, not Folders
                new_name = self.update_new_name_section_1(new_name, row_data)
        if self.box_2:  # There is something changed and therefore needs to be run
            new_name = self.update_new_name_section_2(new_name, row_data)
        if self.box_3:  # There is something changed and therefore needs to be run
            new_name = self.update_new_name_section_3(new_name, row_data)
        if self.box_4:  # There is something changed and therefore needs to be run
            new_name = self.update_new_name_section_4(new_name, row_data)
        if self.box_5:  # There is something changed and therefore needs to be run
            new_name = self.update_new_name_section_5(new_name, row_data)
        if self.box_6:  # There is something changed and therefore needs to be run
            new_name = self.update_new_name_section_6(new_name, row_data)
        if self.box_7:  # There is something changed and therefore needs to be run
            new_name = self.update_new_name_section_7(new_name, row_data)
        if self.box_8:  # There is something changed and therefore needs to be run
            if row_data[3] == "File":  # This box applies only to Files, not Folders
                new_name = self.update_new_name_section_8(new_name, row_data)
        if self.rename_pairs_file:  # There is something change and therefore needs to be run
            new_name = self.update_new_name_rename_pairs_file(new_name, row_data)
        return str(new_name)

    def update_new_name_section_1(self, new_name, row_data):  # 1. File Name
        combo_Name = self.builder.get_object("combo_Name")
        combo_Name_Entry = self.builder.get_object("combo_Name_Entry")
        entry_Name_Fixed = self.builder.get_object("entry_Name_Fixed")
        if len(new_name.split(".")) > 1:
            has_extension = True
        else:
            has_extension = False
        # Don't need to check:  combo_Name_Entry.get_text() == "Keep":
        if has_extension == True:  # File with extension
            filename_part = ".".join(new_name.split(".")[:-1])
            extension_part = new_name.split(".")[-1]
            if combo_Name_Entry.get_text() == "Remove":
                filename_part = ""
            elif  combo_Name_Entry.get_text() == "Fixed":
                filename_part = entry_Name_Fixed.get_text()
            new_name = str(filename_part) + "." + str(extension_part)
        else:  # File with no extension
            # Can't "Remove", only "Fixed"
            if combo_Name_Entry.get_text() == "Fixed":
                new_name = entry_Name_Fixed.get_text()
        return new_name

    def update_new_name_section_2(self, new_name, row_data):  # 2. Replace
        entry_Replace_Search = self.builder.get_object("entry_Replace_Search")
        checkbox_Replace_Case = self.builder.get_object("checkbox_Replace_Case")
        entry_Replace_With = self.builder.get_object("entry_Replace_With")
        search_text = entry_Replace_Search.get_text()
        with_text = entry_Replace_With.get_text()
        if len(new_name.split(".")) > 1:
            has_extension = True
        else:
            has_extension = False
        if row_data[3] == "File" and has_extension == True:
            filename_part = ".".join(new_name.split(".")[:-1])
            extension_part = new_name.split(".")[-1]
            if search_text != "":
                if checkbox_Replace_Case.get_active() == True:  # Case snesitive
                    filename_part = str(filename_part).replace(search_text, with_text)
                else:  # Case Insensitive
                    filename_part = re.sub(re.escape(search_text), with_text, str(filename_part), flags=re.IGNORECASE)
                new_name = str(filename_part) + "." + str(extension_part)
        else:  # Folders and Files with no extensions
            if search_text != "":
                if checkbox_Replace_Case.get_active() == True:  # Case snesitive
                    new_name = str(new_name).replace(search_text, with_text)
                else:  # Case Insensitive
                    new_name = re.sub(re.escape(search_text), with_text, str(new_name), flags=re.IGNORECASE)
        return new_name

    def update_new_name_section_3(self, new_name, row_data):  # 3. Case
        combo_Case = self.builder.get_object("combo_Case")
        combo_Case_Entry = self.builder.get_object("combo_Case_Entry")
        if len(new_name.split(".")) > 1:
            has_extension = True
        else:
            has_extension = False
        # don't need to check:  combo_Case_Entry.get_text() == "Same":
        if row_data[3] == "File" and has_extension == True:
            filename_part = ".".join(new_name.split(".")[:-1])
            extension_part = new_name.split(".")[-1]
            if combo_Case_Entry.get_text() == "Upper":
                filename_part = filename_part.upper()
            elif combo_Case_Entry.get_text() == "Lower":
                filename_part = filename_part.lower()
            elif combo_Case_Entry.get_text() == "Title":
                filename_part = filename_part.title()
            elif combo_Case_Entry.get_text() == "Sentence":
                filename_part = filename_part.lower()
                filename_part = filename_part[:1].upper() + filename_part[1:]
            new_name = str(filename_part) + "." + str(extension_part)
        else:  # Folders and Files with no extensions
            if combo_Case_Entry.get_text() == "Upper":
                new_name = new_name.upper()
            elif combo_Case_Entry.get_text() == "Lower":
                new_name = new_name.lower()
            elif combo_Case_Entry.get_text() == "Title":
                new_name = new_name.title()
            elif combo_Case_Entry.get_text() == "Sentence":
                new_name = new_name.lower()
                new_name = new_name[:1].upper() + new_name[1:]
        return new_name

    def update_new_name_section_4(self, new_name, row_data):  # 4. Remove
        spin_Remove_First = self.builder.get_object("spin_Remove_First")
        spin_Remove_Last = self.builder.get_object("spin_Remove_Last")
        spin_Remove_From = self.builder.get_object("spin_Remove_From")
        spin_Remove_To = self.builder.get_object("spin_Remove_To")
        combo_Remove_Crop = self.builder.get_object("combo_Remove_Crop")
        combo_Remove_Crop_Entry = self.builder.get_object("combo_Remove_Crop_Entry")
        entry_Remove_Crop = self.builder.get_object("entry_Remove_Crop")
        Remove_First = int(spin_Remove_First.get_value())
        Remove_Last = int(spin_Remove_Last.get_value())
        Remove_From = int(spin_Remove_From.get_value())
        Remove_To = int(spin_Remove_To.get_value())
        Remove_Crop = combo_Remove_Crop_Entry.get_text()
        Crop = entry_Remove_Crop.get_text()
        if len(new_name.split(".")) > 1:
            has_extension = True
        else:
            has_extension = False
        if row_data[3] == "File" and has_extension == True:
            filename_part = ".".join(new_name.split(".")[:-1])
            extension_part = new_name.split(".")[-1]
            if Remove_First > 0:
                filename_part = filename_part[Remove_First:]
            if Remove_Last > 0:
                filename_part = filename_part[:-Remove_Last]
            if Remove_From > 0:
                if Remove_To >= Remove_From:
                    if len(filename_part) >= Remove_From:
                        filename_part = filename_part[:Remove_From - 1] + filename_part[Remove_To:]
                    else:
                        filename_part = filename_part[:Remove_From]
            if Remove_Crop != "None":
                temp_crop = filename_part.split(Crop)
                if Remove_Crop == "Before First":
                    if len(temp_crop) > 1:  # Meaning that 'crop' was found in filename_part
                        filename_part = str(Crop) + Crop.join(temp_crop[0 - (len(temp_crop) - 1):])
                if Remove_Crop == "Before Last":
                    if len(temp_crop) > 1:  # Meaning that 'crop' was found in filename_part
                        filename_part = str(Crop) + temp_crop[len(temp_crop) - 1]
                if Remove_Crop == "After First":
                    if len(temp_crop) > 1:  # Meaning that 'crop' was found in filename_part
                        filename_part = temp_crop[0] + str(Crop)
                if Remove_Crop == "After Last":
                    if len(temp_crop) > 1:  # Meaning that 'crop' was found in filename_part
                        filename_part = str(Crop.join(temp_crop[:len(temp_crop) - 1])) + str(Crop)
            new_name = str(filename_part) + "." + str(extension_part)
        else:  # Folders and Files with no extensions
            if Remove_First > 0:
                new_name = new_name[Remove_First:]
            if Remove_Last > 0:
                new_name = new_name[:-Remove_Last]
            if Remove_From > 0:
                if Remove_To >= Remove_From:
                    if len(new_name) >= Remove_From:
                        new_name = new_name[:Remove_From - 1] + new_name[Remove_To:]
                    else:
                        new_name = new_name[:Remove_From]
            if Remove_Crop != "None":
                temp_crop = new_name.split(Crop)
                if Remove_Crop == "Before First":
                    if len(temp_crop) > 1:  # Meaning that 'crop' was found in new_name
                        new_name = str(Crop) + Crop.join(temp_crop[0 - (len(temp_crop) - 1):])
                if Remove_Crop == "Before Last":
                    if len(temp_crop) > 1:  # Meaning that 'crop' was found in new_name
                        new_name = str(Crop) + temp_crop[len(temp_crop) - 1]
                if Remove_Crop == "After First":
                    if len(temp_crop) > 1:  # Meaning that 'crop' was found in new_name
                        new_name = temp_crop[0] + str(Crop)
                if Remove_Crop == "After Last":
                    if len(temp_crop) > 1:  # Meaning that 'crop' was found in new_name
                        new_name = str(Crop.join(temp_crop[:len(temp_crop) - 1])) + str(Crop)
        return new_name

    def update_new_name_section_5(self, new_name, row_data):  # 5. Add
        entry_Add_Prefix = self.builder.get_object("entry_Add_Prefix")
        entry_Add_Suffix = self.builder.get_object("entry_Add_Suffix")
        entry_Add_Insert = self.builder.get_object("entry_Add_Insert")
        spin_Add_Insert = self.builder.get_object("spin_Add_Insert")
        Add_Prefix = entry_Add_Prefix.get_text()
        Add_Suffix = entry_Add_Suffix.get_text()
        Add_Insert = entry_Add_Insert.get_text()
        Add_Insert_At = int(spin_Add_Insert.get_value())
        if len(new_name.split(".")) > 1:
            has_extension = True
        else:
            has_extension = False
        if row_data[3] == "File" and has_extension == True:
            filename_part = ".".join(new_name.split(".")[:-1])
            extension_part = new_name.split(".")[-1]
            if len(Add_Prefix) > 0:
                filename_part = Add_Prefix + filename_part
            if len(Add_Suffix) > 0:
                filename_part = filename_part + Add_Suffix
            if len(Add_Insert) > 0 and Add_Insert_At > 0:  # Insert before the Add_Insert_At value, so Add_Insert_At=1 puts it at the beginning of the string
                if Add_Insert_At > len(filename_part):
                    filename_part = filename_part + Add_Insert
                elif Add_Insert_At == 1:
                    filename_part = Add_Insert + filename_part
                else:
                    filename_part = filename_part[:(Add_Insert_At - 1)] + Add_Insert + filename_part[(Add_Insert_At - 1):]
            elif len(Add_Insert) > 0 and Add_Insert_At < 0:
                filename_part = filename_part[:(Add_Insert_At)] + Add_Insert + filename_part[(Add_Insert_At):]
            new_name = str(filename_part) + "." + str(extension_part)
        else:  # Folders and Files with no extensions
            if len(Add_Prefix) > 0:
                new_name = Add_Prefix + new_name
            if len(Add_Suffix) > 0:
                new_name = new_name + Add_Suffix
            if len(Add_Insert) > 0 and Add_Insert_At > 0:  # Insert before the Add_Insert_At value, so Add_Insert_At=1 puts it at the beginning of the string
                if Add_Insert_At > len(new_name):
                    new_name = new_name + Add_Insert
                elif Add_Insert_At == 1:
                    new_name = Add_Insert + new_name
                else:
                    new_name = new_name[:(Add_Insert_At - 1)] + Add_Insert + new_name[(Add_Insert_At - 1):]
            elif  len(Add_Insert) > 0 and Add_Insert_At < 0:
                new_name = new_name[:(Add_Insert_At)] + Add_Insert + new_name[(Add_Insert_At):]
        return new_name

    def update_new_name_section_6(self, new_name, row_data):  # 6. Append
        combo_Append_Folder_Name = self.builder.get_object("combo_Append_Folder_Name")
        combo_Append_Folder_Name_Entry = self.builder.get_object("combo_Append_Folder_Name_Entry")
        entry_Append_Folder_Name_Separator = self.builder.get_object("entry_Append_Folder_Name_Separator")
        separator = entry_Append_Folder_Name_Separator.get_text()
        local_folder_name = ""
        # Get folder name
        # If there isn't a sub directory, get local part of default_folder_path
        # If there is a sub directory, get local part of that sub directory
        if row_data[2] == "" or row_data[2] == "/":
            local_folder_name = str(os.path.basename(os.path.normpath(default_folder_path)))
        else:
            local_folder_name = str(os.path.basename(os.path.normpath(row_data[2])))
        if len(new_name.split(".")) > 1:
            has_extension = True
        else:
            has_extension = False
        if row_data[3] == "File" and has_extension == True:
            filename_part = ".".join(new_name.split(".")[:-1])
            extension_part = new_name.split(".")[-1]
            if combo_Append_Folder_Name_Entry.get_text() == "Prefix":
                filename_part = local_folder_name + separator + filename_part
            elif combo_Append_Folder_Name_Entry.get_text() == "Suffix":
                filename_part = filename_part + separator + local_folder_name
            new_name = str(filename_part) + "." + str(extension_part)
        else:  # Folders and Files with no extensions
            if combo_Append_Folder_Name_Entry.get_text() == "Prefix":
                new_name = local_folder_name + separator + new_name
            elif combo_Append_Folder_Name_Entry.get_text() == "Suffix":
                new_name = new_name + separator + local_folder_name
        return new_name

    def update_new_name_section_7(self, new_name, row_data):  # 7. Numbering
        combo_Numbering = self.builder.get_object("combo_Numbering")
        combo_Numbering_Entry = self.builder.get_object("combo_Numbering_Entry")
        spin_Numbering_At = self.builder.get_object("spin_Numbering_At")
        spin_Numbering_Increment = self.builder.get_object("spin_Numbering_Increment")
        spin_Numbering_Padding = self.builder.get_object("spin_Numbering_Padding")
        spin_Numbering_Start = self.builder.get_object("spin_Numbering_Start")
        checkbox_Numbering_Per_Folder = self.builder.get_object("checkbox_Numbering_Per_Folder")
        entry_Numbering_Separator = self.builder.get_object("entry_Numbering_Separator")
        Numbering_Entry = combo_Numbering_Entry.get_text()
        Numbering_At = int(spin_Numbering_At.get_value())
        Numbering_Increment = int(spin_Numbering_Increment.get_value())
        Numbering_Padding = int(spin_Numbering_Padding.get_value())
        Numbering_Start = int(spin_Numbering_Start.get_value())
        Numbering_Per_Folder = checkbox_Numbering_Per_Folder.get_active()  # Boolean
        Numbering_Separator = entry_Numbering_Separator.get_text()
        global directory_counts
        # Logic
        if Numbering_Per_Folder:
            if len(new_name.split(".")) > 1:
                has_extension = True
            else:
                has_extension = False
            if row_data[3] == "File" and has_extension == True:
                filename_part = ".".join(new_name.split(".")[:-1])
                extension_part = new_name.split(".")[-1]
                # We can ignore Numbering_Entry == "None"":
                if Numbering_Entry == "Prefix":
                    padded_number = return_padded_number_for_per_folder_option(row_data[2], Numbering_Start, Numbering_Increment, Numbering_Padding)
                    filename_part = padded_number + Numbering_Separator + filename_part
                elif Numbering_Entry == "Suffix":
                    padded_number = return_padded_number_for_per_folder_option(row_data[2], Numbering_Start, Numbering_Increment, Numbering_Padding)
                    filename_part = filename_part + Numbering_Separator + padded_number
                elif Numbering_Entry == "Insert":  # Insert before the Numbering_Increment value, so Numbering_Increment=1 puts it after the first character in the string %#%%%%
                    if Numbering_At > 0:  # Otherwise it would be a Prefix
                        if Numbering_At <= len(filename_part):
                            padded_number = return_padded_number_for_per_folder_option(row_data[2], Numbering_Start, Numbering_Increment, Numbering_Padding)
                            filename_part = filename_part[:Numbering_At] + Numbering_Separator + padded_number + Numbering_Separator + filename_part[Numbering_At:]
                        elif  Numbering_At > len(filename_part):  # Same as Suffix
                            padded_number = return_padded_number_for_per_folder_option(row_data[2], Numbering_Start, Numbering_Increment, Numbering_Padding)
                            filename_part = filename_part + Numbering_Separator + padded_number
                    else:  # Same as prefix
                        padded_number = return_padded_number_for_per_folder_option(row_data[2], Numbering_Start, Numbering_Increment, Numbering_Padding)
                        filename_part = padded_number + Numbering_Separator + filename_part
                new_name = str(filename_part) + "." + str(extension_part)
            else:  # Folders and Files with no extensions
                if Numbering_Entry == "Prefix":
                    padded_number = return_padded_number_for_per_folder_option(row_data[2], Numbering_Start, Numbering_Increment, Numbering_Padding)
                    new_name = padded_number + Numbering_Separator + new_name
                elif Numbering_Entry == "Suffix":
                    padded_number = return_padded_number_for_per_folder_option(row_data[2], Numbering_Start, Numbering_Increment, Numbering_Padding)
                    new_name = new_name + Numbering_Separator + padded_number
                elif Numbering_Entry == "Insert":
                    if Numbering_At > 0:  # Otherwise it would be a Prefix
                        if Numbering_At <= len(new_name):
                            padded_number = return_padded_number_for_per_folder_option(row_data[2], Numbering_Start, Numbering_Increment, Numbering_Padding)
                            new_name = new_name[:Numbering_At] + Numbering_Separator + padded_number + Numbering_Separator + new_name[Numbering_At:]
                        elif  Numbering_At > len(new_name):  # Same as Suffix
                            padded_number = return_padded_number_for_per_folder_option(row_data[2], Numbering_Start, Numbering_Increment, Numbering_Padding)
                            new_name = new_name + Numbering_Separator + padded_number
                    else:  # Same as Prefix
                        padded_number = return_padded_number_for_per_folder_option(row_data[2], Numbering_Start, Numbering_Increment, Numbering_Padding)
                        new_name = padded_number + Numbering_Separator + new_name
        else:  # Use directory_counts["/"] for everything
            padded_number = str(Numbering_Start + (directory_counts["/"] * Numbering_Increment)).rjust(Numbering_Padding, '0')
            # Increment the directory_counts["/"] global
            directory_counts["/"] = directory_counts["/"] + 1
            if len(new_name.split(".")) > 1:
                has_extension = True
            else:
                has_extension = False
            if row_data[3] == "File" and has_extension == True:
                filename_part = ".".join(new_name.split(".")[:-1])
                extension_part = new_name.split(".")[-1]
                # We can ignore Numbering_Entry == "None"":
                if Numbering_Entry == "Prefix":
                    filename_part = padded_number + Numbering_Separator + filename_part
                elif Numbering_Entry == "Suffix":
                    filename_part = filename_part + Numbering_Separator + padded_number
                elif Numbering_Entry == "Insert":  # Insert before the Numbering_Increment value, so Numbering_Increment=1 puts it after the first character in the string %#%%%%
                    if Numbering_At > 0:  # Otherwise it would be a Prefix
                        if Numbering_At <= len(filename_part):
                            filename_part = filename_part[:Numbering_At] + Numbering_Separator + padded_number + Numbering_Separator + filename_part[Numbering_At:]
                        elif  Numbering_At > len(filename_part):  # Same as Suffix
                            filename_part = filename_part + Numbering_Separator + padded_number
                new_name = str(filename_part) + "." + str(extension_part)
            else:  # Folders and Files with no extensions
                if Numbering_Entry == "Prefix":
                    new_name = padded_number + Numbering_Separator + new_name
                elif Numbering_Entry == "Suffix":
                    new_name = new_name + Numbering_Separator + padded_number
                elif Numbering_Entry == "Insert":
                    if Numbering_At > 0:  # Otherwise it would be a Prefix
                        if Numbering_At <= len(new_name):
                            new_name = new_name[:Numbering_At] + Numbering_Separator + padded_number + Numbering_Separator + new_name[Numbering_At:]
                        elif  Numbering_At > len(new_name):  # Same as Suffix
                            new_name = new_name + Numbering_Separator + padded_number
        return new_name

    def update_new_name_section_8(self, new_name, row_data):  # 8. Extension
        combo_Extension = self.builder.get_object("combo_Extension")
        combo_Extension_entry = self.builder.get_object("combo_Extension_entry")
        entry_Extension = self.builder.get_object("entry_Extension")
        if len(new_name.split(".")) > 1:
            # has_extension = True
            filename_part = ".".join(new_name.split(".")[:-1])
            extension_part = new_name.split(".")[-1]
            # Can ignore "Same"
            if combo_Extension_entry.get_text() == "Upper":
                new_name = str(filename_part) + "." + str(extension_part).upper()
            elif combo_Extension_entry.get_text() == "Lower":
                new_name = str(filename_part) + "." + str(extension_part).lower()
            elif combo_Extension_entry.get_text() == "Fixed":
                new_name = str(filename_part) + "." + entry_Extension.get_text()
            elif combo_Extension_entry.get_text() == "Extra":
                new_name = str(filename_part) + "." + str(extension_part) + "." + entry_Extension.get_text()
            elif combo_Extension_entry.get_text() == "Remove":
                new_name = str(filename_part)
        return new_name

    def update_new_name_rename_pairs_file(self, new_name, row_data):  # Rename Pair file
        if new_name in rename_pairs_from_file:  # Is the current "new_name" in the rename_pairs_from_file dictionary?
            return rename_pairs_from_file[new_name]  # Yes: return the rename pair
        else:
            return new_name  # No: return the original "new_name"

    def check_settings_for_box_1(self):  # Checking to see if there are any changes to a widget in this box
        combo_Name = self.builder.get_object("combo_Name")
        combo_Name_Entry = self.builder.get_object("combo_Name_Entry")
        entry_Name_Fixed = self.builder.get_object("entry_Name_Fixed")
        box_Name = self.builder.get_object("box_Name")
        if (combo_Name_Entry.get_text() == "Fixed" and entry_Name_Fixed.get_text() != "") or (combo_Name_Entry.get_text() == "Remove"):
            self.box_1 = True
            box_Name.get_style_context().remove_class('no-border')
            box_Name.get_style_context().add_class('red-border')
        else:
            self.box_1 = False
            box_Name.get_style_context().remove_class('red-border')
            box_Name.get_style_context().add_class('no-border')

    def check_settings_for_box_2(self):  # Checking to see if there are any changes to a widget in this box
        entry_Replace_Search = self.builder.get_object("entry_Replace_Search")
        entry_Replace_With = self.builder.get_object("entry_Replace_With")
        box_Replace = self.builder.get_object("box_Replace")
        if entry_Replace_Search.get_text() != "":
            self.box_2 = True
            box_Replace.get_style_context().remove_class('no-border')
            box_Replace.get_style_context().add_class('red-border')
        else:
            self.box_2 = False
            box_Replace.get_style_context().remove_class('red-border')
            box_Replace.get_style_context().add_class('no-border')

    def check_settings_for_box_3(self):  # Checking to see if there are any changes to a widget in this box
        combo_Case = self.builder.get_object("combo_Case")
        combo_Case_Entry = self.builder.get_object("combo_Case_Entry")
        box_Case = self.builder.get_object("box_Case")
        if combo_Case_Entry.get_text() != "Same":
            self.box_3 = True
            box_Case.get_style_context().remove_class('no-border')
            box_Case.get_style_context().add_class('red-border')
        else:
            self.box_3 = False
            box_Case.get_style_context().remove_class('red-border')
            box_Case.get_style_context().add_class('no-border')

    def check_settings_for_box_4(self):  # Checking to see if there are any changes to a widget in this box
        spin_Remove_First = self.builder.get_object("spin_Remove_First")
        spin_Remove_Last = self.builder.get_object("spin_Remove_Last")
        spin_Remove_From = self.builder.get_object("spin_Remove_From")
        spin_Remove_To = self.builder.get_object("spin_Remove_To")
        box_Remove = self.builder.get_object("box_Remove")
        combo_Remove_Crop = self.builder.get_object("combo_Remove_Crop")
        combo_Remove_Crop_Entry = self.builder.get_object("combo_Remove_Crop_Entry")
        entry_Remove_Crop = self.builder.get_object("entry_Remove_Crop")
        self.box_4 = False
        if int(spin_Remove_First.get_value()) != 0:
            self.box_4 = True
        if int(spin_Remove_Last.get_value()) != 0:
            self.box_4 = True
        if (int(spin_Remove_From.get_value()) != 0) and (int(spin_Remove_To.get_value()) >= int(spin_Remove_From.get_value())):
            self.box_4 = True
        # Can ignore "None"
        if combo_Remove_Crop_Entry.get_text() == "Before First" and entry_Remove_Crop.get_text() != "":
            self.box_4 = True
        if combo_Remove_Crop_Entry.get_text() == "Before Last" and entry_Remove_Crop.get_text() != "":
            self.box_4 = True
        if combo_Remove_Crop_Entry.get_text() == "After First" and entry_Remove_Crop.get_text() != "":
            self.box_4 = True
        if combo_Remove_Crop_Entry.get_text() == "After Last" and entry_Remove_Crop.get_text() != "":
            self.box_4 = True
        if self.box_4:
            box_Remove.get_style_context().remove_class('no-border')
            box_Remove.get_style_context().add_class('red-border')
        else:
            box_Remove.get_style_context().remove_class('red-border')
            box_Remove.get_style_context().add_class('no-border')

    def check_settings_for_box_5(self):  # Checking to see if there are any changes to a widget in this box
        entry_Add_Prefix = self.builder.get_object("entry_Add_Prefix")
        entry_Add_Suffix = self.builder.get_object("entry_Add_Suffix")
        entry_Add_Insert = self.builder.get_object("entry_Add_Insert")
        box_Add = self.builder.get_object("box_Add")
        self.box_5 = False
        if entry_Add_Prefix.get_text() != "":
            self.box_5 = True
        if entry_Add_Suffix.get_text() != "":
            self.box_5 = True
        if (entry_Add_Insert.get_text() != ""):
            self.box_5 = True
        if self.box_5:
            box_Add.get_style_context().remove_class('no-border')
            box_Add.get_style_context().add_class('red-border')
        else:
            box_Add.get_style_context().remove_class('red-border')
            box_Add.get_style_context().add_class('no-border')

    def check_settings_for_box_6(self):  # Checking to see if there are any changes to a widget in this box
        combo_Append_Folder_Name = self.builder.get_object("combo_Append_Folder_Name")
        combo_Append_Folder_Name_Entry = self.builder.get_object("combo_Append_Folder_Name_Entry")
        entry_Append_Folder_Name_Separator = self.builder.get_object("entry_Append_Folder_Name_Separator")
        box_Append = self.builder.get_object("box_Append")
        if combo_Append_Folder_Name_Entry.get_text() != "None":
            self.box_6 = True
            box_Append.get_style_context().remove_class('no-border')
            box_Append.get_style_context().add_class('red-border')
        else:
            self.box_6 = False
            box_Append.get_style_context().remove_class('red-border')
            box_Append.get_style_context().add_class('no-border')

    def check_settings_for_box_7(self):  # Checking to see if there are any changes to a widget in this box
        combo_Numbering = self.builder.get_object("combo_Numbering")
        combo_Numbering_Entry = self.builder.get_object("combo_Numbering_Entry")
        spin_Numbering_At = self.builder.get_object("spin_Numbering_At")
        spin_Numbering_Increment = self.builder.get_object("spin_Numbering_Increment")
        spin_Numbering_Padding = self.builder.get_object("spin_Numbering_Padding")
        spin_Numbering_Start = self.builder.get_object("spin_Numbering_Start")
        checkbox_Numbering_Per_Folder = self.builder.get_object("checkbox_Numbering_Per_Folder")
        entry_Numbering_Separator = self.builder.get_object("entry_Numbering_Separator")
        box_Numbering = self.builder.get_object("box_Numbering")
        if combo_Numbering_Entry.get_text() != "None":
            self.box_7 = True
            box_Numbering.get_style_context().remove_class('no-border')
            box_Numbering.get_style_context().add_class('red-border')
        else:
            self.box_7 = False
            box_Numbering.get_style_context().remove_class('red-border')
            box_Numbering.get_style_context().add_class('no-border')

    def check_settings_for_box_8(self):  # Checking to see if there are any changes to a widget in this box
        combo_Extension = self.builder.get_object("combo_Extension")
        combo_Extension_entry = self.builder.get_object("combo_Extension_entry")
        entry_Extension = self.builder.get_object("entry_Extension")
        box_Extension = self.builder.get_object("box_Extension")
        self.box_8 = False
        # Can ignore "Same"
        if combo_Extension_entry.get_text() == "Upper":
            self.box_8 = True
        if combo_Extension_entry.get_text() == "Lower":
            self.box_8 = True
        if combo_Extension_entry.get_text() == "Fixed" and entry_Extension.get_text() != "":
            self.box_8 = True
        if combo_Extension_entry.get_text() == "Extra" and entry_Extension.get_text() != "":
            self.box_8 = True
        if combo_Extension_entry.get_text() == "Remove":
            self.box_8 = True
        if self.box_8:
            box_Extension.get_style_context().remove_class('no-border')
            box_Extension.get_style_context().add_class('red-border')
        else:
            box_Extension.get_style_context().remove_class('red-border')
            box_Extension.get_style_context().add_class('no-border')

    def handy_list_of_all_settings(self):  # Note:  This isn't used anywhere, but it's useful to have a list of...
        # Various GtkBox:
        box_Main = self.builder.get_object("box_Main")
        box_Folder_Selecter = self.builder.get_object("box_Folder_Selecter")
        box_Options_and_Buttons = self.builder.get_object("box_Options_and_Buttons")
        box_Options = self.builder.get_object("box_Options")
        box_Name = self.builder.get_object("box_Name")
        box_Replace = self.builder.get_object("box_Replace")
        box_Case = self.builder.get_object("box_Case")
        box_Remove = self.builder.get_object("box_Remove")
        box_Add = self.builder.get_object("box_Add")
        box_Append = self.builder.get_object("box_Append")
        box_Numbering = self.builder.get_object("box_Numbering")
        box_Extension = self.builder.get_object("box_Extension")
        box_Files = self.builder.get_object("box_Files")
        box_Status = self.builder.get_object("box_Status")
        box_Buttons = self.builder.get_object("box_Buttons")
        # box 1
        combo_Name = self.builder.get_object("combo_Name")
        combo_Name_Entry = self.builder.get_object("combo_Name_Entry")
        entry_Name_Fixed = self.builder.get_object("entry_Name_Fixed")
        # box 2
        entry_Replace_Search = self.builder.get_object("entry_Replace_Search")
        checkbox_Replace_Case = self.builder.get_object("checkbox_Replace_Case")
        entry_Replace_With = self.builder.get_object("entry_Replace_With")
        # box 3
        combo_Case = self.builder.get_object("combo_Case")
        combo_Case_Entry = self.builder.get_object("combo_Case_Entry")
        # box 4
        spin_Remove_First = self.builder.get_object("spin_Remove_First")
        spin_Remove_Last = self.builder.get_object("spin_Remove_Last")
        spin_Remove_From = self.builder.get_object("spin_Remove_From")
        spin_Remove_To = self.builder.get_object("spin_Remove_To")
        combo_Remove_Crop = self.builder.get_object("combo_Remove_Crop")
        combo_Remove_Crop_Entry = self.builder.get_object("combo_Remove_Crop_Entry")
        entry_Remove_Crop = self.builder.get_object("entry_Remove_Crop")
        # box 5
        entry_Add_Insert = self.builder.get_object("entry_Add_Insert")
        entry_Add_Suffix = self.builder.get_object("entry_Add_Suffix")
        entry_Add_Prefix = self.builder.get_object("entry_Add_Prefix")
        spin_Add_Insert = self.builder.get_object("spin_Add_Insert")
        # box 6
        combo_Append_Folder_Name = self.builder.get_object("combo_Append_Folder_Name")
        combo_Append_Folder_Name_Entry = self.builder.get_object("combo_Append_Folder_Name_Entry")
        entry_Append_Folder_Name_Separator = self.builder.get_object("entry_Append_Folder_Name_Separator")
        # box 7
        combo_Numbering = self.builder.get_object("combo_Numbering")
        combo_Numbering_Entry = self.builder.get_object("combo_Numbering_Entry")
        spin_Numbering_At = self.builder.get_object("spin_Numbering_At")
        spin_Numbering_Increment = self.builder.get_object("spin_Numbering_Increment")
        spin_Numbering_Padding = self.builder.get_object("spin_Numbering_Padding")
        spin_Numbering_Start = self.builder.get_object("spin_Numbering_Start")
        checkbox_Numbering_Per_Folder = self.builder.get_object("checkbox_Numbering_Per_Folder")
        entry_Numbering_Separator = self.builder.get_object("entry_Numbering_Separator")
        # box 8
        combo_Extension = self.builder.get_object("combo_Extension")
        combo_Extension_entry = self.builder.get_object("combo_Extension_entry")
        entry_Extension = self.builder.get_object("entry_Extension")
        # box 9
        entry_Mask = self.builder.get_object("entry_Mask")
        checkbox_Folders = self.builder.get_object("checkbox_Folders")
        checkbox_Subfolders = self.builder.get_object("checkbox_Subfolders")
        checkbox_Files = self.builder.get_object("checkbox_Files")
        checkbox_Hidden = self.builder.get_object("checkbox_Hidden")
        spin_File_Name_Min = self.builder.get_object("spin_File_Name_Min")
        spin_File_Name_Max = self.builder.get_object("spin_File_Name_Max")
        # Folder Chooser
        entry_Extension = self.builder.get_object("entry_Extension")
        filechooser_Folder_Selecter = self.builder.get_object("filechooser_Folder_Selecter")
        entry_Folder_path = self.builder.get_object("entry_Folder_path")
        # Buttons
        button_Refresh = self.builder.get_object("button_Refresh")
        button_Refresh_Reselect = self.builder.get_object("button_Refresh_Reselect")
        button_Reset = self.builder.get_object("button_Reset")
        button_Rename_Pairs = self.builder.get_object("button_Rename_Pairs")
        button_Rename = self.builder.get_object("button_Rename")
        checkbox_Save_History = self.builder.get_object("checkbox_Save_History")
        button_Open_Settings = self.builder.get_object("button_Open_Settings")
        button_Save_Settings = self.builder.get_object("button_Save_Settings")
        button_SaveAs_Settings = self.builder.get_object("button_SaveAs_Settings")
        button_About = self.builder.get_object("button_About")
        # Data Grid
        treeview_Data_Grid = self.builder.get_object("treeview_Data_Grid")
        treeviewcolumn_Current_Name = self.builder.get_object("treeviewcolumn_Current_Name")
        treeviewcolumn_New_Name = self.builder.get_object("treeviewcolumn_New_Name")
        treeviewcolumn_Sub_Directory = self.builder.get_object("treeviewcolumn_Sub_Directory")
        treeviewcolumn_Size = self.builder.get_object("treeviewcolumn_Size")
        treeviewcolumn_Date_Modified = self.builder.get_object("treeviewcolumn_Date_Modified")
        treeviewcolumn_Status = self.builder.get_object("treeviewcolumn_Status")
        treeviewcolumn_Full_Path = self.builder.get_object("treeviewcolumn_Full_Path")
        treeviewcolumn_Local_Path = self.builder.get_object("treeviewcolumn_Local_Path")
        treeviewcolumn_Type = self.builder.get_object("treeviewcolumn_Type")
        treeviewcolumn_Hidden = self.builder.get_object("treeviewcolumn_Hidden")
        # Status Labels
        label_Status_Rows = self.builder.get_object("label_Status_Rows")
        label_Status_Selected = self.builder.get_object("label_Status_Selected")
        label_Status_Renamed = self.builder.get_object("label_Status_Renamed")
        label_Status_Failed = self.builder.get_object("label_Status_Failed")


""" **************************************************************************************************************** """
# "class Main()" ends here...
# Beyond here lay functions...
""" **************************************************************************************************************** """


def get_list_of_files_and_subdirs():  # Gets the list of all files and folder from the default_folder_path
    all_paths = []
    for path, subdirs, files in os.walk(default_folder_path, topdown=False):
        for name in files:
            temp_name = str(os.path.join(path, name)).replace(default_folder_path + '/', '')
            all_paths.append(temp_name)
        for name in subdirs:
            temp_name = str(os.path.join(path, name)).replace(default_folder_path + '/', '')
            all_paths.append(temp_name + '/')
    return all_paths


def populate_files_Full(entry_Mask, checkbox_Folders, checkbox_Subfolders, checkbox_Files, checkbox_Hidden, spin_File_Name_Min, spin_File_Name_Max):
    # This populates the files_Full list with all file/folder information, which is the basis of the data grid
    global files_Full
    # files_Full[0] = full path to file/folder
    # files_Full[1] = local path to file/folder
    # files_Full[2] = sub directory path
    # files_Full[3] = file/folder type
    # files_Full[4] = current file/folder name
    # files_Full[5] = new file/folder name
    # files_Full[6] = size
    # files_Full[7] = date modified
    # files_Full[8] = hidden
    # files_Full[9] = status
    files_unsorted = []  # Unsorted list of files before we sort and put them in files_Full
    files_temp = []
    files_temp = get_list_of_files_and_subdirs()
    for file in files_temp:
        # initialize all part# variables
        part0 = part1 = part2 = part3 = part4 = part5 = part6 = part7 = part8 = part9 = ''
        part0 = default_folder_path + '/' + file
        part1 = file
        # part3 comes before part2 because part2 needs to know if it's type
        if file[-1:] == '/':
            part3 = 'Folder'
        else:
            part3 = 'File'
        # now is part2 and part4 semi-combined
        if ('/' in file) and (part3 == 'File'):
            part2 = file.split('/')
            part4 = part2[len(part2)-1]
            part2 = "/".join(part2[:len(part2)-1]) + "/"
        elif part3 == 'Folder':
            part2 = file.split('/')
            part4 = part2[(len(part2)-2)]
            part2 = "/".join(part2[:len(part2)-2]) + "/"
        else:
            part2 = ''
            part4 = file
        part5 = ''  # This will be done after we filter out all the files/folder we don't want
        if part3 == "File":
            part6 = human_readable_filesize(os.stat(part0).st_size)
        else:
            part6 = ''
        part7 = datetime.datetime.fromtimestamp(os.stat(part0).st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        if part4[:1] == '.':
            part8 = True
        else:
            part8 = False
        part9 = ''
        files_unsorted.append([part0,part1,part2,part3,part4,part5,part6,part7,part8,part9])
    # At this point files_unsorted has been populated with _ALL_ files/Folders from default_folder_path
    # ==================================================================================================================
    # Now to go through that list and remove what doesn't match:
    # Box 9 = entry_Mask, checkbox_Folders, checkbox_Subfolders, checkbox_Files, checkbox_Hidden, spin_File_Name_Min, spin_File_Name_Max
    # entry_Mask = *.*
    if entry_Mask != "*.*" or entry_Mask[:2] == "*.":
        files_temp = []
        for file in files_unsorted:
            if file[3] == "Folder":
                files_temp.append(file)
            else:
                if re.search(entry_Mask[1:], file[4]):
                    files_temp.append(file)
        files_unsorted = files_temp
    # checkbox_Folders = True
    if checkbox_Folders is False:
        files_temp = []
        for file in files_unsorted:
            if file[3] == "File":
                files_temp.append(file)
        files_unsorted = files_temp
    # checkbox_Subfolders = False
    if checkbox_Subfolders is False:
        files_temp = []
        for file in files_unsorted:
            if file[2] == "/" or file[2] == "":
                files_temp.append(file)
        files_unsorted = files_temp
    # checkbox_Files = True
    if checkbox_Files is False:
        files_temp = []
        for file in files_unsorted:
            if file[3] == "Folder":
                files_temp.append(file)
        files_unsorted = files_temp
    # checkbox_Hidden = False
    if checkbox_Hidden is False:
        files_temp = []
        for file in files_unsorted:
            if file[8] is False:
                files_temp.append(file)
        files_unsorted = files_temp
    # spin_File_Name_Min = 0
    if spin_File_Name_Min > 0:
        files_temp = []
        for file in files_unsorted:
            if len(file[4]) >= spin_File_Name_Min:
                files_temp.append(file)
        files_unsorted = files_temp
    # spin_File_Name_Max = 0
    if spin_File_Name_Max > 0:
        files_temp = []
        for file in files_unsorted:
            if len(file[4]) <= spin_File_Name_Max:
                files_temp.append(file)
        files_unsorted = files_temp
    # Now that the list is filtered, we need to sort them before adding them to files_Full
    # ==================================================================================================================
    # Unfortunately, I couldn't find an easy way to do exactly what I was wanting,
    # so I had to break up the different File/Folder types and sort them individually,
    # then combine them in the ultimate order I chose:  Folders->Files->SubFolders->SubFiles.
    # Unfortunately, I could get the "natural sorting" to work with this...  Maybe in the future...
    # Folders
    temp_folders = []
    for file in files_unsorted:
        if file[3] == 'Folder' and file[2] == "/":
            temp_folders.append(file)
    temp_folders.sort(key=itemgetter(0))
    # SubFolders
    temp_subfolders = []
    for file in files_unsorted:
        if file[3] == 'Folder' and file[2] != "/":
            temp_subfolders.append(file)
    temp_subfolders.sort(key=itemgetter(2, 4))
    # Files
    temp_files = []
    for file in files_unsorted:
        if file[3] == 'File' and file[2] == "":
            temp_files.append(file)
    temp_files.sort(key=itemgetter(0))
    # SubFiles
    temp_subfiles = []
    for file in files_unsorted:
        if file[3] == 'File' and file[2] != "":
            temp_subfiles.append(file)
    temp_subfiles.sort(key=itemgetter(2, 4))
    files_Full = temp_folders + temp_files + temp_subfolders + temp_subfiles


def human_readable_filesize(num, suffix='B'):  # Make file sizes easier to read
    # Based on:  https://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size
    for unit in [' ', ' K', ' M', ' G', ' T', ' P', ' E', ' Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, ' Y', suffix)


def check_config_and_local_share_folders():  # Make sure that the .config and .local folders exist
    # This will check that there is a "~/.config/BSFEMA" folder.  If it doesn't exist, it will make it.
    full_path = os.path.expanduser("~/.config/BSFEMA/")
    if os.path.isdir(full_path):
        # print(str(full_path) + " exists")
        pass
    else:
        print("The ~/.config/BSFEMA/ folder doesn't exist for path:  " + str(full_path))
        print("Creating the ~/.config/BSFEMA/ folder for path:  " + str(full_path))
        try:
            os.mkdir(full_path)
        except OSError:
            print("Creation of the ~/.config/BSFEMA/ folder failed for path:  " + str(full_path))
        else:
            print("Creation of the ~/.config/BSFEMA/ folder succeeded for path:  " + str(full_path))
    # This will check that there is a "~/.local/share/BSFEMA/" folder.  If it doesn't exist, it will make it.
    full_path = os.path.expanduser("~/.local/share/BSFEMA/")
    if os.path.isdir(full_path):
        # print(str(full_path) + " exists")
        pass
    else:
        print("The ~/.local/share/BSFEMA/ folder doesn't exist for path:  " + str(full_path))
        print("Creating the ~/.local/share/BSFEMA/ folder for path:  " + str(full_path))
        try:
            os.mkdir(full_path)
        except OSError:
            print("Creation of the ~/.local/share/BSFEMA/ folder failed for path:  " + str(full_path))
        else:
            print("Creation of the ~/.local/share/BSFEMA/ folder succeeded for path:  " + str(full_path))


def read_in_rename_pairs_file():  # Read in the rename pairs file
    global rename_pairs_from_file
    rename_pairs_from_file.clear()
    global rename_pairs_file_to_load
    full_path = os.path.expanduser(rename_pairs_file_to_load)
    if os.path.isfile(full_path):
        with open(full_path, "r", encoding='utf-8-sig') as file:
            line = file.readline()
            line = line.replace('\n', '')  # Remove newline character
            line_count = 1
            while line:
                parts = line.split("/")
                if len(parts) == 0:
                    # Ignore line as it is not a valid rename pair (no "/" character)
                    pass
                elif len(parts) == 2:
                    rename_pairs_from_file[parts[0]] = parts[1]
                else:
                    # Ignore line as it is not a valid rename pair (too many "/" characters)
                    print("The following line (#" + str(line_count) + ") in the rename pair file is not a valid rename pair:  " + line)
                line = file.readline()
                line = line.replace('\n', '')  # Remove newline character
                line_count = line_count + 1
            file.close()


def read_in_application_settings():  # Read in the user's custom application settings
    global settings_file_to_load
    global application_Settings
    application_Settings.clear()  # Start fresh with no values
    # Normal Settings
    full_path = os.path.expanduser(settings_file_to_load)
    if os.path.isfile(full_path):
        with open(full_path, "r", encoding='utf-8-sig') as file:
            line = file.readline()
            while line:
                if line[:1] == "#":
                    pass
                elif line == "" or line == "\n":
                    pass
                else:
                    line = line.replace('\n', '')
                    if len(line.split("=")) > 1:  # Make sure there is a "=" in the line
                        if len(line.split("=")) == 2:  # Set normal value
                            application_Settings.append([line.split("=")[0],line.split("=")[1]])
                        elif len(line.split("=")) > 2:  # Set value that also contains a "=" character
                            application_Settings.append([line.split("=")[0], "=".join(line.split("=")[1:])])
                    else:
                        print("Invalid entry in settings.txt file:  " + line)
                line = file.readline()
        file.close()
    # These are now all settable available via the GUI
    # Hidden Settings (un-settable through UI)
    full_path = os.path.expanduser("~/.config/BSFEMA/hidden_settings.txt")
    if os.path.isfile(full_path):
        with open(full_path, "r", encoding='utf-8-sig') as file:
            line = file.readline()
            while line:
                if line[:1] == "#":
                    pass
                elif line == "" or line == "\n":
                    pass
                else:
                    line = line.replace('\n', '')
                    if len(line.split("=")) > 1:  # Make sure there is a "=" in the line
                        if len(line.split("=")) == 2:  # Set normal value
                            application_Settings.append([line.split("=")[0], line.split("=")[1]])
                        elif len(line.split("=")) > 2:  # Set value that also contains a "=" character
                            application_Settings.append([line.split("=")[0], "=".join(line.split("=")[1:])])
                    else:
                        print("Invalid entry in hidden_settings.dat file:  " + line)
                line = file.readline()
        file.close()


def return_padded_number_for_per_folder_option(sub_folder_name, Numbering_Start, Numbering_Increment, Numbering_Padding):  # box_7 padding
    global directory_counts
    # Since "" and "/" are the same "sub folder name", creating a temp name to store it
    temp_subfolder_name = ""
    if sub_folder_name == "":
        temp_subfolder_name = "/"
    else:
        temp_subfolder_name = sub_folder_name
    padded_number = str(Numbering_Start + (directory_counts[temp_subfolder_name] * Numbering_Increment)).rjust(Numbering_Padding, '0')
    # Increment the directory_counts[temp_subfolder_name] global
    directory_counts[temp_subfolder_name] = directory_counts[temp_subfolder_name] + 1
    return padded_number


def update_full_path_with_new_name(current_full_path, new_name, file_type):  # Update Full Path to the new full path with the updated rename_pairs[New Name]
    global default_folder_path
    if file_type == "File":
        temp = current_full_path.split('/')
        current_name = temp[len(temp) - 1]
        temp_full_path = current_full_path[:0 - len(current_name)]
        temp_full_path = str(os.path.join(temp_full_path, new_name))
    elif file_type == "Folder":
        if current_full_path[-1:] == "/":  # remove the final "/" from a path
            temp_full_path = current_full_path[:-1]
        temp = temp_full_path.split('/')
        current_name = temp[len(temp) - 1]
        # base_path = default_folder_path + "/"
        temp_full_path = temp_full_path[:0 - len(current_name)]
        temp_full_path = str(os.path.join(temp_full_path, new_name))
        if temp_full_path[-1:] != "/":  # remove the final "/" from a path
            temp_full_path = temp_full_path + "/"
    return temp_full_path


def update_local_path_with_new_value(current_full_path, current_name, file_type):  # Update Local Pathto the new local path with the updated rename_pairs[New Name]
    global default_folder_path
    if default_folder_path[-1:] != "/":  # remove the final "/" from a path
        temp_default_folder_path = default_folder_path + "/"
    local_path = current_full_path[len(temp_default_folder_path):]
    return local_path


if __name__ == '__main__':
    check_config_and_local_share_folders()  # Make sure that the .config and .local folders exist
    settings_file_to_load = "~/.config/BSFEMA/settings.txt"  # Load the default settings file
    read_in_application_settings()
    # Check for command line arguments, and set the default_folder_path appropriately
    if len(sys.argv) > 1:  # If there is a command line argument, check if it is a folder
        if os.path.isdir(sys.argv[1]):  # Valid folder:  so set the default_folder_path to it
            default_folder_path = sys.argv[1]
        elif os.path.isdir(os.path.dirname(os.path.abspath(sys.argv[1]))):  # If file path was sent:  use folder path from it.
            default_folder_path = os.path.dirname(os.path.abspath(sys.argv[1]))
        else:  # Invalid folder:  so set the default_folder_path to where the python file is
            default_folder_path = sys.path[0]
    else:  # No command line argument:  so set the default_folder_path to where the python file is
        default_folder_path = sys.path[0]
    main = Main()
    gtk.main()
