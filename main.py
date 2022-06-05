from doccano_api_client import DoccanoClient

from tkinter.filedialog import askopenfilename
from tkinter import Tk, Label, Button, Radiobutton, IntVar


def ask_multiple_choice_question(prompt, options):
    root = Tk()
    if prompt:
        Label(root, text=prompt).pack()
    v = IntVar()
    for i, option in enumerate(options):
        Radiobutton(root, text=option, variable=v, value=i).pack(anchor="w")
    Button(root, text="ok", command=lambda: root.quit()).pack()
    root.mainloop()
    if v.get() == 0:
        return None
    return options[v.get()]


if __name__ == '__main__':
    base_url = 'http://localhost:8000'
    username = 'admin'
    password = 'admin'
    client = DoccanoClient(base_url, username, password)

    Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
    inputFilePath = askopenfilename()  # show an "Open" dialog box and return the path to the selected file
    filePathTokens = inputFilePath.split("/")
    inputFileName = filePathTokens[-1]
    print(inputFilePath)

    projectList = client.get_project_list()['results']

    result = ask_multiple_choice_question(
        "Select your Doccano project",
        [project['name'] for project in projectList]
    )

    print(result)

    # upload a json file to project 3. If file is in current directory, file_path is omittable
    r_json_upload = client.post_doc_upload(
        project_id=3,
        file_name=inputFileName,
        file_path='/'.join(filePathTokens)[0:-1] + '/',
        column_data="data",
        format="JSONL"
    )

    print(r_json_upload)

    # res = client.span_type_upload(3, "label_config.json", "C:\\Users\\Anastassy Cap\\Downloads\\")
    # print(f'Label creation response:\n{res}')
