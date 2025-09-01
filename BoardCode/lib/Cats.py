cats={}
cats['61000000007E30010000000000'] = {'name': 'henk', 'age': 6}
cats['32E09C0000ED30010000000000'] = {'name': 'bob', 'age': 12}


def get_defined(tag):
    return tag in cats.key()

def get_name(tag):
    return cats[tag]['name']

def get_age(tag):
    return cats[tag]['age']

def get_all_names():
    all_names = []
    for tag in cats: all_names.append(cats[tag]['name'])
    return all_names