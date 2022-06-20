from allennlp.predictors.predictor import Predictor
from nltk import tokenize
import json

from doccano_api_client import DoccanoClient

from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter import Tk


def mergeCommonLabels(listOfLabels):
    newList = list()

    length = len(listOfLabels)
    labelStartIndex = 0
    if length > 0:
        labelStartIndex = listOfLabels[0][0]

    for index, labelList in enumerate(listOfLabels):

        labelEndIndex = labelList[1]
        labelName = labelList[2]

        """
        If the next label does not have the same name or is not adjacent or we are at the end of the list of labels,
        we change the cursor positions and merge
        """
        if index == length - 1 or labelEndIndex + 1 != listOfLabels[index + 1][0] or labelName != \
                listOfLabels[index + 1][2]:
            newList.append([labelStartIndex, labelEndIndex, labelName])
            if index != length - 1:
                labelStartIndex = listOfLabels[index + 1][0]

    return newList


def predict(sentence, model):
    # These two models use different set of tags, It will be useful to check both
    fine_grained_output = model.predict(sentence=sentence)
    words = fine_grained_output['words']
    labels = fine_grained_output['tags']
    # print(f"Words: \n {words}")
    # print(f"Labels: \n {labels}")
    # print(f'Words length: {len(words)}')
    # print(f'Labels length: {len(labels)}')
    # print(f"Full output: \n {fine_grained_output}")

    # elmo_output = ner_elmo.predict(sentence=sentence)
    # print(elmo_output['tags'])
    return words, labels


def main(fine_grained):
    Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
    inputFilePath = askopenfilename()  # show an "Open" dialog box and return the path to the selected file
    print(inputFilePath)

    file = open(inputFilePath, "r")
    fullText = file.read()
    file.close()
    sentences = tokenize.sent_tokenize(fullText)
    listOfLabels = list()

    # write processed text to a file
    outputFilePath = asksaveasfilename()
    outputFileName = outputFilePath.split("/")[-1]
    print(outputFilePath)
    print(outputFileName)
    outputFile = open(outputFilePath, "a")
    outputFile.truncate(0)  # clear contents of the file starting at the beginning of the file

    # the following characters do not (normally) have spaces after them in a text
    charsThatNeedNoSpaces = ['(', ')', ',', '-', '.']

    for idx, sentence in enumerate(sentences):

        startIndexOfLabel = 0
        endIndexOfLabel = 0
        listOfLabels.clear()
        words, labels = predict(sentence, fine_grained)

        for index, currentLabel in enumerate(labels):

            splitLabel = currentLabel.split('-')[-1]

            if currentLabel == 'O' and index != len(labels) - 1:
                startIndexOfLabel = startIndexOfLabel + len(words[index]) + 1
                endIndexOfLabel = endIndexOfLabel + len(words[index]) + 1
                continue

            if index == len(labels) - 1 or currentLabel != labels[index + 1]:
                # the next label is different so we record this label in the list together with the indexes
                if currentLabel != 'O':
                    listOfLabels.append([startIndexOfLabel, endIndexOfLabel + len(words[index]), splitLabel])
                if index == len(labels) - 1:
                    # Once we are done with this sentence, we need to merge all common labels in the list
                    mergedLabels = mergeCommonLabels(listOfLabels)

                    data = {"data": " ".join(words), "label": mergedLabels}
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
    doccano_client = DoccanoClient(
        'http://localhost:8000',
        'admin',
        'admin'
    )

    r_json_upload = doccano_client.post_doc_upload(
        project_id=3,
        file_name='output.jsonl',
        column_data="data",
        file_path='C:/Users/Anastassy Cap/Downloads/')
    print(r_json_upload)


if __name__ == '__main__':
    ner_fine_grained = Predictor.from_path(
        "https://storage.googleapis.com/allennlp-public-models/fine-grained-ner.2021-02-11.tar.gz")

    # ner_elmo = Predictor.from_path("https://storage.googleapis.com/allennlp-public-models/ner-elmo.2021-02-12.tar.gz")

    main(ner_fine_grained)
    # predict("EternalBlue is a computer exploit developed by the U.S. Exploit National Security Agency (NSA).")
