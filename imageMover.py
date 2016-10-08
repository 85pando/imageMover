#!/usr/bin/python -tt
# -*- coding: UTF-8 -*

"""
ImageMover is a program that can be used to sort images. Copy all images into one folder and create a subfolder for each category you want. ImageMover will display a button for each folder. Each image will be opened and when you press the corresponding button it will be moved into this folder.

Copyright (C) 2015 Stephan Heidinger

This work is licensed under a Creative Commons Attribution-ShareAlike 3.0 Unported License.

See the full license text here: https://creativecommons.org/licenses/by-sa/3.0/legalcode
"""

######### Imports
from __future__ import print_function
from Tkinter import *
import Image, ImageTk
from os import walk
from os import path
from os import chdir
from os import remove
from os import rename
from os import makedirs
from os import symlink
from tkMessageBox import showerror
from optparse import OptionParser
######### End Imports

class ImageMover:

  """
  The ImageMover class displays a windows in which an image is shown. Buttons are presented for skipping, deleting or moving the image. The buttons for moving images are based on the folders in the current path.
  """

  def __init__(self, parent, verbose):
    self.verbose = BooleanVar(value=verbose)
    self.lastMovedImage = []
    # prepare windows

    ## newCategory window
    self.newCategoryWindow = Toplevel()
    self.newCategoryWindow.title("Create new Category")
    Label(self.newCategoryWindow, text="Enter the name for the new Category:").pack()
    self.newCategoryText = StringVar()
    Entry(self.newCategoryWindow,
          textvariable=self.newCategoryText,
         ).pack(fill=X)
    Button(self.newCategoryWindow,
           text="Create new Category",
           command=self.newCategoryExecuteClick,
    ).pack(fill=X,side=LEFT)
    Button(self.newCategoryWindow,
           text="Cancel",
           command=self.newCategoryCancelClick,
    ).pack(fill=X,side=LEFT)
    self.newCategoryWindow.withdraw()

    ## Rename window
    self.renameWindow = Toplevel()
    self.renameWindow.title("Rename Image")
    Label(self.renameWindow, text="Enter the new name for the current image:").pack()
    self.renameText = StringVar()
    Entry(self.renameWindow,
          textvariable=self.renameText,
         ).pack()
    Button(self.renameWindow,
           text="Rename image",
           command=self.renameExecuteClick,
           ).pack(side=LEFT)
    Button(self.renameWindow,
            text="Cancel",
            command=self.renameCancelClick,
            ).pack(side=LEFT)
    self.renameWindow.withdraw()

    ## Symlink window
    self.symlinkWindow = Toplevel()
    self.symlinkWindow.title("Create Link")
    Label(self.symlinkWindow, text="Name on the button").grid(row=0, column=0)
    Label(self.symlinkWindow, text="Name on the button").grid(row=0, column=1)
    self.symlinkLinkName = StringVar()
    Entry(self.symlinkWindow,
          textvariable=self.symlinkLinkName,
          ).grid(row=1,column=0)
    self.symlinkSourcePath = StringVar()
    Entry(self.symlinkWindow,
          textvariable=self.symlinkSourcePath,
         ).grid(row=1, column=1)
    Button(self.symlinkWindow,
           text="Create Link",
           command=self.symlinkExecuteClick,
           ).grid(row=2,column=0)
    Button(self.symlinkWindow,
           text="Cancel",
           command=self.symlinkCancelClick,
    ).grid(row=2, column=1)
    self.symlinkWindow.withdraw()

    ## parent window
    self.myParent = parent
    self.myParent.title("Not yet initialized")

    # create menu bar
    self.menubar = Menu(self.myParent)
    self.myParent.config(menu=self.menubar)
    ## create program menu
    self.programmenu = Menu(self.menubar, tearoff=0)
    self.menubar.add_cascade(label="Program", menu=self.programmenu)
    self.programmenu.add_checkbutton(label="Log to Command Line",
                                 variable=self.verbose,
    )
    self.programmenu.add_separator()
    self.programmenu.add_command(label="New Category", command=self.newCategoryClick)
    self.programmenu.add_command(label="Link folder", command=self.symlinkClick)
    self.programmenu.add_separator()
    self.programmenu.add_command(label="Exit", command=self.closeWindow)
    self.menubar.add_command(label="Undo Move", command=self.undoClick)
    self.menubar.add_separator()
    self.menubar.add_command(label="Rename Image", command=self.renameClick)

    # create imageFrame, Scrollbars & canvas
    self.imageFrame = Frame(self.myParent, bd=2, relief=SUNKEN)
    self.imageFrame.grid_rowconfigure(0, weight=1)
    self.imageFrame.grid_columnconfigure(0, weight=1)
    xscroll = Scrollbar(self.imageFrame, orient=HORIZONTAL)
    xscroll.grid(row=1, column=0, sticky=E + W)
    yscroll = Scrollbar(self.imageFrame, orient=VERTICAL)
    yscroll.grid(row=0, column=1, sticky=N + S)
    self.canvas = Canvas(self.imageFrame,
                    bd=0,
                    xscrollcommand=xscroll.set,
                    yscrollcommand=yscroll.set)
    self.canvas.grid(row=0, column=0, sticky=N + S + E + W)
    xscroll.config(command=self.canvas.xview)
    yscroll.config(command=self.canvas.yview)
    self.imageFrame.pack(fill=BOTH, expand=1)

    # get directoryNames and fileNames from given directory
    walkResult = walk(pathString)
    walkResult = walkResult.next()
    # split up walkResult into directories and files
    directoryNames = sorted(walkResult[1])
    self.fileNames = sorted(walkResult[2])
    # create skip and delete button
    Button(self.myParent, text="Delete", command=self.deleteClick).pack(side=LEFT)
    Button(self.myParent, text="Skip", command=self.skipClick).pack(side=LEFT)
    # create arrays for folder buttons
    # noinspection PyUnusedLocal
    buttons = [Button() for x in range(len(directoryNames))]
    for counter in range(len(directoryNames)):
      buttons[counter] = Button(self.myParent,
                                text=directoryNames[counter],
                                command=self.directoryClickClosure(directoryNames[counter])
      )
      buttons[counter].pack(side=LEFT)

    self.currImage = None
    # get first image
    if self.fileNames:
      self.displayNextImage()
      self.drawCanvas()
    else:
      self.closeWindow()

  def skipClick(self):
    """
    This method is used when clicking the skip button. It does not move the current image, just goes on to the next.
    """
    if self.verbose.get():
      print("Skipping image:", self.currImage)
    self.displayNextImage()

  def deleteClick(self):
    """
    This method is used, when clicking the delete button. It deletes the current image and afterwards displays the next image.
    """
    # just to be sure its an image
    if self.testIfImage(self.currImage):
      if self.verbose.get():
        print("Deleting image:", self.currImage)
      remove(self.currImage)
    self.displayNextImage()

  def directoryClickClosure(self, label):
    """
    This is a closure method that is called upon pressing one of the directory buttons. It sends the label of the directory to the directoryClick method.
    :param label: the label of the button clicked
    :return: the label of the button clicked
    """
    return lambda: self.directoryClick(label)

  def directoryClick(self, targetString):
    """
    This method is used, when one of the directory buttons is clicked. It moves the current image to the corresponding folder and afterwards displays the next image.
    :param targetString:
    """
    # just to make sure its an image
    if self.testIfImage(self.currImage):
      targetString = targetString + "/" + self.currImage
      if self.verbose.get():
        print("Moving image", self.currImage, "to", targetString)
      # store new image location for possible undo operation
      self.lastMovedImage.append((self.currImage, targetString))
      rename(self.currImage, targetString)
      self.displayNextImage()

  def undoClick(self):
    """
    This method undoes the last moves. It cannot undo deletes and does not care about skips.
    """
    if len(self.lastMovedImage) == 0:
      if self.verbose.get():
        print("There is no previous image to be moved.")
    else:
      previousImage, previousPath = self.lastMovedImage.pop()
      # put current image back into list
      self.fileNames.append(self.currImage)
      if self.verbose.get():
        print("Put image", self.currImage, "back into the file list to be processed.")
      # move previous image back into the main folder
      rename(previousPath, previousImage)
      if self.verbose.get():
        print("Undo move of", previousImage, "from location", previousPath)
      # display the image which we just moved back
      self.displaySpecificImage(previousImage)

  def newCategoryClick(self):
    """
    This method makes the self.newCategoryWindow visible and sets a new string to be set in the Entry.
    """
    if self.verbose.get():
      print("Opening new category window.")
    self.newCategoryText.set("new category")
    self.newCategoryWindow.deiconify()
    self.newCategoryWindow.focus()


  def newCategoryExecuteClick(self):
    """
    This method creates a new folder and a button so that images can now be moved into this folder. The name of the folder is based on the content of the Entry widget inside the self.newCategoryWindow. If the folder already exists a message may be posted on the console based on verbosity.
    """
    newCategoryName = self.newCategoryText.get()
    newCategoryPath = path.abspath(newCategoryName)
    if path.exists(newCategoryPath):
      if self.verbose.get():
        print("Category already exists")
      showerror("Oh noes!", "The new category already exists.")
    else:
      if self.verbose.get():
        print("Create new Category", newCategoryName)
      makedirs(newCategoryPath)
      Button(self.myParent,
             text=newCategoryName,
             command=self.directoryClickClosure(newCategoryName)
      ).pack(side=LEFT)
      self.newCategoryWindow.withdraw()

  def newCategoryCancelClick(self):
    """
    This method hides the createNewCategory window and may print something to the console based on verbosity.
    """
    if self.verbose.get():
      print("No new category created.")
    self.newCategoryWindow.withdraw()

  def renameClick(self):
    """
    This method makes the self.renameWindow visible and sets a new string to be set in the Entry.
    """
    if self.verbose.get():
      print("Opening renaming window.")
    self.renameText.set("newImageName.jpg")
    self.renameWindow.deiconify()
    self.renameWindow.focus()

  def renameExecuteClick(self):
    newFileName = self.renameText.get()
    newFilePath = path.abspath(newFileName)
    if path.exists(newFilePath):
      if self.verbose.get():
        print("File already exists.")
      showerror("Oh noes!", "The filename you provided already exists.")
    else:
      if self.verbose.get():
        print("Rename image", self.currImage, "to", newFileName)
      rename(self.currImage, newFilePath)
      self.currImage = newFileName
      self.displaySpecificImage(newFileName)
      self.renameWindow.withdraw()

  def renameCancelClick(self):
    """
    This method hides the renameCategory window and may print something to the console based on verbosity.
    """
    if self.verbose.get():
      print("Image not renamed.")
    self.renameWindow.withdraw()

  def symlinkClick(self):
    """
    This method makes the self.symlinkWindow visible and sets a new string to be set in the Entry.
    """
    if self.verbose.get():
      print("Opening symlinking window.")
    self.symlinkLinkName.set("linkName")
    self.symlinkSourcePath.set("linkSource")
    self.symlinkWindow.deiconify()
    self.symlinkWindow.focus()

  def symlinkExecuteClick(self):
    if path.exists(self.symlinkLinkName.get()):
      if self.verbose.get():
        print("Link name already exists.")
      showerror("Oh noes!", "The link name already exists.")
    else:
      if not path.exists(self.symlinkSourcePath.get()):
        if self.verbose.get():
          print("Link source does not exists.")
        showerror("Oh noes!", "The source for the link does not exist.")
      else:
        symlink(self.symlinkSourcePath.get(), self.symlinkLinkName.get())
        Button(self.myParent,
               text=self.symlinkLinkName.get(),
               command=self.directoryClickClosure(self.symlinkLinkName.get())
               ).pack(side=LEFT)
        self.symlinkWindow.withdraw()

  def symlinkCancelClick(self):
    if self.verbose.get():
      print("Symlinking cancelled.")
    self.symlinkWindow.withdraw()

  def displayNextImage(self):
    """
    This method displays the next image from a list of files in the canvas. When there are no more images left, it will close the window.
    """
    prevImage = self.currImage
    while self.fileNames:
      # get next file
      self.currImage = self.fileNames.pop()
      if self.testIfImage(self.currImage):
        # found image
        break
    if self.currImage == prevImage:
      if self.verbose.get():
        print("No more image left, exiting.")
      self.closeWindow()
    else:
      self.drawCanvas()

  def displaySpecificImage(self, imagePath):
    """
    This method will display the image that is given at the path imagePath.
    :param imagePath: The path of the image to display instead of the current one.
    """
    # set specific image as image to display
    self.currImage = imagePath
    self.drawCanvas()

  @staticmethod
  def testIfImage(filetotest):
    """
    This method can be used to test, if a file can be interpreted as an image.
    :param filetotest: The file to test for interpretability as an image
    :return: True if filetotest can be interpreted as an image. False otherwise
    """
    # noinspection PyBroadException
    try:
      Image.open(filetotest)
    except IOError:
      # print("IOError")
      return False
    except:
      print("unknown error")
      return False
    return True

  def drawCanvas(self):
    """
    This method takes the current image and displays it in the Canvas.
    """
    # noinspection PyBroadException
    try:
      # this variable has to be kept in class, or drawing might fail
      # noinspection PyAttributeOutsideInit
      self.imagefile = ImageTk.PhotoImage(Image.open(self.currImage))
      self.canvas.delete("all")
      self.canvas.create_image(0, 0, image=self.imagefile, anchor="nw")
      self.canvas.config(scrollregion=self.canvas.bbox(ALL))
    except:
      if self.verbose.get():
        print("This should not have happened, I verified that", self.currImage, "is an image beforehand.")
      exit(1)
    self.myParent.title("images left: " + str(len(self.fileNames)) + "; image: " + self.currImage)
    # draw frame
    self.imageFrame.update_idletasks()
    # self.imageFrame.update()

  def closeWindow(self):
    """
    This method can be used to close the ImageMover window.
    """
    self.myParent.destroy()

    ###### End Class

if __name__ == '__main__':
  usage = "usage: %prog [options] [path]"
  parser = OptionParser(usage=usage, version="%prog v0.1.x")
  parser.add_option('-v', '--verbose',
                    action='store_true',
                    dest='verbose',
                    help='enables output to command line'
                    )
  parser.set_defaults(verbose=False)
  (options, args) = parser.parse_args()

  # create pathString
  pathString = ""
  # remove all options from args
  while len(sys.argv) >= 2 and sys.argv[1].startswith("-"):
    del sys.argv[1]
  # check if a path was given
  if len(sys.argv) == 1:
    pathString = path.abspath("./")
    if options.verbose:
      print("Using current directory as path.")
  else:
    pathString = path.abspath(sys.argv[1])
    if options.verbose:
      print("Using path:", pathString)
  chdir(pathString)

  # start the program
  root = Tk()
  imageMover = ImageMover(root, options.verbose)
  root.mainloop()
  exit(0)
