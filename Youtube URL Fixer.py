from tkinter import Tk, StringVar, Label, Button, Entry


class main():
    def __init__(self):
        self.w = 50
        self.root = Tk()
        self.root.title("Youtube URL Fixer")
        self.root.geometry('430x60')
        self.tv0 = StringVar(self.root)
        self.tv1 = StringVar(self.root)
        label0 = Label(self.root, text = 'Paste here').grid(row = 1, column = 1)
        label0 = Label(self.root, text = 'Fixed url') .grid(row = 2, column = 1)
        button0 = Button(self.root, text = "Fix url", command = self.fix_url).grid(row = 1, column = 3)
        button0 = Button(self.root, text = "Copy url", command = self.cp).grid(row = 2, column = 3)

    def cp(self, event=''):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.tv1.get())

    def fix_url(self):
        # "https://www.youtube.com/embed/ukKbWoEluLA?rel=0&showinfo=0"
        # https://www.youtube.com/watch?v=ukKbWoEluLA
        url = self.tv0.get()
        if not url == "我想你":
            url = url[url.find('https'):]
            url = url.replace('"','')
            if not 'watch?v=' in url:
                url = url.replace('embed/','watch?v=')
                url = url[:url.rfind('?')]
            self.tv1.set(url)
        else:
            self.tv1.set("我也想你我的爱")
        #return url
    
    def run(self):
        self.field0 = Entry(self.root, width = self.w, textvariable = self.tv0).grid(row = 1, column = 2)
        self.field1 = Entry(self.root, width = self.w, textvariable = self.tv1).grid(row = 2, column = 2)
        self.root.mainloop()


if __name__ == "__main__":
    app = main()
    app.run()

   # C:\Users\predator\AppData\Roaming\Python\Python38\Scripts\pyinstaller.exe "Youtube URL Fixer.py" -F -w


