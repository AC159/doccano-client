from tkinter.filedialog import askdirectory

import os
import re


def sanitizeFiles():
    directory = askdirectory()

    if directory.split('/')[-1] == 'ST':
        for filename in os.listdir(directory):
            filepath = directory + '/' + filename
            if not os.path.isfile(filepath):
                continue

            f = open(filepath, "r+", encoding="utf8")
            fullText = f.read()
            fullText = fullText.replace('Active in Program', '\nActive in Program').replace('Admit Term', '\nAdmit Term')

            f.seek(0)  # go to the beginning of the file before writing
            f.write(fullText)
            f.truncate()
            f.close()

    elif directory.split('/')[-1] == 'SIN':
        for filename in os.listdir(directory):
            filepath = directory + '/' + filename
            if not os.path.isfile(filepath):
                continue

            f = open(filepath, "r+", encoding="utf8")
            fullText = f.read()

            try:
                firstName = re.findall('First Name:[a-zA-Z]*\n*', fullText)[0].rstrip('\n')
                middleName = re.findall('Middel Name\(s\):[a-zA-Z]*\n*', fullText)[0].rstrip('\n')
            except IndexError as error:
                print(f'Could not parse file {filename} correctly: {error}')
                continue

            # the order of string replacement is important
            fullText = fullText.replace('Family Name(s):', '')
            fullText = re.sub('Middel Name\(s\):[a-zA-Z]*\n*', middleName + ' ', fullText).replace('Middel Name(s):', ' ')
            fullText = re.sub('First Name:[a-zA-Z]*\n*', firstName + ' ', fullText)

            f.seek(0)  # go to the beginning of the file before writing
            f.write(fullText)
            f.truncate()
            f.close()


if __name__ == '__main__':
    sanitizeFiles()
