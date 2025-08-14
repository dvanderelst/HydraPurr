import sqlite3
import copy
from LickLibrary import  Misc, Settings
import decimal

def data2item(data):
    columns = Settings.data_columns
    types = Settings.data_types
    item = {}
    for c, d, t in zip(columns, data, types):
        if t == float: d = decimal.Decimal(str(d))
        item[c] = d
    return item


class SQLconnector:
    def __init__(self, db_file, table, omit_fields=[]):
        self.table = table
        self.connection = sqlite3.connect(db_file)
        self.columns = self.get_table_columns()
        self.omit_fields = omit_fields
        self.insert_command = self.create_insert_command()

    def get_table_columns(self):
        cursor = self.connection.execute('select * from %s' % self.table)
        names = [description[0] for description in cursor.description]
        return names

    def read_data(self):
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM %s' % self.table)
        data = cursor.fetchall()
        return data

    def create_insert_command(self):
        if not Misc.isList(self.omit_fields): self.omit_fields = [self.omit_fields]
        retained = copy.copy(self.columns)
        for x in self.omit_fields: retained.remove(x)
        field_string = Misc.fields2str(retained, blank=False)
        blank_string = Misc.fields2str(retained, blank=True)
        full_command = "INSERT INTO %s %s VALUES %s" % (self.table, field_string, blank_string)
        return full_command

    def insert_data(self, data):
        cursor = self.connection.cursor()
        cursor.execute(self.insert_command, data)
        self.connection.commit()
