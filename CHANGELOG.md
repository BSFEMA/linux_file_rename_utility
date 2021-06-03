# v1.5
* Performance:  I dramatically increased the speed at which the data grid is updated after the file renaming takes place.  Updating 3000 records in the data grid after the renaming used to take [94.98 seconds], but it now takes [0.5 seconds].
* Fixed:  I forgot to add the "checkbox#checkbox_Replace_Case{}" line in the .css file when I added that feature.
* Fixed:  Removed the "viewport_Data_Grid" widget.  This makes the data grid column headers fixed in place and will no longer scroll off.  I updated the .css file accordingly.  I also moved the "self.set_scrollwindow_Data_Grid_height(400)" line to before the "window.show()" to prevent some GTK errors from displaying as a result of the change.

# v1.4
* Added:  Case sensitive option for searching in Box_2
* Changed:  Two word labels were given a new line to make them 2 lines:  "Case Sensitive", "Per Folder", "Min. Len.", "Max. Len."

# v1.3
* Bug:  When Folders=unchecked & Subfolders=checked in Box_9, the result was Subfolders were still being shown in data grid.  This has been corrected so that no Type=Folder records will be shown when Folders=unchecked. 

# v1.2
* Performance:  Increased the speed at which unselected rows "New Name" and "Status" columns are blanked out as well as selected rows "New Name" is modified by boxes 1-8.
* Fixed:  The "combo_Name_Entry" line in "def button_Reset_clicked" moved up two lines to be in the correct position...

# v1.1
* Added:  Importing a rename pair file.
* Added:  Better CSS customization.  Each UI object has been named and can now be customized.
* Added:  Added new hidden settings:  button_Rename_image

# v1.0
* Starting point.  This is the base application with everything working.
