from Tkinter import Tk, BOTH, W, N, E, S, ALL, Canvas, Toplevel, Entry, Frame, Button, Label
import time
import random

class App(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.parent = parent
        self.rect=dict()
        self.max_width = 600
        self.max_height = 600
        self.initDimensions()
        self.initUI()
        self.reset_canvas()
        for i in range(10):
            self.updateCanvas()
        for i in range(100):
            self.newUpdate()
            self.canvas.update_idletasks()

    def initDimensions(self):
        self.canvas_width = self.max_width
        self.canvas_height = self.max_height
        self.rows = 44
        self.cols = 44
        # self.h = 1;
        self.cellwidth = self.canvas_width/self.cols
        self.cellheight = self.canvas_height/self.rows
        print self.cellheight,self.cellwidth

    def updateDimensions(self,r,c,y=1):
        self.rows = r
        self.cols = c

        self.cellwidth = self.max_width/self.cols
        self.cellheight = self.max_height/self.rows
        if(self.cellwidth<=self.cellheight):
            self.cellheight = self.cellwidth
        else:
            self.cellwidth = self.cellheight
        self.canvas_height = self.rows * self.cellheight
        self.canvas_width = self.cols * self.cellwidth

    def initUI(self):
        self.parent.title("Test")
        self.pack(fill=BOTH, expand=0)
        area = Frame(self, width=500, height=500, borderwidth = 2, relief = 'sunken')
        area.grid(row=1, column=0, columnspan=11, rowspan=4,
            padx=5, sticky=E+W+S+N)
        # self.updateDimensions(10, 70)
        self.canvas = Canvas(area, bg='white', width=self.canvas_width, height=self.canvas_height)
        self.canvas.pack()
        # self.rowconfigure(0, pad =10)
        # self.rowconfigure(1, pad =10)

    def reset_canvas(self):
        self.canvas.delete(ALL)
        for col in range(self.cols):
            for row in range(self.rows):
                x1 = col * self.cellwidth
                y1 = row * self.cellheight
                x2 = x1 + self.cellwidth
                y2 = y1 + self.cellheight
                self.rect[self.rows - row - 1,col] = self.canvas.create_rectangle(x1,y1,x2,y2, fill="red", tags="rect", outline = 'black', width = 1)



    def newUpdate(self):
        start = time.clock()
        self.canvas.delete(ALL)
        self.rect=dict()
        t = time.clock()
        a = [random.randint(0, self.rows-1) for i in range(500)]
        b = [random.randint(0, self.cols-1) for i in range(500)]
        t1 = time.clock()
        # print 'Random: ', time.clock() - t
        for (row,col) in zip(a,b):
                x1 = col * self.cellwidth
                y1 = row * self.cellheight
                x2 = x1 + self.cellwidth
                y2 = y1 + self.cellheight
                if (row,col) not in self.rect:
                    self.rect[row,col] = self.canvas.create_rectangle(x1,y1,x2,y2, fill="red", tags="rect", outline = 'black', width = 0)

        # print 'Time : ', time.clock() - start - (t1-t)
        # print 'Size of data(2):', len(self.rect)
        # print a
        # print b


    def updateCanvas(self):
        start = time.clock()
        for col in range(self.rows):
            for row in range(self.cols):
                self.canvas.itemconfig(self.rect[row,col],fill='white')
        # print 'Time2 : ', time.clock() - start
        # print 'Size of data(1): ', len(self.rect)


def main():

    root = Tk()
    app = App(root)
    root.geometry("610x610+100+200")

    root.mainloop()


if __name__ == '__main__':
    main()