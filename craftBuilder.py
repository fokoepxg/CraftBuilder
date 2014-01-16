from Tkinter import Tk, BOTH, W, N, E, S, ALL, Canvas, Toplevel, Entry, Frame, Button, Label
from tkFileDialog import askopenfilename, asksaveasfilename
from ttk import Checkbutton, Combobox,Style
import tkMessageBox
import sys
import math
import cPickle as pickle
import sqlite3 as lite
import socket
import time
import sys
import urllib
import urllib2
import os
from colors import COLORS

#################################################################################################
# DATA THAT NEEDS TO BE FILLED IN
HOST = 'XXXXXXXX'
PORT = 0000
USERNAME = 'XXXX'
TOKEN = None # can be left blank, if blank it will access from auth.db
DB_DIR = os.path.dirname(os.path.realpath(__file__)) + '/' # Change if database is not in the same directory as this file.
                                                                                            # Backslah might need to be changed in windows (not sure)
#################################################################################################

DB = 'cache.' + str(HOST) + '.' + str(PORT) + '.db'
db_name = DB_DIR + DB


#################################################################################################
# SOME DEFAULTS FOR DRAWING CAN BE CHANGED IF NEEDED
OVERLAYWIDTH = 3
DEFAULTWIDTH = 1
NUMPERSEC = 300 # for sending build messages to server, to ensure server is not overloaded
#################################################################################################

class HelpWindow(object):
    def __init__(self,master, title):
        self.top=Toplevel(master)
        self.value = ''
        self.top.geometry("300x300+300+300")
        self.l=Label(self.top,text=title)
        self.l.pack()
        self.b=Button(self.top,text='Ok',command=self.cleanup)
        self.b.pack()
        self.b.focus()
    def cleanup(self):
        self.top.destroy()

class popupWindow(object):
    def __init__(self,master, title):
        self.top=Toplevel(master)
        self.value = ''
        self.top.geometry("+300+300")
        self.l=Label(self.top,text=title)
        self.l.pack()
        self.e=Entry(self.top)
        self.e.pack()
        self.b=Button(self.top,text='Ok',command=self.cleanup)
        self.b.pack()
        self.e.focus()
    def cleanup(self):
        self.value=self.e.get()
        self.top.destroy()

class Client(object):
    def __init__(self, host=HOST, port=PORT):
        # self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.conn.connect((host, port))
        self.nicks = dict()
        self.data = ''
    def connect(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((HOST, PORT))
    def close(self):
        self.conn.shutdown(socket.SHUT_RDWR)
        self.conn.close()
    def regis(self):
        global TOKEN
        if TOKEN is not None:
            values = {'username': USERNAME, 'identity_token': TOKEN}
        else:
            qs = "select * from identity_token where username==\"" + USERNAME + '\";'
            con = lite.connect(DB_DIR + 'auth.db')
            cur = con.cursor()
            cur.execute(qs)
            data = cur.fetchone()
            print data
            sys.stdout.flush()
            if data is not None:
                TOKEN = data[1]
                print USERNAME, TOKEN
            else:
                return 0
            values = {'username': USERNAME, 'identity_token': TOKEN}
        self.connect()
        url = 'https://craft.michaelfogleman.com/api/1/identity'
        user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
        headers = { 'User-Agent' : user_agent }
        try:
            data = urllib.urlencode(values)
            req = urllib2.Request(url, data,headers)
            response = urllib2.urlopen(req)

            if (response.code == 200):
                auth_token = response.read()
                self.conn.send('A,' + USERNAME + ',' + auth_token + '\n')
                return 1
            else:
                return 0
        except urllib2.HTTPError:
            print 'HTTP Error. Not authenticated'
            return 0

    def recv_data(self):
        self.data = self.data + self.conn.recv(1024)
        self.data = ''

    def read_signs(self, x1, y1, z1, x2, y2, z2, db_name):
        qs = "select * from sign where x between %s and %s and y between %s and %s and z between %s and %s;"\
                %(str(x1),str(x2), str(y1), str(y2), str(z1), str(z2))
        con = None
        try:
            con = lite.connect(db_name)
            cur = con.cursor()
            cur.execute(qs)
            data = cur.fetchall()
            sys.stdout.flush()
        except RuntimeError:
            pass
        sign_list = list()

        for y in range(0,int(y2)-int(y1)+1):
            sign_list.append(dict())

        for row in data:
            if (row[2]-int(x1),row[4]-int(z1)) in sign_list[row[3]-int(y1)]:
                sign_list[row[3]-int(y1)][row[2]-int(x1),row[4]-int(z1)][int(row[5])] = row[6]
            else:

                sign_list[row[3]-int(y1)][row[2]-int(x1),row[4]-int(z1)] = [-1,-1,-1,-1,-1,-1,-1,-1]
                sign_list[row[3]-int(y1)][row[2]-int(x1),row[4]-int(z1)][int(row[5])] = row[6]
            sys.stdout.flush()

        return sign_list

    def read_db(self, x1, y1, z1, x2, y2, z2, db_name):
        qs = "select * from block where x between %s and %s and y between %s and %s and z between %s and %s;"\
                %(str(x1),str(x2), str(y1), str(y2), str(z1), str(z2))
        con = None
        try:
            con = lite.connect(db_name)
            cur = con.cursor()
            cur.execute(qs)
            data = cur.fetchall()
        except RuntimeError:
            pass
        copy_list = list()
        for y in range(0,int(y2)-int(y1)+1):
            copy_list.append(dict())

        for row in data:
            if row[5] < 0 or row[5] == 0:
                pass
            else:
                if (row[2]-int(x1),row[4]-int(z1)) not in copy_list[row[3]-int(y1)]:
                    copy_list[row[3]-int(y1)][row[2]-int(x1),row[4]-int(z1)] = row[5]
        return copy_list


    def client_send(self, x, y, z, w):
        qs = "B," + str(int(round(x))) + ',' + str(int(round(y))) + ',' + str(int(round(z))) + ',' + str(int(w)) + '\n'
        self.conn.send(qs)

    def client_send_sign(self, x, y, z, f, sign_text):
        qs = "S," + str(int(round(x))) + ',' + str(int(round(y))) + ',' + str(int(round(z))) + ',' + str(int(f)) + ',' + sign_text + '\n'
        self.conn.send(qs)


class App(Frame):

    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.levels = list()
        self.signs = list()
        self.items = [i for i in range(1,64)]
        self.items.remove(16)
        self.current_item = 0
        self.parent = parent
        self.max_width = 600
        self.max_height = 600
        self.client = Client()
        self.initDimensions()
        self.initUI()
        self.reset_canvas()

    def connect(self):

        res = self.client.regis()
        if(res == 1):
            time.sleep(1)
            self.connect_button.config(state = 'disabled')
            self.disconnect_button.config(state = 'normal')

    def disconnect(self):
        self.client.close()
        self.connect_button.config(state = 'normal')
        self.disconnect_button.config(state = 'disabled')


    def initDimensions(self):
        self.canvas_width = self.max_width
        self.canvas_height = self.max_height
        self.rows = 10
        self.cols = 10
        # self.h = 1;
        self.cellwidth = self.canvas_width/self.cols
        self.cellheight = self.canvas_height/self.rows
        self.initData()

    def add_new_level(self):
        temp=dict()
        temp2 = dict()
        self.levels.append(temp)
        self.signs.append(temp2)

    def insert_new_level(self, loc):
        temp=dict()
        temp2 = dict()
        self.levels.insert(loc,temp)
        self.signs.insert(loc,temp2)

    def initData(self):
        self.levels = list()
        self.signs = list()
        self.rect = dict()
        self.rect_text = dict()
        self.curr_level = 0
        self.overlay_level = 0
        self.overlayToggle = False
        self.levels.append(dict())
        self.signs.append(dict())
        self.current_item = 1


    def reset_canvas(self):
        self.canvas.delete(ALL)
        count = 0
        for col in range(self.cols):
            for row in range(self.rows):
                x1 = col * self.cellwidth
                y1 = row * self.cellheight
                x2 = x1 + self.cellwidth
                y2 = y1 + self.cellheight
                self.rect[self.rows - row - 1,col] = self.canvas.create_rectangle(x1,y1,x2,y2, fill="white", tags="rect", outline = 'black', width = DEFAULTWIDTH)
                self.rect_text[self.rows - row - 1,col] = self.canvas.create_text((x1+x2)/2,(y1+y2)/2, text = '', font=('verdana', 7))
        self.parent.title("Craft Builder: Dimensions: " + str(self.rows) + 'x' + str(len(self.levels)) +'x' + str(self.cols))

    def redraw_overlay(self):
        if self.overlayToggle == 1:
            for col in range(self.cols):
                for row in range(self.rows):
                    if (self.rows - row - 1,col) in self.levels[self.overlay_level]:
                        self.canvas.itemconfig(self.rect[self.rows - row - 1,col], width = OVERLAYWIDTH)
                    else:
                        self.canvas.itemconfig(self.rect[self.rows - row - 1,col], width = DEFAULTWIDTH)
        else:
            for col in range(self.cols):
                for row in range(self.rows):
                    self.canvas.itemconfig(self.rect[self.rows - row - 1,col], width = DEFAULTWIDTH)

    def redraw_level(self):
        start = time.clock()
        count = 0
        for col in range(self.cols):
            for row in range(self.rows):
                if (self.rows - row - 1,col) in self.levels[self.curr_level]:
                    count = count + 1
                    val = self.levels[self.curr_level][self.rows - row - 1,col]

                    self.canvas.itemconfig(self.rect[self.rows - row - 1,col],fill=COLORS[val],width = DEFAULTWIDTH)
                    self.canvas.itemconfig(self.rect_text[self.rows - row - 1,col], text = self.levels[self.curr_level][self.rows - row - 1,col])
                else:
                    self.canvas.itemconfig(self.rect[self.rows - row - 1,col],fill="white",width = DEFAULTWIDTH)
                    self.canvas.itemconfig(self.rect_text[self.rows - row - 1,col], text = '')

        self.parent.title("Craft Builder: Dimensions: " + str(self.rows) + 'x' + str(len(self.levels)) +'x' + str(self.cols))
        self.redraw_overlay()
        print 'Time for redraw: ', time.clock() - start
        print 'Number of blocks: ', count
        sys.stdout.flush()

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
        self.canvas.config(width = self.canvas_width, height = self.canvas_height)

        self.canvas.delete(ALL)
        self.initData()
        for i in range(y-1):
            self.levels.append(dict())
            self.signs.append(dict())

    def altMenu(self, event):
        # print "Keycode:", event.keycode, "State:", event.keysym, event.type

        if event.type == '2':
            self.altAction = True
            self.clear_button.config(text = 'Multi Clear', bg = 'white')
            self.delete_button.config(text = 'Multi Delete', bg='white')
            self.insert_button.config(text = 'Multi Insert', bg='white')
            self.new_level_button.config(text = 'Multi New', bg = 'white')
        elif event.type == '3':
            defaultbg = self.parent.cget('bg')
            self.altAction = False
            self.clear_button.config(text = 'Clear Level', bg = defaultbg)
            self.delete_button.config(text = 'Delete', bg = defaultbg)
            self.insert_button.config(text = 'Insert', bg = defaultbg)
            self.new_level_button.config(text = 'New Level', bg = defaultbg)
        sys.stdout.flush()

    def initUI(self):

        self.altAction = False
        self.parent.title("Craft Builder")
        self.style = Style()
        self.style.theme_use("default")
        self.pack(fill=BOTH, expand=0)

        self.columnconfigure(0, pad = 7)
        self.columnconfigure(1, pad = 7)
        self.columnconfigure(2, pad = 7)
        self.columnconfigure(9, weight =1 )
        self.columnconfigure(3, pad=7)
        self.columnconfigure(5, pad=7)

        self.rowconfigure(1, weight=1)
        self.rowconfigure(5, pad=7)
        self.rowconfigure(6, pad=7)
        self.rowconfigure(7, pad=7)
        self.rowconfigure(8, pad=7)

        area = Frame(self, width=500, height=500, borderwidth = 2, relief = 'sunken')
        area.grid(row=1, column=0, columnspan=11, rowspan=4,
            padx=5, sticky=E+W+S+N)

        self.canvas = Canvas(area, bg='white', width=self.canvas_width, height=self.canvas_height)

        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.callbackLeftClick)
        self.canvas.bind("<B1-Motion>", self.callbackLeftClick)
        self.canvas.bind("<Button-3>", self.callbackRightClick)
        self.canvas.bind("<B3-Motion>", self.callbackRightClick)
        self.canvas.bind("<Button-5>", self.scrollWheel)
        self.canvas.bind("<Button-4>", self.scrollWheel)
        self.parent.bind("<Shift_L>", self.altMenu)
        self.parent.bind("<KeyRelease-Shift_L>", self.altMenu)


        self.new_button = Button(self, text="New", command = self.onNew, width = 6)
        self.new_button.grid(row=5, column=0)

        save_button = Button(self, text="Save", command = self.onSave, width = 6)
        save_button.grid(row=6, column=0)

        load_button = Button(self, text="Load", command = self.onLoad, width = 6)
        load_button.grid(row=7, column=0)

        self.connect_button = Button(self, text="Connect", command = self.connect, width = 6)
        self.connect_button.grid(row=8, column=0)

        self.clear_button = Button(self, text="Clear Level", command = self.onClear, width =8)
        self.clear_button.grid(row=5, column=1)

        self.delete_button = Button(self, text="Delete Level", command = self.onDelete, width =8)
        self.delete_button.grid(row=6, column=1)

        self.insert_button = Button(self, text="Insert Level", command = self.onInsertLevel, width =8)
        self.insert_button.grid(row=7, column=1)

        self.disconnect_button = Button(self, text="Disconnect", command = self.disconnect, width = 8)
        self.disconnect_button.grid(row=8, column=1)
        self.disconnect_button['state'] = 'disabled'

        lbl_a = Label(self, text="Curr. Level", font=("Verdana", 10))
        lbl_a.grid(row = 5, column = 2)

        lbl_b = Label(self, text="Overlay Level", font=("Verdana", 10))
        lbl_b.grid(row = 6, column = 2)

        copy_level_button = Button(self, text="Copy overlay level", command = self.onCopy, width = 12)
        copy_level_button.grid(row=7, column=2, columnspan=1)

        load_world_button = Button(self, text="Load from world", command = self.onLoadFromWorld, width = 12)
        load_world_button.grid(row=8, column=2)

        self.currLevelCombo = Combobox(self, values = range(len(self.levels)), width = 5, state = 'readonly')
        self.currLevelCombo.grid(row = 5, column = 3)
        self.currLevelCombo.bind("<<ComboboxSelected>>", self.currLevelChooser)
        self.currLevelCombo.set(0)

        self.overlayLevelCombo = Combobox(self, values = range(len(self.levels)), width = 5, state = 'readonly')
        self.overlayLevelCombo.grid(row = 6, column = 3)
        self.overlayLevelCombo.bind("<<ComboboxSelected>>", self.overlayLevelChooser)
        self.overlayLevelCombo.set(0)


        self.new_level_button = Button(self, text="New Level", command = self.onNewLevel, width = 12)
        self.new_level_button.grid(row=7, column=3,columnspan=1)

        paste_button = Button(self, text="Paste in world", command = self.onPaste, width = 12)
        paste_button.grid(row=8, column=3)

        lbl_d = Label(self, text="Item", font=("Verdana", 10))
        lbl_d.grid(row = 5, column = 4)

        self.toggle = Checkbutton(self, text="Overlay Toggle", command = self.onToggle)
        self.toggle.grid(row=6, column=4)

        rotate_button = Button(self, text="Rotate", command = self.onRotate, width = 12)
        rotate_button.grid(row=7, column=4,columnspan=1)

        paste_sign_button = Button(self, text="Paste Signs", command = self.onPasteSign, width = 12)
        paste_sign_button.grid(row=8, column=4)

        self.itemCombo = Combobox(self, values = self.items, width = 5, state = 'readonly')
        self.itemCombo.grid(row = 5, column = 5)
        self.itemCombo.bind("<<ComboboxSelected>>", self.itemChooser)
        self.itemCombo.set(1)
        self.current_item = 1
        self.lbl_e = Label(self, text="", font=("Verdana", 8), width = 12, relief = 'ridge')
        self.lbl_e.grid(row = 6, column = 5)

        add_geo_button = Button(self, text="Add Geometry", command = self.addGeo, width = 12)
        add_geo_button.grid(row=8, column=5)

        try:
            import builder
        except ImportError:
            add_geo_button.config(state = 'disabled')

    def scrollWheel(self, event):
        if event.num == 5:
            #scroll down
            if self.curr_level==len(self.levels) -1:
                pass
            else:
                self.curr_level = self.curr_level + 1
                self.currLevelCombo.set(self.curr_level)
                self.redraw_level()
        else:
            #scroll up
            if self.curr_level == 0:
                pass
            else:
                self.curr_level = self.curr_level - 1
                self.currLevelCombo.set(self.curr_level)
                self.redraw_level()

    def onClear(self):
        if tkMessageBox.askquestion('Clear', "Clear Level: " + str(self.curr_level)) == 'yes':
            self.levels[self.curr_level] = dict()
            self.signs[self.curr_level] = dict()
            self.redraw_level()
        else:
            pass

    def onDelete(self):
        if tkMessageBox.askquestion('Delete', "Delete Level: " + str(self.curr_level)) == 'yes':
            if len(self.levels) == 1:
                self.onClear()
            else:
                self.levels.pop(self.curr_level)
                self.signs.pop(self.curr_level)
                self.currLevelCombo.config(values = range(len(self.levels)))
                self.overlayLevelCombo.config(values = range(len(self.levels)))

                if self.overlayToggle == 1:
                    self.toggle.invoke()
                    self.overlayToggle = 0

                if self.curr_level != 0:
                    self.curr_level = self.curr_level - 1
                    self.currLevelCombo.set(self.curr_level)
                else:
                    self.currLevelCombo.set(self.curr_level)
                self.redraw_level()

    def addGeo(self):
        self.w=popupWindow(self,title = "Enter Command: help for Help")
        self.wait_window(self.w.top)

        try:
            c = self.w.value.split(' ')
            if c[0] == 'help':
                self.h = HelpWindow(self, title = 'Enter command followed by args seperated by spaces\n' +
                                                                    'Available commands (sphere, pyramid, cuboid)\n' +
                                                                    '1.   pyramid x1 x2 y z1 z2 fill(0/1) \n' +
                                                                    '2.   sphere cx cy cz r fill(0/1) \n' +
                                                                    '4.   circle_x x y z r fill(0/1) \n' +
                                                                    '5.   circle_y x y z r fill(0/1) \n' +
                                                                    '6.   circle_z x y z r fill(0/1) \n' +
                                                                    '7.   cylinder_x x1 x2 y z r fill(0/1) \n' +
                                                                    '8.   cylinder_y x y1 y2 z r fill(0/1) \n' +
                                                                    '9.   cylinder_z x y z1 z2 r fill(0/1) \n' +
                                                                    '10. cuboid x1 x2 y1 y2 z1 z2 fill(0/1) \n' )
            elif c[0] == 'sphere':
                if len(c) - 1 == 5:
                    result = builder.sphere(int(c[1]),int(c[2]),int(c[3]),int(c[4]),int(c[5]))
                    for i in result:
                        print i
                        if i[1] < len(self.levels) and i[1] >=0:
                            if i[0] < self.rows and i[0] >=0 and i[2] < self.cols and i[2] >=0:
                                self.levels[i[1]][i[0],i[2]] = self.current_item
                    self.redraw_level()

            elif c[0] == 'pyramid':
                if len(c) - 1 == 6:
                    result = builder.pyramid(int(c[1]),int(c[2]),int(c[3]),int(c[4]),int(c[5]),int(c[6]))
                    for i in result:
                        if i[1] < len(self.levels) and i[1] >= 0:
                            if i[0] < self.rows and i[0] >=0 and i[2] < self.cols and i[2] >=0:
                                self.levels[i[1]][i[0],i[2]] = self.current_item
                    self.redraw_level()

            elif c[0] == 'circle_x':
                if len(c) - 1 == 5:
                    result = builder.circle_x(int(c[1]),int(c[2]),int(c[3]),int(c[4]),int(c[5]))
                    for i in result:
                        if i[1] < len(self.levels) and i[1] >= 0:
                            if i[0] < self.rows and i[0] >=0 and i[2] < self.cols and i[2] >=0:
                                self.levels[i[1]][i[0],i[2]] = self.current_item
                    self.redraw_level()
            elif c[0] == 'circle_y':
                if len(c) - 1 == 5:
                    result = builder.circle_y(int(c[1]),int(c[2]),int(c[3]),int(c[4]),int(c[5]))
                    for i in result:
                        if i[1] < len(self.levels) and i[1] >= 0:
                            if i[0] < self.rows and i[0] >=0 and i[2] < self.cols and i[2] >=0:
                                self.levels[i[1]][i[0],i[2]] = self.current_item
                    self.redraw_level()
            elif c[0] == 'circle_z':
                if len(c) - 1 == 5:
                    result = builder.circle_z(int(c[1]),int(c[2]),int(c[3]),int(c[4]),int(c[5]))
                    for i in result:
                        if i[1] < len(self.levels) and i[1] >= 0:
                            if i[0] < self.rows and i[0] >=0 and i[2] < self.cols and i[2] >=0:
                                self.levels[i[1]][i[0],i[2]] = self.current_item
                    self.redraw_level()
            elif c[0] == 'cylinder_x':
                if len(c) - 1 == 6:
                    x1,x2 = sorted([int(c[1]),int(c[2])])
                    result = builder.cylinder_x(x1,x2,int(c[3]),int(c[4]),int(c[5]),int(c[6]))
                    for i in result:
                        if i[1] < len(self.levels) and i[1] >= 0:
                            if i[0] < self.rows and i[0] >=0 and i[2] < self.cols and i[2] >=0:
                                self.levels[i[1]][i[0],i[2]] = self.current_item
                    self.redraw_level()
            elif c[0] == 'cylinder_y':
                if len(c) - 1 == 6:
                    y1,y2 = sorted([int(c[2]),int(c[3])])
                    result = builder.cylinder_y(int(c[1]),y1,y2,int(c[4]),int(c[5]),int(c[6]))
                    for i in result:
                        if i[1] < len(self.levels) and i[1] >= 0:
                            if i[0] < self.rows and i[0] >=0 and i[2] < self.cols and i[2] >=0:
                                self.levels[i[1]][i[0],i[2]] = self.current_item
                    self.redraw_level()
            elif c[0] == 'cylinder_z':
                if len(c) - 1 == 6:
                    z1,z2 = sorted([int(c[3]),int(c[4])])
                    result = builder.cylinder_z(int(c[1]),int(c[2]),z1,z2,int(c[5]),int(c[6]))
                    for i in result:
                        if i[1] < len(self.levels) and i[1] >= 0:
                            if i[0] < self.rows and i[0] >=0 and i[2] < self.cols and i[2] >=0:
                                self.levels[i[1]][i[0],i[2]] = self.current_item
                    self.redraw_level()

            elif c[0] == 'cuboid':
                if len(c) - 1 == 7:
                    result = builder.cuboid(int(c[1]),int(c[2]),int(c[3]),int(c[4]),int(c[5]),int(c[6]),int(c[7]))
                    for i in result:
                        if i[1] < len(self.levels) and i[1] >= 0:
                            if i[0] < self.rows and i[0] >=0 and i[2] < self.cols and i[2] >=0:
                                self.levels[i[1]][i[0],i[2]] = self.current_item
                    self.redraw_level()
                pass
        except RuntimeError:
            pass

    def onPaste(self):
        self.w=popupWindow(self,title = "On world, facing north (i.e x increases ahead of you,\n"+
                                                            "and z increases to your right.\n" +
                                                            "Enter origin point (x y z) seperated by spaces: eg. 12 12 12:")
        self.wait_window(self.w.top)
        data = self.w.value.split(' ')
        try:
            xo = int(data[0])
            yo = int(data[1])
            zo = int(data[2])
            if tkMessageBox.askquestion('Coords', "Is this (x,y,z) correct: " + str(xo) +',' +str(yo) + ',' + str(zo)) == 'yes':
                print 'Pasting'
                count = 0
                for j,i in enumerate(self.levels):
                    for key,value in i.iteritems():
                        xr = int(xo + key[0])
                        yr = int(yo + j)
                        zr = int(zo + key[1])
                        # self.client.client_send(xr,yr,zr,0)
                        if int(value) != 0:
                            self.client.client_send(xr,yr,zr,int(value))
                            count = count + 1
                        if count % NUMPERSEC == 0:
                            time.sleep(1)
            else:
                pass
        except ValueError:
            pass

    def onPasteSign(self):
        self.w=popupWindow(self,title = "Facing north, enter origin point(x y z): eg. 12 12 12:")
        self.wait_window(self.w.top)
        data = self.w.value.split(' ')
        try:
            xo = int(data[0])
            yo = int(data[1])
            zo = int(data[2])
            if tkMessageBox.askquestion('Coords', "Is this (x,y,z) correct: " + str(xo) +',' +str(yo) + ',' + str(zo)) == 'yes':
                print 'Pasting'
                count = 0
                for j,i in enumerate(self.signs):
                    for key,value in i.iteritems():
                        xr = int(xo + key[0])
                        yr = int(yo + j)
                        zr = int(zo + key[1])

                        for num,val in enumerate(value):
                            if val!=-1:
                                # print j,i,num, val
                                self.client.client_send_sign(xr, yr, zr, num, val)
                        sys.stdout.flush()
        except ValueError:
            pass

    def onLoadFromWorld(self):
        self.w=popupWindow(self,title = "Enter bottom left point: (x y z)")
        self.wait_window(self.w.top)
        try:
            [x1,y1,z1] = [int(i) for i in self.w.value.split(' ')]

            self.w=popupWindow(self,title = "Enter top right point: (x y z)")
            self.wait_window(self.w.top)
            [x2,y2,z2] = [int(i) for i in self.w.value.split(' ')]

            x1,x2 =  sorted([x1,x2])
            y1,y2 =  sorted([y1,y2])
            z1,z2 =  sorted([z1,z2])

            if tkMessageBox.askquestion('Coords', "Bottom left: " + str(x1) +',' +str(y1) + ',' + str(z1) + '\n' + \
                "Top right: " + str(x2) +',' +str(y2) + ',' + str(z2)) == 'yes':
                print 'Copying',x1,y1,z1,' to',x2,y2,z2
                data = self.client.read_db(x1,y1,z1,x2,y2,z2, db_name)
                signs = self.client.read_signs(x1,y1,z1,x2,y2,z2, db_name)
                newData = list()

                for i in data:
                    temp = dict()
                    for key,value in i.iteritems():
                        if value != 0:
                            temp[key[0], key[1]] = value
                    newData.append(temp)

                newSignData = list()
                for i in signs:
                    temp = dict()
                    for key,value in i.iteritems():
                        temp[key[0], key[1]] = value
                    newSignData.append(temp)

                if self.overlayToggle == 1:
                    self.toggle.invoke()
                    self.overlayToggle = 0
                self.updateDimensions(x2-x1+1, z2-z1+1, len(newData))
                self.reset_canvas()
                self.levels = newData
                self.signs = newSignData
                sys.stdout.flush()

                self.redraw_level()
                self.currLevelCombo.config(values = range(len(self.levels)))
                self.overlayLevelCombo.config(values = range(len(self.levels)))
        except ValueError:
            pass



    def onCopy(self):
        for col in range(self.cols):
            for row in range(self.rows):
                if (row,col) in self.levels[self.overlay_level]:
                   self.levels[self.curr_level][row,col] = self.levels[self.overlay_level][row,col]
        self.redraw_level()

    def onSave(self):
        filename = asksaveasfilename(parent=self)
        pickle.dump({'Dimensions' : [self.rows,self.cols,len(self.levels)],'Levels' : self.levels, 'Signs' : self.signs}, open(filename, 'wb'))

    def onLoad(self):
        if self.overlayToggle == 1:
            self.toggle.invoke()
            self.overlayToggle = 0

        filename = askopenfilename(parent=self)
        obj = pickle.load(open(filename, 'rb'))
        self.updateDimensions(int(obj['Dimensions'][0]), int(obj['Dimensions'][1]), int(obj['Dimensions'][2]))
        self.reset_canvas()
        self.levels = obj['Levels']

        if 'Signs' in obj:
            self.signs = obj['Signs']
        self.redraw_level()
        self.currLevelCombo.config(values = range(len(self.levels)))
        self.overlayLevelCombo.config(values = range(len(self.levels)))

    def onToggle(self):
        if self.overlayToggle == 0:
            self.overlayToggle =1
            self.redraw_overlay()
        else:
            self.overlayToggle = 0
            self.redraw_overlay()

    def onNewLevel(self):
        self.add_new_level()
        self.currLevelCombo.config(values = range(len(self.levels)))
        self.overlayLevelCombo.config(values = range(len(self.levels)))
        self.redraw_level()

    def onInsertLevel(self):
        self.insert_new_level(self.curr_level)
        self.currLevelCombo.config(values = range(len(self.levels)))
        self.overlayLevelCombo.config(values = range(len(self.levels)))
        self.redraw_level()


    def onRotate(self):
        self.rotatedData = list()
        self.rotatedSignData = list()

        for i in self.levels:
            temp = dict()
            for key,value in i.iteritems():
                xr = (key[0] * math.cos(math.radians(-90)) - (key[1]) * math.sin(math.radians(-90)))
                zr = (key[0] * math.sin(math.radians(-90)) + (key[1]) * math.cos(math.radians(-90)))
                temp[int(math.floor(xr)),int(math.floor(zr))] = value
            self.rotatedData.append(temp)

        sign_map = {0:2, 3:0, 1:3, 2:1, 6:5, 7:6, 4:7, 5:4} #FOR ROTATION CALCULATION
        for i in self.signs:
            temp = dict()
            for key,value in i.iteritems():
                xr = (key[0] * math.cos(math.radians(-90)) - (key[1]) * math.sin(math.radians(-90)))
                zr = (key[0] * math.sin(math.radians(-90)) + (key[1]) * math.cos(math.radians(-90)))
                new_value = [value[sign_map[0]],
                                      value[sign_map[1]],
                                      value[sign_map[2]],
                                      value[sign_map[3]],
                                      value[sign_map[4]],
                                      value[sign_map[5]],
                                      value[sign_map[6]],
                                      value[sign_map[7]]]
                temp[int(math.floor(xr)),int(math.floor(zr))] = new_value
            self.rotatedSignData.append(temp)

        #Moving to origin x,z : 0,0
        self.newData=list()
        self.newSignData=list()
        for i in self.rotatedData:
            temp=dict()
            for key,value in i.iteritems():
                temp[key[0], int(key[1])+int((self.rows-1))] = value
            self.newData.append(temp)
        for i in self.rotatedSignData:
            temp=dict()
            for key,value in i.iteritems():
                temp[key[0], int(key[1])+int((self.rows-1))] = value
            self.newSignData.append(temp)


        temp = self.rows
        self.rows = self.cols
        self.cols = temp

        temp = self.curr_level
        temp2 = self.overlay_level
        temp3 = self.overlayToggle

        self.updateDimensions(self.rows, self.cols,len(self.newData))
        self.reset_canvas()
        self.levels = self.newData
        self.signs = self.newSignData
        self.curr_level = temp
        self.overlay_level = temp2
        self.overlayToggle = temp3
        self.currLevelCombo.config(values = range(len(self.levels)))
        self.overlayLevelCombo.config(values = range(len(self.levels)))
        self.currLevelCombo.set(self.curr_level)
        self.overlayLevelCombo.set(self.overlay_level)
        self.redraw_level()


    def onNew(self):
        if self.overlayToggle == 1:
            self.toggle.invoke()
            self.overlayToggle = 0
        self.w=popupWindow(self,title = "Enter Dimensions in XxZxY format (e.g. 10x20x3)")
        self.wait_window(self.w.top)
        try:
            data = self.w.value.split('x')
            if len(data) == 2:
                self.updateDimensions(int(data[0]), int(data[1]),1)
            else:
                self.updateDimensions(int(data[0]), int(data[1]),int(data[2]))
            # self.initData()
            self.reset_canvas()
            self.currLevelCombo.config(values = range(len(self.levels)))
            self.overlayLevelCombo.config(values = range(len(self.levels)))
        except ValueError:
            pass

    def currLevelChooser(self, event):
        self.curr_level = int(self.currLevelCombo.get())
        self.redraw_level()

    def overlayLevelChooser(self, event):
        self.overlay_level = int(self.overlayLevelCombo.get())
        self.redraw_overlay()

    def itemChooser(self, event):
        self.current_item = int(self.itemCombo.get())

    def callbackLeftClick(self,event):
        col = int(math.floor((event.x)/self.cellwidth))
        row = int(math.floor((event.y)/self.cellheight))
        if (self.rows - row - 1,col) in self.rect:
            self.canvas.itemconfig(self.rect[self.rows - row - 1,col],fill=COLORS[self.current_item])
            self.canvas.itemconfig(self.rect_text[self.rows - row - 1,col], text = str(self.current_item))

        self.levels[self.curr_level][self.rows - row - 1,col] = self.current_item

        if row < self.rows and row >=0 and col < self.cols and col >= 0:
            self.lbl_e.config(text = 'x,y,z: ' + str(self.rows-row-1) + ',' + str(self.curr_level) + ',' + str(col))

    def callbackRightClick(self,event):
        col = int(math.floor((event.x)/self.cellwidth))
        row = int(math.floor((event.y)/self.cellheight))
        if (self.rows - row - 1,col) in self.rect:
            self.canvas.itemconfig(self.rect[self.rows - row - 1,col],fill="white")
            self.canvas.itemconfig(self.rect_text[self.rows - row - 1,col], text = '')

        self.levels[self.curr_level].pop((self.rows - row - 1,col),None)

        if row < self.rows and row >=0 and col < self.cols and col >= 0:
            self.lbl_e.config(text = 'x,y,z: ' + str(self.rows-row-1) + ',' + str(self.curr_level) + ',' + str(col))

def main():

    root = Tk()
    app = App(root)
    root.geometry("700x750+100+200")

    root.mainloop()


if __name__ == '__main__':
    main()