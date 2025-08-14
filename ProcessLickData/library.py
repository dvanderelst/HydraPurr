import pandas
import numpy

def read(filename):
    fl = open(filename, 'r')
    comment = fl.readline()
    fl.close()
    data = pandas.read_csv(filename, skiprows=6, header=None)
    data.columns = ['time', 'response']
    return data, comment

def summarize(filename):
    threshold = 10000
    data, _ = read(filename)
    data = data.values
    conductance = data[:, 1]

    summary = []
    previous_state = None
    counter = 0
    for value in conductance:
        if value < threshold: current_state = 'below'
        if value >= threshold: current_state = 'above'
        if previous_state is None: previous_state = current_state
        if current_state == previous_state:
            counter = counter + 1
        else:
            #print(counter, previous_state)
            if previous_state == 'below': summary.append(-1 * counter)
            if previous_state == 'above': summary.append(1 * counter)
            counter = 1

        previous_state = current_state

    summary = numpy.array(summary)
    return summary