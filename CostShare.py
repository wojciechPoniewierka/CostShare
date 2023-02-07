# Wojciech Poniewierka, February 2021

# Imports
import pandas as pd
from tkinter import *
from tkinter import filedialog, messagebox
import os
from copy import deepcopy
import numpy as np

# Constants
WIDTH = 900
HEIGHT = 500
WINDOW_SIZE = str(WIDTH) + 'x' + str(HEIGHT)
BACKGROUND_COLOUR = '#3b414a'
TEXT_COLOUR = '#121212'

ROOT = Tk()
ICON = PhotoImage(file='Program_Files/icon.png')
SCREEN_WIDTH = ROOT.winfo_screenwidth()
SCREEN_HEIGHT = ROOT.winfo_screenheight()

FILE = None
TRANSACTIONS = {}
EVENT_SPENT = []
MAX_PEOPLE = 8
MAX_SUBSYSTEMS = 15
CELLS = {}
INIT_BUTTONS = []
FILE_BUTTONS = []


# Functions
def new_file():
    global FILE
    FILE = 'Untitled'
    frame1.place(x=100, y=130)
    label2.place(x=470, y=100)
    label3.place(x=75, y=180)
    make_cells()
    ROOT.title('CostShare - Untitled')
    for val in CELLS.values():
        val.delete(0, END)
    CELLS['cell01'].focus()
    place_buttons('file')


def read_file():
    global INIT_BUTTONS, FILE
    file = filedialog.askopenfilename(initialdir='User_Files',
                                      title='Choose a CostShare CSV file to read',
                                      filetypes=(('CSV files', '*.csv'), ('All files', '*.*')))

    if file.endswith('.csv'):
        FILE = os.path.basename(file)
        cs_data = pd.read_csv(file, index_col=0)
        frame1.place(x=100, y=130)
        label2.place(x=470, y=100)
        label3.place(x=75, y=180)
        make_cells()
        for val in CELLS.values():
            val.delete(0, END)
        ROOT.title(f'CostShare - {os.path.basename(file)}')
        for i in range(0, cs_data.shape[0] + 1):
            for j in range(0, cs_data.shape[1]):
                if i == 0 and j == 0:
                    continue
                elif i == 0 and j != 0:
                    CELLS[f'cell{0}{j}'].insert(0, cs_data.columns[j])
                else:
                    CELLS[f'cell{i}{j}'].insert(0, cs_data.iloc[i - 1][j])

        CELLS['cell01'].focus()
        place_buttons('file')

        if cs_data.shape[0] > MAX_SUBSYSTEMS + 1 or cs_data.shape[1] > MAX_PEOPLE + 1:
            error_label = Label(ROOT,
                                text='Warning: File too big to fit workplace',
                                font=('Impact', 14),
                                fg='#FF0000',
                                bg=BACKGROUND_COLOUR)
            error_label.place(x=WIDTH - 300, y=HEIGHT - 50)
            error_label.after(4000, error_label.destroy)
    else:
        text = None
        if len(file) == 0:
            text = 'Error: You have not selected any file'
        elif not file.endswith('.csv'):
            text = 'Error: not a CSV file'
        error_label = Label(ROOT,
                            text=text,
                            font=('Impact', 14),
                            fg='#FF0000',
                            bg=BACKGROUND_COLOUR)
        error_label.place(x=WIDTH - 300, y=HEIGHT - 50)
        error_label.after(4000, error_label.destroy)


def save_file(mode='save'):
    global FILE
    newfile = False

    if FILE == 'Untitled' or mode == 'save_as':
        file = filedialog.asksaveasfilename(initialfile='untitled.csv',
                                            defaultextension='.csv',
                                            filetypes=[('CSV files', '*.csv'),
                                                       ('All files', '*.*')])
        if file is None:
            error_label = Label(ROOT,
                                text='Error: You have not selected any file',
                                font=('Impact', 14),
                                fg='#FF0000',
                                bg=BACKGROUND_COLOUR)
            error_label.place(x=WIDTH - 300, y=HEIGHT - 50)
            error_label.after(4000, error_label.destroy)

        else:
            newfile = True
            FILE = file

    new_df = load_to_df()

    if not newfile:
        new_df.to_csv(f'User_Files/{FILE}')
    else:
        new_df.to_csv(FILE)


def load_to_df():
    subcosts_num = 0
    participants_num = 0
    for i in range(1, MAX_SUBSYSTEMS + 1):
        if len(CELLS[f'cell{i}{0}'].get()) != 0:
            subcosts_num += 1
        else:
            break
    for i in range(1, MAX_PEOPLE + 1):
        if len(CELLS[f'cell{0}{i}'].get()) != 0:
            participants_num += 1
        else:
            break

    new_dict = []

    for i in range(1, subcosts_num + 1):
        nd = {}
        for j in range(participants_num + 1):
            if j == 0:
                nd[''] = CELLS[f'cell{i}{0}'].get()
            else:
                nd[CELLS[f'cell{0}{j}'].get()] = CELLS[f'cell{i}{j}'].get()
        new_dict.append(nd)

    new_df = pd.DataFrame(new_dict)
    return new_df


def calculate():
    global TRANSACTIONS, EVENT_SPENT
    df = load_to_df()
    if df.empty:
        quit()
    bin_df = deepcopy(df)
    fl_df = deepcopy(df)

    for col in df.columns:
        if col == '':
            continue
        else:
            for i, val in enumerate(df[col]):
                if len(val) == 0 or val == 'NaN':
                    fl_df[col][i] = None
                    bin_df[col][i] = 0
                elif val[-1] == 'n':
                    fl_df[col][i] = float(val[:-1])
                    bin_df[col][i] = 0
                else:
                    fl_df[col][i] = float(val)
                    bin_df[col][i] = 1
    bin_df = bin_df.drop(columns=[''])
    fl_df = fl_df.drop(columns=[''])

    participant_spent = fl_df.sum(axis=0)
    event_spent = fl_df.sum(axis=1)
    event_part_count = bin_df.sum(axis=1)

    EVENT_SPENT = [(df.iloc[i][0], event_spent[i]) for i in range(len(event_spent))]

    event_price_by_participant = [event_spent[i] / event_part_count[i] for i in range(len(event_spent))]
    participant_should_spent = {par: 0 for par in fl_df.columns}
    for col in fl_df.columns:
        for i, val in enumerate(bin_df[col]):
            if val == 0:
                continue
            else:
                participant_should_spent[col] += event_price_by_participant[i]

    cost_dict = {par: {'spent': None, 'should_spent': None, 'balance': None} for par in fl_df.columns}

    for col in fl_df.columns:
        spent = participant_spent[col]
        should_spent = np.round(participant_should_spent[col], 2)
        cost_dict[col]['spent'] = spent
        cost_dict[col]['should_spent'] = should_spent
        cost_dict[col]['balance'] = np.round(spent - should_spent, 2)

    debtors = []
    lenders = []
    transactions = {par: [] for par in cost_dict.keys()}

    for par in cost_dict.keys():
        if cost_dict[par]['balance'] < 0:
            debtors.append([par, cost_dict[par]['balance']])
        elif cost_dict[par]['balance'] > 0:
            lenders.append([par, cost_dict[par]['balance']])

    debtors.sort(key=lambda x: x[1], reverse=False)
    lenders.sort(key=lambda x: x[1], reverse=True)

    while len(debtors) > 0 and len(lenders) > 0:
        if abs(debtors[0][1]) > lenders[0][1]:
            lender = lenders.pop(0)
            transactions[debtors[0][0]].append((lender[0], np.round(lender[1], 2)))
            debtors[0][1] += lender[1]
        elif abs(debtors[0][1]) < lenders[0][1]:
            debtor = debtors.pop(0)
            transactions[debtor[0]].append((lenders[0][0], np.round(debtor[1], 2)))
            lenders[0][1] += debtor[1]
        else:
            debtor = debtors.pop(0)
            lender = lenders.pop(0)
            transactions[debtor[0]].append((lender[0], np.round(lender[1], 2)))

    if len(debtors) != 0:
        for el in debtors:
            if np.round(el[1], 1) != 0:
                transactions[el[0]].append(('Undefined operation', el[1]))

    if len(lenders) != 0:
        for el in lenders:
            if np.round(el[1], 1) != 0:
                transactions[el[0]].append(('Undefined operation', el[1]))

    TRANSACTIONS = transactions

    report_button = Button(ROOT,
                           width=9,
                           text='Get report',
                           command=generate_report,
                           font=('Tahoma', 16),
                           fg=TEXT_COLOUR,
                           bg=BACKGROUND_COLOUR,
                           activeforeground=TEXT_COLOUR,
                           activebackground=BACKGROUND_COLOUR)
    report_button.place(x=250, y=50)


def generate_report():
    report_window = Toplevel()
    window_config(report_window, f'Report for: {FILE}')
    report = f'REPORT FOR {FILE}\n'

    report += '\nParticipants:\n'
    for key in TRANSACTIONS.keys():
        report += key + ', '
    report = report[:-2] + '\n'

    report += '\nMoney spent in subevents:\n'
    for el in EVENT_SPENT:
        report += f'{el[0]}: {el[1]}\n'

    report += '\nTransactions to make:\n'
    for key in TRANSACTIONS.keys():
        if len(TRANSACTIONS[key]):
            for el in TRANSACTIONS[key]:
                report += f'{key} -> {el[0]}: {abs(el[1])}\n'

    txt_var = StringVar()
    txt_var.set(report)
    message_report = Message(report_window,
                             font=('Tahoma', 12),
                             fg=TEXT_COLOUR,
                             textvariable=txt_var,
                             bg=BACKGROUND_COLOUR)
    message_report.place(x=50, y=50)

    save_report_button = Button(report_window,
                                width=len('Save to txt'),
                                text='Save to txt',
                                command=lambda: save_report(report),
                                font=('Tahoma', 16),
                                fg=TEXT_COLOUR,
                                bg=BACKGROUND_COLOUR,
                                activeforeground=TEXT_COLOUR,
                                activebackground=BACKGROUND_COLOUR)
    save_report_button.place(x=700, y=400)

    exit_button = Button(report_window,
                         width=len('Save to txt'),
                         text='Exit',
                         command=lambda: report_window.destroy(),
                         font=('Tahoma', 16),
                         fg=TEXT_COLOUR,
                         bg=BACKGROUND_COLOUR,
                         activeforeground=TEXT_COLOUR,
                         activebackground=BACKGROUND_COLOUR)
    exit_button.place(x=700, y=320)


def save_report(report):
    filename = FILE[:-4] + '_report.txt'
    with open(f'User_Files/{filename}', 'w') as f:
        f.write(report)


def manual():
    with open('Program_Files/manual.txt', 'r') as f:
        lines = f.readlines()
    manual_txt = ''.join(lines)
    messagebox.showinfo("CostShare - Manual", manual_txt)


def about():
    with open('Program_Files/about.txt', 'r') as f:
        lines = f.readlines()
    about_txt = ''.join(lines)
    messagebox.showinfo("CostShare V1.0", about_txt)


# Widnow functions
def window_config(window, title):
    x = int((SCREEN_WIDTH - WIDTH) / 2)
    y = int((SCREEN_HEIGHT - HEIGHT) / 2)
    window.geometry(f'{WIDTH}x{HEIGHT}+{x}+{y}')
    window.title(title)
    window.iconphoto(True, ICON)
    window.config(background=BACKGROUND_COLOUR)
    return window


def make_cells():
    global CELLS
    for i in range(MAX_SUBSYSTEMS + 1):
        for j in range(MAX_PEOPLE + 1):
            state = NORMAL
            if i == 0 and j == 0:
                colour = '#000000'
                width = 20
                state = DISABLED
            elif i == 0 and j != 0:
                colour = '#488583'
                width = 12
            elif i != 0 and j == 0:
                colour = '#48856A'
                width = 20
            else:
                colour = '#5E5E5E'
                width = 12

            textarea = Entry(frame1,
                             fg=TEXT_COLOUR,
                             bg=colour,
                             width=width,
                             state=state,
                             disabledbackground='#000000')
            textarea.grid(row=i, column=j)
            CELLS[f'cell{i}{j}'] = textarea


def make_buttons(which):
    global INIT_BUTTONS, FILE_BUTTONS
    init_texts = ['New File', 'Open File', 'Manual', 'Exit']
    file_texts = ['Calculate', 'Save file', 'Exit']
    init_commands = [new_file, read_file, manual, quit]
    file_commands = [calculate, save_file, quit]

    texts, commands, buttons = None, None, None

    if which == 'init':
        texts = init_texts
        commands = init_commands
        buttons = INIT_BUTTONS

    elif which == 'file':
        texts = file_texts
        commands = file_commands
        buttons = FILE_BUTTONS

    for i in range(len(texts)):
        buttons.append(Button(ROOT,
                              width=len(max(texts, key=len)),
                              text=texts[i],
                              command=commands[i],
                              font=('Tahoma', 16),
                              fg=TEXT_COLOUR,
                              bg=BACKGROUND_COLOUR,
                              activeforeground=TEXT_COLOUR,
                              activebackground=BACKGROUND_COLOUR))


def place_buttons(which):
    global INIT_BUTTONS, FILE_BUTTONS
    xs_init = [200, 450, 200, 450]
    ys_init = [275, 275, 350, 350]
    xs_file = [400, 550, 700]
    ys_file = [50, 50, 50]

    xs, ys, buttons = None, None, None
    if which == 'init':
        xs = xs_init
        ys = ys_init
        buttons = INIT_BUTTONS
    elif which == 'file':
        xs = xs_file
        ys = ys_file
        buttons = FILE_BUTTONS

    for i in range(len(xs)):
        buttons[i].place(x=xs[i], y=ys[i])


# Main window
ROOT = window_config(ROOT, 'CostShare')

# Menubar
menubar = Menu(ROOT)
ROOT.config(menu=menubar)

newfile_icon = PhotoImage(file='Program_Files/new.png')
openfile_icon = PhotoImage(file='Program_Files/open.png')
savefile_icon = PhotoImage(file='Program_Files/save.png')
exit_icon = PhotoImage(file='Program_Files/exit.png')
about_icon = PhotoImage(file='Program_Files/about.png')
manual_icon = PhotoImage(file='Program_Files/manual.png')

filemenu = Menu(menubar, tearoff=0, font=('Impact', 12))
menubar.add_cascade(label='File', menu=filemenu)
filemenu.add_command(label='New', command=new_file, image=newfile_icon, compound='left')
filemenu.add_command(label='Open', command=read_file, image=openfile_icon, compound='left')
filemenu.add_command(label='Save', command=save_file, image=savefile_icon, compound='left')
filemenu.add_separator()
filemenu.add_command(label='Exit', command=quit, image=exit_icon, compound='left')

helpmenu = Menu(menubar, tearoff=0, font=('Impact', 12))
menubar.add_cascade(label='Help', menu=helpmenu)
helpmenu.add_command(label='Manual', command=manual, image=manual_icon, compound='left')
helpmenu.add_command(label='About program', command=about, image=about_icon, compound='left')

# Labels and workplace
label1 = Label(ROOT,
               text='Cost Share',
               font=('Impact', 20, 'bold'),
               fg=TEXT_COLOUR,
               bg=BACKGROUND_COLOUR)
label1.place(x=WIDTH / 2 - 400, y=30)

make_buttons('init')
make_buttons('file')
place_buttons('init')

frame1 = Frame(ROOT)

label2 = Label(ROOT,
               text='Participants',
               font=('Impact', 15),
               fg='#488583',
               bg=BACKGROUND_COLOUR)

label3 = Label(ROOT,
               text='Subcosts',
               font=('Impact', 15),
               fg='#48856A',
               bg=BACKGROUND_COLOUR,
               wraplength=1)

if __name__ == '__main__':
    ROOT.mainloop()
