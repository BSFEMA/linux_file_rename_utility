# Linux File Rename Utility

## Application
Linux File Rename Utility

## Author
BSFEMA (https://github.com/BSFEMA)

## Purpose
To provide Linux with a good file rename utility.  I didn't particularly like any of the existing rename utilities available on Linux and I didn't like having to run a Windows one in Wine either...  This was also a good excuse to learn Gtk and Glade programming with Python.

# Installation
There really isn't an "install" for this since it is just a python script and a few other files.  With that said, there are a few different ways to 'download' it:

###The 'git clone' method:
Clone the repository.  In a terminal navigate to where you want the folder to be created and the files downloaded into, then run the following command:

    git clone https://github.com/BSFEMA/linux_file_rename_utility.git

Please note that this method will create a hidden ".git" folder.  If you just want the program files and nothing else, feel free to delete this folder.

###The 'git download zip' method:
On the main [linux_file_rename_utility](https://github.com/BSFEMA/linux_file_rename_utility) repository page, you can click on the green "Code" button, then click on the "Download Zip" option.  You can then extract the contents where you want to store the application.

###The 'curl' method:
Download the individual files directly.  Create a folder to store the files, navigate to it in a terminal window and run the following commands:

    curl -LJO https://github.com/BSFEMA/linux_file_rename_utility/blob/master/linux_file_rename_utility.py
    curl -LJO https://github.com/BSFEMA/linux_file_rename_utility/blob/master/linux_file_rename_utility.glade
    curl -LJO https://github.com/BSFEMA/linux_file_rename_utility/blob/master/linux_file_rename_utility.css
    curl -LJO https://github.com/BSFEMA/linux_file_rename_utility/blob/master/linux_file_rename_utility.svg
    curl -LJO https://github.com/BSFEMA/linux_file_rename_utility/blob/master/README.md
    curl -LJO https://github.com/BSFEMA/linux_file_rename_utility/blob/master/CHANGELOG.md
    curl -LJO https://github.com/BSFEMA/linux_file_rename_utility/blob/master/LICENSE

###The 'wget' method: 
Download the individual files directly.  Create a folder to store the files, navigate to it in a terminal window and run the following commands:

    wget --no-check-certificate --content-disposition https://github.com/BSFEMA/linux_file_rename_utility/blob/master/linux_file_rename_utility.py
    wget --no-check-certificate --content-disposition https://github.com/BSFEMA/linux_file_rename_utility/blob/master/linux_file_rename_utility.glade
    wget --no-check-certificate --content-disposition https://github.com/BSFEMA/linux_file_rename_utility/blob/master/linux_file_rename_utility.css
    wget --no-check-certificate --content-disposition https://github.com/BSFEMA/linux_file_rename_utility/blob/master/linux_file_rename_utility.svg
    wget --no-check-certificate --content-disposition https://github.com/BSFEMA/linux_file_rename_utility/blob/master/README.md
    wget --no-check-certificate --content-disposition https://github.com/BSFEMA/linux_file_rename_utility/blob/master/CHANGELOG.md
    wget --no-check-certificate --content-disposition https://github.com/BSFEMA/linux_file_rename_utility/blob/master/LICENSE

# Command Line Parameters
There is just 1:  It is the folder path that will be used to start renaming files from.  If this value isn't provided, then the starting path will be where this application file is located.  The intention is that you can call this application from a context menu from a file browser (e.g. Nemo) and it would automatically load up that folder.  If you pass it a path to a file, it will use the folder that the file resides in instead.

# Folders
This application will create a "~/.config/BSFEMA/" folder and a "~/.local/share/BSFEMA/" folder if they don't exist.
* The purpose of the "~/.config/BSFEMA/" folder is to store application specific config information (i.e. default, hidden, and saved settings files).
* The purpose of the "~/.local/share/BSFEMA/" folder is to store application specific data (i.e. history text files for each execution of a rename).

# Default settings file
You can add a "settings.txt" file to the "~/.config/BSFEMA/" folder (i.e. "~/.config/BSFEMA/settings.txt").  If this file exists, it will be used as the default settings to apply each time the application is launched.  This file holds all of the application settings that will be initially loaded.  You can use the "Save Settings to File" button and overwrite the "settings.txt" file.

# Hidden settings file
You can add a "hidden_settings.txt" file to the "~/.config/BSFEMA/" folder (i.e. "~/.config/BSFEMA/hidden_settings.txt").  If this file exists, it will be used as the default settings to apply each time the application is launched.  This file holds a few settings that are not stored in the normal settings.txt file.  Here is the complete list of options that you can set in the file:

"hidden_settings.txt" contents:

    # The following are various settings that you cannot set through the UI
    # Please see the line above each setting for the appropriate values
    # Commenting the line out (i.e. adding a '#' to the beginning of the line), the applicaiton will use the standard default options
    
    ##### Start the application maximized:
    # Default = False  [blank, commented out, or not set]
    # Values:  "True" or "False" only
    window_maximize=False
    
    ##### Direction of the spinner widgets:
    # Default = HORIZONTAL
    # Values:  "HORIZONTAL" or "VERTICAL" only
    # Notes: "HORIZONTAL" decreases the height compared to "VERTICAL", but increases the width
    spinner_orientation=HORIZONTAL
    
    ##### Starting vertical height of the data grid:
    # Default = 400
    # Values:  [integer >= 0]
    # Notes:  100 give 3 rows, 400 gives 16 rows (depending on your OS theme)
    scrollwindow_Data_Grid=400
    
    ##### Show icon on rename button:
    # Default = False  [blank, commented out, or not set]
    # Values:  "True" or "False" only
    # Notes:  This will cause the vertical window size to increase if spinner_orientation=HORIZONTAL
    button_Rename_image=False

Personally, I like setting spinner_orientation=VERTICAL & button_Rename_image=True, but that doesn't work on smaller monitors, which is why the defaults are set to the above.

# Saved settings files
You can save any configuration to a .txt file and then open/load that settings file at a later time.  This is useful if you periodically perform the same rename actions.  The settings files are stored in the "~/.config/BSFEMA/" folder (e.g. "~/.config/BSFEMA/some_saved_settings_file.txt") by default.

# Save History files
If you have the "Save History" option checked, it will create a file in the "~/.local/share/BSFEMA/" folder each time the "Rename Files" button is clicked.
The filename will be in the format of "%Y_%m_%d_%H_%M_%S_%f".txt (e.g. 2020_12_18_15_20_24_186471.txt).
The format of the file is (without spaces):  ["File"/"Folder"] | [full path + file/folder name] | [new file/folder name] | [rename status]

Examples:

    Folder|/home/example_user/Documents/test_1/|test|Renamed!
    Folder|/home/example_user/Documents/test_2/|test|New Name path already exists
    File|/home/example_user/Documents/pic_example_with_underscores_1.jpg|pic example 1.jpg|Renamed!
    File|/home/example_user/Documents/pic_example_with_underscores_2.jpg|pic example 2.jpg|Renamed!

# Possible Rename Statuses
Before clicking the Rename Files button:
* No change...
* To be changed

After clicking the Rename Files button:
* Renamed!
* New Name path already exists
* FAILED TO RENAME!
* Current Name's Full Path doesn't exist

# Import Rename Pairs
You can import a "/" delimited list of rename pairs.
It will apply this after it has gone through boxes 1-8.
The rename pairs must be the full file name including any file extension.
Each time the "Import Rename Pairs" button is pressed it will immediately wipe out any existing rename pair information.  This means that if you import a rename pair, but want to blank it out, simply click the "Import Rename Pairs" button and then cancel the file open dialog.
Any invalid rows will be output to the terminal, with the line number for easy reference.

Example rename pairs .txt file:

    1.txt/2.txt
    1.txt/3.txt
    1.txt/4.txt
    subfolder_1/Sub Folder 1

Note:  If there are multiple resulting file names for a given file name, it will use the last one.  In the above example, "1.txt" will be renamed to "4.txt".

# Icon File
If you copy the "linux_file_rename_utility.svg" to "~.local/share/icons", then it should be picked up by the system and can be used as any other icon.

# Nemo Action context menu

You can create a nemo action file so that you can right click in a folder and launch the Linux File Rename Utility from there.

Example (filename = "linux_file_rename_utility.nemo_action"):

    [Nemo Action]
    Name=Linux File Rename Utility
    Quote=double
    Exec=python3 "<YOUR_PATH_TO>/linux_file_rename_utility.py" %F
    Selection=any
    Extensions=any
    Icon-Name=linux_file_rename_utility

Save the "linux_file_rename_utility.nemo_action" file to "~/.local/share/nemo/actions".

Note:  The "Icon-Name" line references the "linux_file_rename_utility" name.  Please see the "Icon File" section above for more information on this.

Context menus might be possible for other file managers, but that will be up to you to figure out ;) 

# CSS
Each UI object (e.g. button, label, etc.) has a name and can therefore have its own unique css applied to it.

Examples:

    1. If you wanted all text to be 10pt font, you can set the "window {}" line in the css file to a value of "font-size: 10px;"  This will then filter down to all objects contained within it.
        * window {font-size: 10px;}
    2. If you wanted to make just the "button_Rename" object have a specific background and foreground color, you can set the "button#button_Rename {}" line to a value of something like "background: #FF0000; color: #0000FF;".
        * button#button_Rename {background: #FF0000; color: #0000FF;}

# Known issues
I have noticed that when you re-order the columns in the data grid that Gtk throws warnings like this:

    (linux_file_rename_utility.py:628656): Gtk-WARNING **: 18:50:14.570: Negative content width -15 (allocation 1, extents 8x8) while allocating gadget (node button, owner GtkButton)

Unfortunately, I don't know why this error is being thrown or how to fix it.  Just ignore it or don't re-order the columns...

# Screenshots

I have uploaded a few screenshots from various Linux distros here:  [https://imgur.com/a/2jxFVG1](https://imgur.com/a/2jxFVG1)

# Changelog
See the [CHANGELOG.md file](https://github.com/BSFEMA/linux_file_rename_utility/blob/master/CHANGELOG.md).

# License
**MIT**. See the [License file](https://github.com/BSFEMA/linux_file_rename_utility/blob/master/LICENSE).
