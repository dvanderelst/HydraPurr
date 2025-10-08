def request_kind():
    selected_kind = None
    while selected_kind is None:
        kind = input("Enter data type to retrieve (licks/system): ")
        kind = kind.lower()
        if kind.startswith('s'): selected_kind = 'system'
        if kind.startswith('l'): selected_kind = 'licks'
    print('Selected data type:', selected_kind)
    return selected_kind

def request_save():
    save_response = None
    while save_response is None:
        response = input("Do you want to save the data to a file? (y/n): ")
        response = response.lower()
        if response.startswith('y'): save_response = True
        if response.startswith('n'): save_response = False
    return save_response

def get_file_name(kind):
    #Get a filenmame based on date and time
    from datetime import datetime
    now = datetime.now()
    date_time = now.strftime("%Y%m%d_%H%M%S")
    file_name = f"data_{kind}_{date_time}.txt"
    return file_name

def save_data(data, file_name):
    try:
        with open(file_name, 'w') as file:
            for line in data: file.write(line + '\n')
        print(f"Data saved to {file_name}")
    except Exception as e:
        print("Error saving data to file:", e)