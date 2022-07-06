from allennlp.predictors.predictor import Predictor
from nltk import tokenize
import json
import datefinder

from merge_models import merge_results

from doccano_api_client import DoccanoClient

from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter import Tk, ttk, StringVar, W, E


def mergeCommonLabels(listOfLabels, dates):
    newList = list()

    length = len(listOfLabels)
    labelStartIndex = 0
    if length > 0:
        labelStartIndex = listOfLabels[0][0]  # The starting index is the index of the first label in the list

    for index, labelList in enumerate(listOfLabels):

        labelEndIndex = labelList[1]
        labelName = labelList[2]

        """
        If the next label does not have the same name or is not adjacent or we are at the end of the list of labels,
        we change the cursor positions and merge
        """
        if (index == length - 1 or labelEndIndex + 1 != listOfLabels[index + 1][0] or labelName !=
            listOfLabels[index + 1][2]) and labelName.lower() != 'date':
            newList.append([labelStartIndex, labelEndIndex, labelName])
            if index != length - 1:
                labelStartIndex = listOfLabels[index + 1][0]

    # add all dates found by the datefinder
    for date in dates:
        newList.append([date[2][0], date[2][1], 'DATE'])

    return newList


def predict(sentence, model):
    # Feed the sentence to the fine grained model
    fine_grained_output = model.predict(sentence=sentence)
    words = fine_grained_output['words']
    labels = fine_grained_output['tags']
    return words, labels


# ----------------------------------------------
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


def main(fine_grained, elmo):
    doccano_client = DoccanoClient(
        'http://localhost:8000',
        'admin',
        'admin'
    )

    projectList = doccano_client.get_project_list()

    projectSettings = ProjectSettings()
    projectSettings.doccanoProjects = projectList

    mainWindow = Tk()

    screen_width = mainWindow.winfo_screenwidth()
    screen_height = mainWindow.winfo_screenheight()

    windowWidth = 450
    windowHeight = 175
    center_x = int(screen_width / 2 - windowWidth / 2)
    center_y = int(screen_height / 2 - windowHeight / 2)

    mainWindow.title('Project configuration')
    mainWindow.geometry(f"{windowWidth}x{windowHeight}+{center_x}+{center_y}")

    mainWindow.columnconfigure(0, weight=1)

    projectSettings.frame = createFrame(mainWindow, projectSettings)
    projectSettings.frame.grid(column=0, row=0)
    mainWindow.mainloop()  # show the window until the user selects all files and clicks 'done'

    # We should now have all the files paths as well as the project chosen by the user
    projectSettings.selectedProjectNameFromDropDown = projectSettings.selectedProjectNameFromDropDown.get()
    print(projectSettings)

    # Sanity check that we have all the available information needed
    if not projectSettings.validParameters():
        root = Tk()
        message = ttk.Label(root, text='Input parameters are not valid!')  # todo: make the error message more precise
        message.pack(padx=15, pady=15)
        root.mainloop()
        exit(0)

    inputFilePath = projectSettings.inputFilePath
    inputFileName = projectSettings.inputFileName

    file = open(inputFilePath, "r")
    fullText = file.read()
    file.close()
    # sentences = tokenize.sent_tokenize(fullText)
    sentences = fullText.split('\n')
    listOfLabels = list()

    # write processed text to a file
    outputFilePath = projectSettings.outputFilePath
    outputFileName = projectSettings.outputFileName
    outputFile = open(outputFilePath, "a")
    outputFile.truncate(0)  # clear contents of the file starting at the beginning of the file

    inputFileIsSINCategory = inputFileName.__contains__("SIN_")

    for idx, sentence in enumerate(sentences):

        startIndexOfLabel = 0
        endIndexOfLabel = 0
        listOfLabels.clear()

        # Feed the sentence to both models
        words, labels_fine_grained = predict(sentence, fine_grained)
        words_elmo, labels_elmo = predict(sentence, elmo)

        print(f'Fine grained: \n {words} \n {labels_fine_grained}')
        print(f'Elmo: \n {words_elmo} \n {labels_elmo}')

        merged_labels = merge_results(labels_fine_grained, labels_elmo)
        print(f'Merged labels: \n {merged_labels}')

        # Iterate on all labels of the fine grained model and prioritize it over the elmo one
        for index, currentLabel in enumerate(merged_labels):

            splitLabel = currentLabel.split('-')[-1]

            if currentLabel == 'O' and index != len(merged_labels) - 1:
                startIndexOfLabel = startIndexOfLabel + len(words[index]) + 1
                endIndexOfLabel = endIndexOfLabel + len(words[index]) + 1
                continue

            if index == len(merged_labels) - 1 or currentLabel != merged_labels[index + 1]:
                # the next label is different so we record this label in the list together with the indexes
                if currentLabel != 'O':
                    listOfLabels.append([startIndexOfLabel, endIndexOfLabel + len(words[index]), splitLabel])
                if index == len(merged_labels) - 1:
                    # Once we are done with this sentence, we need to merge all common labels in the list
                    sanitizedSentence = " ".join(words)
                    dates = datefinder.find_dates(sanitizedSentence, index=True, source=True)
                    mergedLabels = mergeCommonLabels(listOfLabels, dates)

                    data = {"data": sanitizedSentence, "label": mergedLabels}
                    print(json.dumps(data))
                    outputFile.write(json.dumps(data) + "\n")
                # if words[index] in charsThatNeedNoSpaces:
                #     startIndexOfLabel = endIndexOfLabel + len(words[index])
                # else:
                startIndexOfLabel = endIndexOfLabel + len(
                    words[index]) + 1  # +1 accounts for the space at the end of the word

            # if words[index] in charsThatNeedNoSpaces:
            #     endIndexOfLabel = endIndexOfLabel + len(words[index])
            # else:
            endIndexOfLabel = endIndexOfLabel + len(
                words[index]) + 1  # +1 accounts for the space at the end of the word

    outputFile.close()

    # upload text file to the doccano instance
    r_json_upload = doccano_client.post_doc_upload(
        project_id=projectSettings.getIdOfSelectedProject(),
        file_name=outputFileName,
        column_data="data",
        file_path=outputFilePath.replace(outputFileName, ''))
    print(r_json_upload)


if __name__ == '__main__':
    ner_fine_grained = Predictor.from_path(
        "https://storage.googleapis.com/allennlp-public-models/fine-grained-ner.2021-02-11.tar.gz")

    ner_elmo = Predictor.from_path("https://storage.googleapis.com/allennlp-public-models/ner-elmo.2021-02-12.tar.gz")

    main(ner_fine_grained, ner_elmo)
    # predict("EternalBlue is a computer exploit developed by the U.S. Exploit National Security Agency (NSA).")
