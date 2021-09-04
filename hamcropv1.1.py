import os
import sys
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter.filedialog import askopenfilename, asksaveasfilename
from PIL import Image, ImageTk, ImageFilter, ImageEnhance, ImageOps

#root = Tk()

#root.geometry("500x350")

# a subclass of Canvas for dealing with resizing of windows

formats = ('.gif','.jpg','.png','.jpeg')

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
        self.fill    = "black"
        self.outline = ""
        self.centre  = "magenta"
        self.alpha   = 0.7
        self.stroke  = 5
        self.name    = None
        self.folder  = ''
        self.imlist  = []
        self.begin   = None
        self.degrees = 0
        self.size    = (100,100)
        self.offset  = (0,100)
        self.canCrop = False
        self.scale   = 1
        self.images  = []
        self.counter = 0
        self.slidrot = IntVar()
        myframe      = Frame(self.root)
        myframe.pack(fill=BOTH, expand=YES)
        self.cv = ResizingCanvas(myframe,width=850, height=400, bg="dark grey", highlightthickness=0)
        self.cv.pack(fill=BOTH, expand=YES)
        if not name == None:
            self.open_img(name)
        
    def fix_size(self,size):
        # Check to see if new size is greater than current size
        if size > self.size:
            self.size = size
            # Geometry wants a string like this
            # 100x200
            self.root.geometry("x".join([str(i) for i in self.size]))

    def set_begin(self, event):
        self.begin = event

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

    def create_rectangle(self, x1, y1, x2, y2, **kwargs):
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
        except AttributeError:
            return None
        #rectangles are drawn on self.cv from top left to bottom right
        # we are working with two coordinate systems here, window coordinates and image coordinates
        # xo and yo are the offset of image coords 0,0 and winodw coords 0,0
        xo, yo = [self.cv.width/2  - self.img.width()/2, 
                  self.cv.height/2 - self.img.height()/2] 
        begin  = (self.begin.x, self.begin.y)
        end    = (event.x, event.y)
        #if begin < end:
        #    tl = begin
        #    br = end
        #elif begin > end:
        #    tl = end
        #    br = begin
        if begin == end:
            #self.cv.create_oval(begin[0]-5,begin[1]-5,begin[0]+5,begin[1]+5, fill="green")
            #self.cv.create_rectangle(xo,yo,xo+20,yo+20, fill="blue")
           # self.cv.create_rectangle((xo+self.img.width())-20,(yo + self.img.height())-20,xo+self.img.width(),yo+self.img.height(), fill="red")
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

    def open_img(self, name=None):
        # Opens a new image, sets name
        # Select the Imagename  from a folder 
        if name == None:
            self.name = filedialog.askopenfilename(title ='Open')
        else:
            self.name = name
        try:
            self.counter = 0
            # opens the image
            print("open_img",self.name)
            self.folder = self.name[:self.name.rfind('/')]
            self.scan_folder(self.folder)
            self.pimg = Image.open(self.name)
            imdims    = (self.pimg.width + self.offset[0], self.pimg.height + self.offset[1])
            self.fix_size(imdims)
            # PhotoImage class is used to add image to widgets, icons etc
            self.img   = ImageTk.PhotoImage(self.scaler(self.pimg))
            self.cv.create_image(self.cv.width/2, self.cv.height/2, image=self.img)
            self.oimg  = self.img
            self.opimg = self.pimg
            self.root.title("hamcrop " + self.name)
            self.slidrot.set(0)
        except FileNotFoundError:
            return None

    def scaler(self, img):
        # displayed pics all go through the scaler, background pics do not
        # if the img width is greater than the canvas
        # then we need to scale down
        # if the image is 2000 wide you need to divide 1920/2000 to get the scale of 0.96
        if img.width > self.cv.width:
            self.scale = self.cv.width/img.width
        elif img.height > self.cv.height:
            self.scale = self.cv.height/img.height
        else:
            self.scale = 1
        img = img.resize((int(img.width*self.scale), int(img.height*self.scale)), Image.ANTIALIAS)
        print("scale:", self.scale)
        return img # return scaled object

    def scan_folder(self, folder):
        # LS a folder and store a list of all the files found with a given extension
        self.imlist = []
        for i in os.listdir(folder):
            if i[i.rfind('.'):].lower() in formats:
                self.imlist.append('/'.join([self.folder, i]))
        for i, j in enumerate(self.imlist):
            print(i,j)

    def open_prev(self, event=''):
        # wrapper for bind
        print("Prev")
        try:
            self.open_img(self.imlist[self.imlist.index(self.name)-1])
        except AttributeError:
            return None

    def open_next(self, event=''):
        #wrapper for bind, this one needs more code because you can have negative list indicies but you cannot exceed list length
        print("next")
        try:
            current = self.imlist.index(self.name)
            if current + 1 == len(self.imlist):
                self.open_img(self.imlist[0])
            else:
                self.open_img(self.imlist[current + 1])
        except AttributeError:
            return None

    def open_folder(self, event=''):
        path = os.path.realpath(self.folder)
        print(path)
        print(self.folder)
        os.startfile(path)

    def handle_enter(self, event):
        print("Can crop1 " + str(self.canCrop))
        if self.canCrop == True:
            self.crop()
        else:
            self.overwrite()

    def save_img(self, dest = ''):
        #overwrite options
        try:
            if dest == '':
                dest = filedialog.asksaveasfilename(title="Save", defaultextension =".jpg",filetypes=[("All Files","*.*"),("JPEG","*.jpeg"),("Portable Network Graphic","*.png")])
            self.pimg.save(dest)
            print(dest)
            self.root.title("hamcrop " + dest + " Saved!")
        except AttributeError:
            #Display Fail message
            self.root.title("hamcrop")
            return None

    def overwrite(self, event=''):
        # wrapper for save_img
        try:
            #dest = r'/'.join([self.folder, self.name])
            self.save_img(self.name)
        except AttributeError:
            return None

    def delete(self, event = ""):
        if self.counter == 1:
            os.remove(self.name)
            self.counter = 0
            self.btn7 = Button(self.cv, text ='Delete File', command = self.delete) .grid(row = 1, column = 9)
            self.open_next()
        else:
            self.counter +=1
            self.btn7 = Button(self.cv, text ='Delete File', command = self.delete, bg = 'red') .grid(row = 1, column = 9)

    def crop(self):
        if self.canCrop == True:
            self.canCrop = False
            #with Image.open(self.name) as im:
            #print('crop dims (first two needs to be low positive numbers)',self.cropdim, len(self.cropdim), self.img.width(), self.img.height())
            self.pimg = self.pimg.crop(self.cropdim)
            self.img = ImageTk.PhotoImage(self.scaler(self.pimg))
            self.cv.delete('all')
            self.cv.create_image(self.cv.width/2, self.cv.height/2, image=self.img)

    def rotate_image(self, degrees):
        self.cv.delete('all')
        try:
            print(degrees)
            self.pimg = self.opimg.rotate(self.degrees-int(degrees), expand=True)
            self.img = ImageTk.PhotoImage(self.scaler(self.pimg))
            self.cv.create_image(self.cv.width/2, self.cv.height/2, image=self.img)
        except AttributeError:
            return None

    def rot_90(self, event=''):
        self.cv.delete('all')
        try:
            self.slidrot.set(0)
            #self.degrees += 90
            self.pimg = self.pimg.rotate(int(90), expand=True)
            self.img = ImageTk.PhotoImage(self.scaler(self.pimg))
            self.cv.create_image(self.cv.width/2, self.cv.height/2, image=self.img)
        except AttributeError:
            return None

    def restore(self):
        self.cv.delete('all')
        self.degrees = 0
        self.slidrot.set(0)
        try:
            self.open_img(self.name)
        except AttributeError:
            return None

    def run(self):
        btn0 = Button(self.cv, text ='Open Image',  command = self.open_img)    .grid(row = 1, column = 1)
        btn1 = Button(self.cv, text ='Crop',        command = self.crop)        .grid(row = 1, column = 2)
        btn2 = Button(self.cv, text ='Undo',        command = self.restore)     .grid(row = 1, column = 3)
        btn3 = Button(self.cv, text ='Save As',     command = self.save_img)    .grid(row = 1, column = 4)
        btn4 = Button(self.cv, text ='Overwrite',   command = self.overwrite)   .grid(row = 1, column = 5)
        btn5 = Button(self.cv, text ='+90',         command = self.rot_90)      .grid(row = 1, column = 6)
        slid = Scale(self.cv,  from_=-90, to=90, orient=HORIZONTAL, length = 300, command = self.rotate_image, variable=self.slidrot).grid(row = 1, column = 7)
        btn6 = Button(self.cv, text ='Open Folder', command = self.open_folder) .grid(row = 1, column = 8)
        btn7 = Button(self.cv, text ='Delete File', command = self.delete)      .grid(row = 1, column = 9)

        # bind mouse event with canvas(self.cv)
        #self.cv.bind("<B1-Motion>",     paint)
        self.cv.bind("<ButtonPress>",   self.set_begin)
        self.cv.bind("<ButtonRelease>", self.draw_rect)
        self.root.bind("<Left>",        self.open_prev)
        self.root.bind("<Right>",       self.open_next)
        self.root.bind("<Delete>",      self.delete)
        self.root.bind("<Return>",      self.handle_enter)
        self.root.bind("<Tab>",         self.rot_90)

        # tag all of the self.cv widgets
        self.cv.addtag_all("all")
        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = main('//'.join([os.getcwd(),sys.argv[1]]))
    except:
        app = main()
    app.run()
