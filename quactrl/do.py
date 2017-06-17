from quactrl import (
    Column, ForeignKey, relationship, Model,
    dal, Integer, String, DATETIME, DECIMAL
)
import pdb


class Batch:
    def __init__(self, part_number, batch_number, operator):
        self.part_number = part_number
        self.batch_number = batch_number
        self.operator = operator
        self.close_date = None
        self.items = {}


class Item:
    def __init__(self, serial_number, batch):
        self.batch = batch
        self.sn = serial_number
        self.status = None
        self.tests = []

    def validate(self, serial_number):
        pass

    @classmethod
    def has_passed_test(self, serial_number):
        return False



class DoDAO:
    """Class to operate with Do Objects"""
    pass
