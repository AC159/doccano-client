from allennlp.predictors.predictor import Predictor
from nltk import tokenize
import json
import datefinder

import re
from merge_models import merge_results

from doccano_api_client import DoccanoClient
import GUI

from tkinter import Tk, ttk
import pyap


def mergeCommonLabels(listOfLabels, dates, addresses, labelIndexOffset):
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

    # now that we have merged commons labels together, we can start inserting other kinds of labels in ascending order
    # of precedence

    # add all dates found by the datefinder
    for date in dates:
        dateLabelStartIndex = date[2][0] + labelIndexOffset
        dateLabelEndIndex = date[2][1] + labelIndexOffset

        if re.findall(r"\d*\.\d*", date[1]):
            # Do not register dates that contain floating point numbers
            continue

        for index, labelList in enumerate(newList[:]):  # iterate on copy of the list of labels
            labelStartIndex = labelList[0]
            labelEndIndex = labelList[1]

            # check if both labels overlap and remove the labels that overlap with the date label
            if (labelStartIndex <= dateLabelStartIndex <= labelEndIndex) or \
                    (labelStartIndex <= dateLabelEndIndex <= labelEndIndex) or \
                    (dateLabelStartIndex <= labelStartIndex <= dateLabelEndIndex) or \
                    (dateLabelStartIndex <= labelEndIndex <= dateLabelEndIndex):
                newList.remove(labelList)

        newList.append([dateLabelStartIndex, dateLabelEndIndex, 'DATE'])

    # add all addresses found by pyap
    for address in addresses:
        addressStartIndex = address.match_start + labelIndexOffset
        addressEndIndex = address.match_end + labelIndexOffset

        for index, labelList in enumerate(newList[:]):
            labelStartIndex = labelList[0]
            labelEndIndex = labelList[1]

            print(f'Label list: {labelList} - address start = {addressStartIndex} end = {addressEndIndex}')

            # check if both labels overlap and remove the labels that overlap with the address label
            if (labelStartIndex <= addressStartIndex <= labelEndIndex) or \
                    (labelStartIndex <= addressEndIndex <= labelEndIndex) or \
                    (addressStartIndex <= labelStartIndex <= addressEndIndex) or \
                    (addressStartIndex <= labelEndIndex <= addressEndIndex):
                print(f'Removed list: {labelList}')
                newList.remove(labelList)

        print(f'Added new address: {[addressStartIndex, addressEndIndex, "ADDRESS"]}')
        newList.append([addressStartIndex, addressEndIndex, 'ADDRESS'])

    return newList


def predict(sentence, model):
    # Feed the sentence to the fine grained model
    fine_grained_output = model.predict(sentence=sentence)
    words = fine_grained_output['words']
    labels = fine_grained_output['tags']
    return words, labels


def main(fine_grained, elmo):

    doccano_client = DoccanoClient(
        'http://localhost:8000',
        'admin',
        'admin'
    )

    projectList = doccano_client.get_project_list()

    projectSettings = GUI.ProjectSettings()
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

    projectSettings.frame = GUI.createFrame(mainWindow, projectSettings)
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

    finalConcatenatedSentences = ""
    finalListOfLabels = list()

    for idx, sentence in enumerate(sentences):

        sentence = sentence.strip()

        if len(sentence) == 0:
            continue

        startIndexOfLabel = 0
        endIndexOfLabel = 0
        listOfLabels.clear()

        # Feed the sentence to both models
        words, labels_fine_grained = predict(sentence, fine_grained)
        words_elmo, labels_elmo = predict(sentence, elmo)

        # print(f'Fine grained: \n {words} \n {labels_fine_grained}')
        # print(f'Elmo: \n {words_elmo} \n {labels_elmo}')

        merged_labels = merge_results(labels_fine_grained, labels_elmo)
        # print(f'Merged labels: \n {merged_labels}')

        labelIndexOffset = len(finalConcatenatedSentences) + 1

        sanitizedSentence = " ".join(words)
        finalConcatenatedSentences = finalConcatenatedSentences + "\n" + sanitizedSentence

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
                    listOfLabels.append([startIndexOfLabel + labelIndexOffset,
                                         endIndexOfLabel + len(words[index]) + labelIndexOffset,
                                         splitLabel])

                if index == len(merged_labels) - 1:
                    # Once we are done with this sentence, we need to merge all common labels in the list
                    dates = datefinder.find_dates(sanitizedSentence, index=True, source=True)
                    addresses = pyap.parse(sanitizedSentence, country='CA')

                    mergedLabels = mergeCommonLabels(listOfLabels, dates, addresses, labelIndexOffset)
                    for label in mergedLabels:
                        finalListOfLabels.append(label)

                    # data = {"data": sanitizedSentence, "label": mergedLabels}
                    # outputFile.write(json.dumps(data) + "\n")

                startIndexOfLabel = endIndexOfLabel + len(
                    words[index]) + 1  # +1 accounts for the space at the end of the word

            endIndexOfLabel = endIndexOfLabel + len(
                words[index]) + 1  # +1 accounts for the space at the end of the word

    print(finalConcatenatedSentences)
    data = {"data": finalConcatenatedSentences, "label": finalListOfLabels}
    outputFile.write(json.dumps(data) + "\n")
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
        "C:\\Users\\Anastassy Cap\\Downloads\\fine-grained-ner.2021-02-11.tar.gz")

    ner_elmo = Predictor.from_path("C:\\Users\\Anastassy Cap\\Downloads\\ner-elmo.2021-02-12.tar.gz")

    main(ner_fine_grained, ner_elmo)
    # predict("EternalBlue is a computer exploit developed by the U.S. Exploit National Security Agency (NSA).")
