from os import listdir, startfile, path, remove, sep
import os
import pathlib
from ctypes import *
from tkinter import *
from io import BytesIO
from atexit import register
from ctypes.wintypes import *
from tkinter import ttk, filedialog, messagebox
from tkinter.filedialog import askopenfilename, asksaveasfilename
from PIL import Image, ImageTk, ImageFilter, ImageEnhance, ImageOps, ImageGrab

"""
Hamcrop

Suite of quick cropping tools for the ham on the go.
Need to have:
    forbid image from being drawn behind buttons (set a margin)

Nice to have:
    Static Transparency BG
    Pan and Zoom
    Ham Batchcrop integration
        Guidelines for custom multicrops
        Dialogue for div crop
        Dialogue for custom crop
        Movable guidelines to define custom crops
    Imlist thumbnail view (like windows explorer thumbnail mode) but one vertical column

Currently Implemented
    Opens an image
        With windows file chooser
        From CMD
        From drag and drop
        From clipboard
    Saves
        With windows file chooser
        To clipboard
    Rotates
        In 90 deg increments
        By the degree
    Crops
        Dynamically drawn crop box and shaded area
        Crops images larger than the screen by scaling 
            them down and scaling up the crop
   
Known Bugs
    A conflict between scaler and resizable canvas causes image to only appear 
        at half size on first load, but then rotating or undoing fixes it.
        The issue happens in open_img
"""

formats = ('.gif','.jpg','.png','.jpeg','.bmp')
tempfiles = ('clipboard.png','temp.png')

version = 1.1

help  = """
Click and drag to create a crop box
Click to clear the box

TAB is Rotate Image by 90 Degrees
CTRL C is copy image to clipboard
CTRL V is paste image from clipboard
CTRL Z is Undo
CTRL S is save
CTRL A is Overwrite
CTRL O is Open Image
ENTER If theres a crop box, Enter applies crop, if not it overwrites the file. Double press to crop and save.
Left Arrow loads previous image
Right Arrow loads next image

Hamcrop version {}
Made by hamsolo474 2021 
""".format(str(version))

def handle_path(path):
    splitters = ['\\','/','//', os.sep]
    count = 0
    op = ['']
    for char in path:
        if char in splitters:
            count+=1
            op.append('')
        else:
            op[count] += char
    print(op)
    fullpath = os.sep.join(op).strip()
    if '.' in op[-1]:
        file = op[-1].strip()
    else:
        file = None
    folder = os.sep.join(op[:-1]).strip()
    print('fp', fullpath, '\nFolder', folder, '\nFile',file)
    return fullpath, folder, file

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class ResizingCanvas(Canvas):
    def __init__(self,parent,**kwargs):
        Canvas.__init__(self,parent,**kwargs)
        self.bind("<Configure>", self.on_resize)
        self.height = self.winfo_reqheight()
        self.width = self.winfo_reqwidth()

    def on_resize(self,event):
        # determine the ratio of old width/height to new width/height
        wscale = float(event.width)/self.width
        hscale = float(event.height)/self.height
        self.width = event.width
        self.height = event.height
        # resize the canvas 
        self.config(width=self.width, height=self.height)
        # rescale all the objects tagged with the "all" tag
        self.scale("all",0,0,wscale,hscale)

class main():
    def __init__(self, name = None):
        self.root    = Tk()
        self.root.title("hamcrop")
        self.fill    = "black" # Used for colouring the crop rects
        self.outline = "" # Same as above
        self.centre  = "magenta" # Used for colouring the centre crop rect
        self.alpha   = 0.7 # Used for colouring the crop rects
        self.stroke  = 5 # Stroke thickness for the centre crop rect
        self.name    = name # Filename
        self.folder  = os.getcwd()  # Folder the file is in
        self.path    = None # Whole file path
        self.spath   = os.getcwd() # Used for open_paste
        self.imlist  = [] # storing images to avoid garbage collection
        self.imlower = [] # used for fixing paths when you load from commandline with questionable case
        self.begin   = None # To store coordinates for first click of crop rect
        self.degrees = 0 # degreees for the rot variable
        self.size    = (100,100) #Window starting size (Useless)
        self.offset  = (0,50) # Does nothing anymore, used to add a margin
        self.canCrop = False # used for enter handling
        self.scale   = 1 # Used for scaling
        self.images  = [] # used for keyboard navigation
        #self.fr      = True # first run
        self.single  = Image.open(resource_path('tbs.png')) # white grey check box background
        self.slidrot = IntVar() # stores the value of the rotation slider
        self.index   = StringVar() #Stores the index of the image in the imlist
        self.delcounter = 0 # delete requires a double press, counts the number of presses
        myframe      = Frame(self.root)
        myframe.pack(fill=BOTH, expand=YES)
        self.cv = ResizingCanvas(myframe,width=850, height=400, bg="dark grey", highlightthickness=0)
        self.cv.pack(fill=BOTH, expand=YES)
        objects = [Button(self.cv, text = 'Open Image',  command = self.open_img),
                   Button(self.cv, text = 'Crop',        command = self.crop),
                   Button(self.cv, text = 'Undo',        command = self.restore),
                   Button(self.cv, text = 'Save As',     command = self.save_img),
                   Button(self.cv, text = 'Overwrite',   command = self.overwrite), 
                   Button(self.cv, text = '+90',         command = self.rot_90),
                   Scale(self.cv,  from_= -90, to = 90,  command = self.rotate_image,
                         orient = HORIZONTAL, length = 300, variable = self.slidrot),
                   Button(self.cv, text = 'Open Folder', command = self.open_folder),
                   Button(self.cv, text = 'Delete File', command = self.delete),
                   Button(self.cv, text = '<- Prev Img', command = self.open_prev),
                   Button(self.cv, text = 'Next Img ->', command = self.open_next),
                   Label(self.cv, textvariable = self.index), #Image count
                   Button(self.cv, text = 'Help',        command = self.display_help),
                   ]
        for col, obj in enumerate(objects):
            obj.grid(row = 1, column = col+1)
        #self.cv.addtag_all("all")
        # bind mouse event with canvas(self.cv)
        self.cv.bind("<B1-Motion>",     self.draw_rect) #used for dyanmic box drawing
        self.cv.bind("<ButtonPress>",   self.set_begin)
        self.cv.bind("<ButtonRelease>", self.draw_rect) #used for clearing 
        self.root.bind("<Left>",        self.open_prev)
        self.root.bind("<Right>",       self.open_next)
        self.root.bind("<Delete>",      self.delete)
        self.root.bind("<Return>",      self.handle_enter)
        self.root.bind("<Tab>",         self.rot_90)
        self.keybind("<Control-Key-z>", self.restore)
        self.keybind("<Control-Key-s>", self.save_img)
        self.keybind("<Control-Key-a>", self.overwrite)
        self.keybind("<Control-Key-o>", self.open_img)
        self.keybind("<Control-Key-v>", self.open_paste)
        self.keybind("<Control-Key-c>", self.save_clipboard)

        if not name == None:
            self.open_img(name) #If theres a file passed through the cmd open it immediately
        
    def keybind(self, key, func):
        # this function makes case insensitive key bindings
        # Takes a string like this "<Control-Key-c>" grabs the C and makes a 
        # keybinding in both cases for it
        fkey = key[-2].lower()
        keystr = (''.join([key[:-2],fkey,key[-1]]),''.join([key[:-2],fkey.upper(),key[-1]]))
        for i in keystr:
            self.root.bind(i, func)

    def fix_size(self, size):
        # Check to see if new size is greater than current size
        if size > self.size:
            self.size = size
            # Geometry wants a string like this
            # 100x200
            self.root.geometry("x".join([str(i) for i in self.size]))

    def set_begin(self, event):
        self.begin = event # used for draw rect
    
    def display_help(self, event=''):
        messagebox.showinfo("Hamcrop Help", help)

    def within_bounds(self,x, y):
        # Maybe implement this one day, but you dont need it
        x= int(x)#-self.offset[0]
        y= int(y)#-self.offset[1]
        iw = self.img.width()
        ih = self.img.height()
        if x < iw:
            if x > 0:
                pass
            else:
                x = 0
        else:
            x = iw
        if y < ih:
            if y > 0:
                pass
            else:
                y = 0
        else:
            y = ih
        print(x,y)
        return (x,y)

    def draw_image(self, img, x = None, y = None):
        if x == None and y == None:
            x = (self.cv.width  + self.offset[0])/2
            y = (self.cv.height + self.offset[1])/2
        self.img   = ImageTk.PhotoImage(self.scaler(img))
        self.cv.create_image(x, y, image=self.img)

    def create_rectangle(self, x1, y1, x2, y2, **kwargs):
        # https://stackoverflow.com/a/54645103/992644
        # Used for creating transparent rectangles
        if 'alpha' in kwargs:
            alpha = int(kwargs.pop('alpha') * 255)
            fill  = kwargs.pop('fill')
            fill  = self.root.winfo_rgb(fill) + (alpha,)
            tag   = kwargs.pop('tags')
            image = Image.new('RGBA', (x2-x1, y2-y1), fill)
            self.images.append(ImageTk.PhotoImage(image))
            self.cv.create_image(x1, y1, image=self.images[-1], anchor='nw', tags = tag)
        self.cv.create_rectangle(x1, y1, x2, y2, **kwargs)

    def draw_rect(self,event):
        # Clears existing drawings before drawing new things
        self.cv.delete("del")
        try:
            self.img.width() # This will fail if someone clicks the background before and img is loaded
        except AttributeError as e:
            print("Draw_rect Attribute Error, this will fail if someone clicks the background before img is loaded", e)
            return None
        #rectangles are drawn on self.cv from top left to bottom right
        # we are working with two coordinate systems here, window coordinates and image coordinates
        # xo and yo are the offset of image coords 0,0 and winodw coords 0,0
        xo, yo = [self.cv.width/2  - self.img.width()/2, 
                  self.cv.height/2 - self.img.height()/2] 
        begin  = (self.begin.x, self.begin.y)
        end    = (event.x, event.y)
        if begin == end:
            #self.cv.create_oval(begin[0]-5,begin[1]-5,begin[0]+5,begin[1]+5, fill="green")
            #self.cv.create_rectangle(xo,yo,xo+20,yo+20, fill="blue")
            #self.cv.create_rectangle((xo+self.img.width())-20,(yo + self.img.height())-20,xo+self.img.width(),yo+self.img.height(), fill="red")
            print(begin, "Click detected did nothing!")
            return None
        else:
            tl = [min(begin[i],end[i]) for i, j in enumerate(begin)]
            br = [max(begin[i],end[i]) for i, j in enumerate(begin)]
        ################
        # top edge
        self.create_rectangle(0, 0, self.cv.width, tl[1], fill=self.fill, outline=self.outline, tags=("del"), alpha=self.alpha)
        # left edge
        self.create_rectangle(0, tl[1], tl[0], br[1], fill=self.fill, outline=self.outline, tags=("del"), alpha=self.alpha)
        # right edge
        self.create_rectangle(br[0], tl[1], self.cv.width, br[1], fill=self.fill, outline=self.outline, tags=("del"), alpha=self.alpha)
        # bottom edge
        self.create_rectangle(0, br[1], self.cv.width, self.cv.height, fill=self.fill, outline=self.outline, tags = ("del"), alpha=self.alpha)
        #centre
        self.cv.create_rectangle(tl[0],tl[1],br[0],br[1], fill="", outline=self.centre, tags = ("del"))
        ###############################
        #print("tl", tl,'\n xo yo', xo,yo, '\n imgorigin', self.imgorigin, '\n cv w', self.cv.width, '\n cv h', self.cv.height, '\n img w', self.img.width(), '\n img h', self.img.height())
        # tl[0] is top left x, tl[1] is top left y, br[0] is bottom right x, br[1] is bottom right y
        # xo and yo are the images offset from the origin of the window
        self.cropdim = ((tl[0] - xo, tl[1] - yo, br[0] - xo, br[1] - yo))
        self.cropdim = [int(i)*(1/self.scale) for i in self.cropdim]  # if the image has been scaled, fix the crop dims to account for the scale, yes i know this list concat shouldnt work but it does, dont question it
        self.canCrop = True
        print("done")

    def open_img(self, name=None, event=''):
        # Opens a new image, sets name
        # Select the Imagename  from a folder 
        if name == None:
            self.name = filedialog.askopenfilename(title ='Open')
        else:
            self.name = name #+ ' '
        try:
            self.delcounter = 0
            # opens the 
            print("open_img",self.name)
            #self.folder = self.name[:self.name.rfind(os.sep)]
            self.path, self.folder, self.name = handle_path(self.name)
            print("Folder", self.folder)
            self.scan_folder()
            self.pimg = Image.open(self.path)
            self.pimg = self.pimg.convert('RGBA')
            #imdims    = (self.pimg.width + self.offset[0], self.pimg.height + self.offset[1])
            #self.fix_size(imdims)
            self.root.state("zoomed")
            # PhotoImage class is used to add image to widgets, icons etc
            self.draw_image(self.pimg)
            self.oimg  = self.img
            self.opimg = self.pimg
            self.root.title("hamcrop " + self.name)
            self.slidrot.set(0)
            #if self.fr == True:
            #    self.restore()
            #    self.fr = False
            self.rotate_image(1)
            self.rotate_image(0)

        except FileNotFoundError as e:
            print("open_img FileNotFound Error", e, '\nname', name, '\nself.name', self.name, 'self\nself.folder', self.folder, '\nself.path', self.path, '\nfr', str(self.fr))
            return None

    def restore(self, event=''):
        # The CTRL Z Binding, reload original image
        self.cv.delete('all')
        self.degrees = 0
        self.slidrot.set(0)
        try:
            self.draw_image(self.opimg)
        except AttributeError as e:
            print("Restore Attribute Error, probably caused by clicking the button without an image loaded", e)
            return None

    def scaler(self, img):
        # displayed pics all go through the scaler, background pics do not
        # if the img width is greater than the canvas
        # I changed it to fullscreen always because fuck this canvas
        # then we need to scale down
        # if the image is 2000 wide you need to divide 1920/2000 to get the scale of 0.96
        if img.width > self.root.winfo_screenwidth() - self.offset[0]:
            self.scale = (self.root.winfo_screenwidth() - self.offset[0])/img.width
        elif img.height > self.root.winfo_screenheight() - self.offset[1]:
            self.scale = (self.root.winfo_screenheight() - self.offset[1])/img.height 
        else:
            self.scale = 1
        img = img.resize((int(img.width*self.scale), int(img.height*self.scale)), Image.ANTIALIAS)
        print("scale:", self.scale)
        print('ran')
        return img # return scaled object

    def scan_folder(self):
        # LS a folder and store a list of all the files found with a given extension
        self.imlist = []
        for i in os.listdir(self.folder):
            if i[i.rfind('.'):].lower() in formats:
                self.imlist.append(os.sep.join([self.folder, i]))
        self.imlower = [i.lower() for i in self.imlist]
        for i, j in enumerate(self.imlist):
            print(i,j)
        self.index.set(' / '.join([str(self.imlower.index(self.path.lower())+1), str(len(self.imlist))]))

    def open_prev(self, event=''):
        # wrapper for bind
        print("Prev")
        try:
            self.open_img(self.imlist[self.imlower.index(self.path.lower())-1])
        except AttributeError as e:
            print("open_prev Attribute Error, probably caused by pressing the button without an image loaded", e)
            return None
        except TypeError as e:
            print("open_prev Type Error, current image path is not in imlist", e)
            return None

    def open_next(self, event=''):
        #wrapper for bind, this one needs more code because you can have negative list indicies but you cannot exceed list length
        print("next")
        try:
            current = self.imlower.index(self.path.lower())
            if current + 1 == len(self.imlist):
                self.open_img(self.imlist[0])
            else:
                self.open_img(self.imlist[current + 1])
        except AttributeError as e:
            print("open_next Attribute Error, probably caused by pressing the button without an image loaded", e)
            return None
        except TypeError as e:
            print("open_next Type Error, current image path is not in imlist", e)
            return None

    def open_paste(self, event=''):
        # Opens an image from the clipboard
        # https://stackoverflow.com/a/7045677/992644
        path = ''
        try:
            im = ImageGrab.grabclipboard()
            print("Clipboard does contain an image.")
        except:
            print("Clipboard did not contain an image.")
            return None
        path = os.sep.join([self.spath,'clipboard.png'])
        print(path)
        im.save(path)
        print('clipboard saved')
        self.open_img(path)

    def handle_enter(self, event):
        # Crops if crop is possible otherwise saves
        print("Can crop1 " + str(self.canCrop))
        if self.canCrop == True:
            self.crop()
        else:
            self.overwrite()

    def open_folder(self, event=''):
        path = os.path.realpath(self.folder)
        print(path)
        print(self.folder)
        os.startfile(path)

    def save_img(self, dest = ''):
        #overwrite options
        try:
            if dest == '':
                dest = filedialog.asksaveasfilename(title="Save", defaultextension =".jpg",filetypes=[("All Files","*.*"),("JPEG","*.jpeg"),("Portable Network Graphic","*.png")])
            if not dest.split('.')[-1].lower() == '.png': # If it doesnt support an alpha channel then convert to RGB
                self.pimg = self.pimg.convert('RGB')
            self.pimg.save(dest)
            print(dest)
            self.root.title("hamcrop " + dest + " Saved!")
        except AttributeError as e:
            #Display Fail message
            self.root.title("hamcrop DID NOT SAVE")
            print("save_img Attribute Error, probably caused by closing the save dialogue without saving anything", e)
            return None

    def save_clipboard(self, event=''):
        # https://stackoverflow.com/a/21320589/992644
        HGLOBAL = HANDLE
        SIZE_T = c_size_t
        GHND = 0x0042
        GMEM_SHARE = 0x2000

        GlobalAlloc = windll.kernel32.GlobalAlloc
        GlobalAlloc.restype = HGLOBAL
        GlobalAlloc.argtypes = [UINT, SIZE_T]

        GlobalLock = windll.kernel32.GlobalLock
        GlobalLock.restype = LPVOID
        GlobalLock.argtypes = [HGLOBAL]

        GlobalUnlock = windll.kernel32.GlobalUnlock
        GlobalUnlock.restype = BOOL
        GlobalUnlock.argtypes = [HGLOBAL]

        CF_DIB = 8

        OpenClipboard = windll.user32.OpenClipboard
        OpenClipboard.restype = BOOL 
        OpenClipboard.argtypes = [HWND]

        EmptyClipboard = windll.user32.EmptyClipboard
        EmptyClipboard.restype = BOOL
        EmptyClipboard.argtypes = None

        SetClipboardData = windll.user32.SetClipboardData
        SetClipboardData.restype = HANDLE
        SetClipboardData.argtypes = [UINT, HANDLE]

        CloseClipboard = windll.user32.CloseClipboard
        CloseClipboard.restype = BOOL
        CloseClipboard.argtypes = None

        #################################################
        image  = self.pimg
        #output = StringIO()
        output = BytesIO()
        image.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()

        hData = GlobalAlloc(GHND | GMEM_SHARE, len(data))
        pData = GlobalLock(hData)
        memmove(pData, data, len(data))
        GlobalUnlock(hData)

        OpenClipboard(None)
        EmptyClipboard()
        SetClipboardData(CF_DIB, pData)
        CloseClipboard()

    def overwrite(self, event=''):
        # wrapper for save_img
        try:
            #dest = r'/'.join([self.folder, self.name])
            self.save_img(self.name)
        except AttributeError as e:
            print("Overwrite Attribute Error, probably caused by clicking the button without an image loaded", e)
            return None

    def delete(self, event = ''):
        if self.delcounter == 1:
            os.remove(self.name)
            self.delcounter = 0
            self.btn7 = Button(self.cv, text ='Delete File', command = self.delete) .grid(row = 1, column = 9)
            self.open_next()
        else:
            self.delcounter +=1
            self.btn7 = Button(self.cv, text ='Delete File', command = self.delete, bg = 'red') .grid(row = 1, column = 9)

    def crop(self, event=''):
        if self.canCrop == True:
            self.canCrop = False
            #with Image.open(self.name) as im:
            #print('crop dims (first two needs to be low positive numbers)',self.cropdim, len(self.cropdim), self.img.width(), self.img.height())
            self.cv.delete('all')
            self.pimg = self.pimg.crop(self.cropdim)
            self.draw_image(self.pimg)

    def rotate_image(self, degrees, event = ''):
        self.cv.delete('all')
        try:
            #print(degrees)
            #self.single  = Image.open('blue.png')
            self.pimg = self.opimg.rotate(self.degrees-int(degrees), expand=True)
            self.img  =  self.add_alpha_bg(self.pimg)
            self.draw_image(self.pimg)
        except AttributeError as e:
            print("Rotate Image Attribute Error, probably caused by clicking the button without an image loaded", e)
            return None

    def rot_90(self, event=''):
        self.slidrot.set(0)
        self.degrees += 90
        self.rotate_image(0)

    def add_alpha_bg(self, dims):
        #doesnt scale, would be nice to have a scaleable solution but it doesnt work and this is already slow enough
        size = (dims.width, dims.height)
        #wunit = int(size[0]/single.width)
        #hunit = int(size[1]/single.height)
        #print("size", wunit, '\nwunit', wunit, '\nhunit', hunit)
        ab   = Image.new('RGBA', size)
        #for y in range(hunit+1):
            # while img.height is less than size[1]
        #    for x in range(wunit+1):
        #        ab.paste(single, (ab.width, ab.height))
        #print('alpha_bg',wunit, hunit, dims.width, dims.height)
        ab.paste(self.single,(0,0))
        ab.paste(dims,(0,0),dims)
        return ab

    def cleanup(self):
        for file in tempfiles:
            try:
                os.remove(os.sep.join([self.spath, file]))
            except FileNotFoundError as e:
                print('Failed to remove {}, it probably doesnt exist\n'.format(file), e)
                continue
            except:
                print('Failed to remove {}, but it does exist\n'.format(file))
                continue
            print('Successfully removed {}'.format(file))

    def run(self):
        # tag all of the self.cv widgets
        self.root.mainloop()

if __name__ == "__main__":
    path = None
    #path = r"D:\Users\Michael\OneDrive\Pictures\bark to the future.png"
    try:
        path = sys.argv[1]
        print("Loaded ",sys.argv[1])
        #app = main(sys.argv[1])
    except:
        print("Loaded without argv")
        # If you see two windows then its because this triggered failed
    app = main(path)
    app.run()
    register(app.cleanup)
