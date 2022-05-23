from doccano_api_client import DoccanoClient

if __name__ == '__main__':

    base_url = 'http://localhost:8000'
    username = 'admin'
    password = 'admin'
    client = DoccanoClient(base_url, username, password)

    print('Project list: ')
    print(client.get_project_list())

    # upload a json file to project 3. If file is in current directory, file_path is omittable
    r_json_upload = client.post_doc_upload(
        project_id=3,
        file_name="admin.jsonl",
        file_path="C:\\Users\\Anastassy Cap\\Downloads\\",
        column_data="data",
        format="JSONL"
    )

    print(r_json_upload)

    res = client.span_type_upload(3, "label_config.json", "C:\\Users\\Anastassy Cap\\Downloads\\")
    print(f'Label creation response:\n{res}')
