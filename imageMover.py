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
from optparse import OptionParser
######### End Imports

class ImageMover:

  """
  The ImageMover class displays a windows in which an image is shown. Buttons are presented for skipping, deleting or moving the image. The buttons for moving images are based on the folders in the current path.
  """

  def __init__(self, parent, verbose):
    self.verbose = verbose
    self.lastMovedImage = []

    self.myParent = parent
    self.myParent.title("Not yet initialized")
    # create menu bar
    self.menubar = Menu(self.myParent)
    self.myParent.config(menu=self.menubar)
    # create program menu
    self.programmenu = Menu(self.menubar, tearoff=0)
    self.menubar.add_cascade(label="Program", menu=self.programmenu)
    self.programmenu.add_checkbutton(label="Log to Command Line",
                                 variable=self.verbose,
                                 onvalue=True,
                                 offvalue=False,
    )
    self.programmenu.add_separator()
    self.programmenu.add_command(label="Exit", command=self.closeWindow)
    self.menubar.add_command(label="Undo Move", command=self.undoClick)
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
    if self.verbose:
      print("Skipping image:", self.currImage)
    self.displayNextImage()

  def deleteClick(self):
    """
    This method is used, when clicking the delete button. It deletes the current image and afterwards displays the next image.
    """
    # just to be sure its an image
    if self.testIfImage(self.currImage):
      if self.verbose:
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
      if self.verbose:
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
      if self.verbose:
        print("There is no previous image to be moved.")
    else:
      previousImage, previousPath = self.lastMovedImage.pop()
      # put current image back into front of list
      self.fileNames = [self.currImage] + self.fileNames
      if self.verbose:
        print("Put image", self.currImage, "back into the file list to be processed.")
      # move previous image back into the main folder
      rename(previousPath, previousImage)
      if self.verbose:
        print("Undo move of", previousImage, "from location", previousPath)
      # display the image which we just moved back
      self.displaySpecificImage(previousImage)

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
      if self.verbose:
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
      if self.verbose:
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
  parser = OptionParser(usage=usage, version="%prog 0.1")
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
