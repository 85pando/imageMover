#!/usr/bin/python -tt
# -*- coding: UTF-8 -*

"""
ImageMover is a program that can be used to sort images. Copy all images into one folder and create a subfolder for each category you want. ImageMover will display a button for each folder. Each image will be opened and when you press the corresponding button it will be moved into this folder.

Copyright (C) 2015 Stephan Heidinger
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
######### End Imports

class ImageMover:

  def __init__(self, parent):
    self.myParent = parent
    self.myParent.title("Not yet initialized")
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
    Button(self.myParent, text="Skip", command=self.skipClick).pack(side=LEFT)
    Button(self.myParent, text="Delete", command=self.deleteClick).pack(side=LEFT)
    # create arrays for folder buttons
    buttons = [0 for x in range(len(directoryNames))]
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
      exit(1)

  def skipClick(self):
    print("Skipping image:", self.currImage)
    self.displayNextImage()

  def deleteClick(self):
    # just to be sure its an image
    if self.testIfImage(self.currImage):
      print("Deleting image:", self.currImage)
      remove(self.currImage)
    self.displayNextImage()

  def directoryClickClosure(self, label):
    return lambda: self.directoryClick(label)

  def directoryClick(self, targetString):
    # just to make sure its an image
    if self.testIfImage(self.currImage):
      targetString = targetString + "/" + self.currImage
      print("Moving image", self.currImage, "to", targetString)
      rename(self.currImage, targetString)
      self.displayNextImage()

  def displayNextImage(self):
    prevImage = self.currImage
    while self.fileNames:
      # get next file
      self.currImage = self.fileNames.pop()
      if self.testIfImage(self.currImage):
        # found image
        break
    if self.currImage == prevImage:
      print("No more image left, exiting.")
      exit(0)
    else:
      self.drawCanvas()

  @staticmethod
  def testIfImage(filetotest):
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
    try:
      # this variable has to be kept in class, or drawing might fail
      self.imagefile = ImageTk.PhotoImage(Image.open(self.currImage))
      self.canvas.delete("all")
      self.canvas.create_image(0, 0, image=self.imagefile, anchor="nw")
      self.canvas.config(scrollregion=self.canvas.bbox(ALL))
    except:
      print("This should not have happened, I verified that", self.currImage, "is an image beforehand.")
      exit(1)
    self.myParent.title("images left: " + str(len(self.fileNames)) + "; image: " + self.currImage)
    # draw frame
    self.imageFrame.update_idletasks()
    # self.imageFrame.update()
###### End Class

def main():
  root = Tk()
  imageMover = ImageMover(root)
  root.mainloop()
  exit(0)

if __name__ == '__main__':
  pathString = ""
  # check for one argument
  if not len(sys.argv) == 2:
    # no path given, use current path
    pathString = path.abspath("./")
  else:
    # path is given
    pathString = path.abspath(sys.argv[1])
  # images base path
  print("image base path:", pathString)
  chdir(pathString)
  # start the program
  main()