from LickLibrary import Buffer, Settings, DbConnector
import logging


class ZooDatabase:
    def __init__(self, load_buffer=False, verbose=False):
        self.table = Settings.table
        self.database = DbConnector.SQLconnector(Settings.database, Settings.table, Settings.omit_fields)
        self.buffer = Buffer.Buffer(load=load_buffer)

    def add_data(self, data, flush=True):
        # Add the data to the buffer
        logging.info('Adding data to buffer ' + str (data))
        self.buffer.append(data)
        # Save a copy of the buffer to disk
        logging.info('Saving buffer to disk')
        self.buffer.save()
        # if flush, then try to flush the buffer to AWS
        if flush and not self.buffer.empty: self.flush_buffer()


    def get_data(self):
        data = self.database.read_data()
        return data

    def flush_buffer(self):
        logging.info('Trying to flush buffer')
        successful_uploads = []
        for i in range(len(self.buffer)):
            logging.info('Flushing: ' + str(self.buffer[i]))
            try:
                self.database.insert_data(self.buffer[i])
                successful_uploads.append(i)
            except Exception as exception:
                logging.exception(str(exception))
        # remove the successfully uploaded data
        self.buffer.remove(successful_uploads)
        logging.info('Remaining items in buffer: ' + str(len(self.buffer)))
        # save the updated buffer to disk
        logging.info('Saving buffer to disk')
        self.buffer.save()


