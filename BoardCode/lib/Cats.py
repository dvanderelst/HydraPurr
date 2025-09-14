cats={}
cats['61000000007E30010000000000'] = {'name': 'henk', 'age': 6}
cats['32E09C0000ED30010000000000'] = {'name': 'bob', 'age': 12}


def get_name(tag_key):
    if tag_key not in cats: return 'unknown'
    return cats[tag_key]['name']

def get_age(tag_key):
    return cats[tag_key]['age']

def get_all_names():
    all_names = []
    for tag_key in cats: all_names.append(cats[tag_key]['name'])
    return all_names