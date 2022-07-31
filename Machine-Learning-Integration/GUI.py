from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter import Tk, ttk, StringVar, W, E


class ProjectSettings:

    def __init__(self):
        self.inputFilePath = ""
        self.inputFileName = ""
        self.outputFilePath = ""
        self.outputFileName = ""

        self.doccanoProjects = list()
        self.selectedProjectNameFromDropDown = ""  # name of the selected project in the 'doccanoProjects' variable
        self.frame = None  # Contains the ttk frame

    def getIdOfSelectedProject(self):
        for project in self.doccanoProjects['results']:
            if self.selectedProjectNameFromDropDown == project['name']:
                return project['id']
        return -1

    def validParameters(self):
        return self.inputFilePath != "" and self.outputFilePath != "" and len(self.doccanoProjects) > 0 and \
               self.selectedProjectNameFromDropDown != ""

    def __str__(self):
        return f'Input file: {self.inputFilePath}\n Output file: {self.outputFileName}\n ' \
               f'Selected Doccano Project: {self.selectedProjectNameFromDropDown}\n '


def choose_input_file(projectSettings):
    filePath = askopenfilename()  # show an "Open" dialog box and return the path to the selected file
    print(filePath)
    fileName = filePath.split("/")[-1]

    projectSettings.inputFilePath = filePath
    projectSettings.inputFileName = fileName

    # update the frame in the GUI that we have selected an input file
    ttk.Label(projectSettings.frame, text=f'{fileName}').grid(column=1, row=1)


def choose_output_file(projectSettings):
    # write processed text to a file
    outputFilePath = asksaveasfilename()
    outputFileName = outputFilePath.split("/")[-1]
    print(outputFilePath)
    print(outputFileName)
    projectSettings.outputFilePath = outputFilePath
    projectSettings.outputFileName = outputFileName

    # update the frame in the GUI that we have selected an output file
    ttk.Label(projectSettings.frame, text=f'{outputFileName}').grid(column=1, row=2)


def createFrame(rootWindow, projectSettings):
    frame = ttk.Frame(rootWindow)

    frame.columnconfigure(0, weight=3)
    frame.columnconfigure(1, weight=1)
    frame.columnconfigure(2, weight=1)

    # Dropdown menu
    projectNames = [project['name'] for project in projectSettings.doccanoProjects['results']]
    ttk.Label(frame, text='Select Doccano project: ').grid(column=0, row=0, sticky=W)

    # this must be set after the main window has been created
    projectSettings.selectedProjectNameFromDropDown = StringVar()
    projectSettings.selectedProjectNameFromDropDown.set(projectNames[0])
    dropdown = ttk.OptionMenu(frame, projectSettings.selectedProjectNameFromDropDown, projectNames[0], *projectNames)
    dropdown.grid(column=2, row=0)

    # Select input file
    ttk.Label(frame, text='Select input file: ').grid(column=0, row=1, sticky=W)
    ttk.Button(frame, text="Browse", command=lambda: choose_input_file(projectSettings)).grid(column=2, row=1, sticky=E)

    # Select output file
    ttk.Label(frame, text='Select output file (JSONL extension): ').grid(column=0, row=2, sticky=W)
    ttk.Button(frame, text="Browse", command=lambda: choose_output_file(projectSettings)).grid(column=2, row=2,
                                                                                               sticky=E)

    # ok button at the bottom of the frame
    ttk.Button(frame, text='Done', command=lambda: rootWindow.destroy()).grid(column=2, row=5, pady=50, sticky=E)

    return frame
