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
