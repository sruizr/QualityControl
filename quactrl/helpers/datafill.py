  class Filler:
      __metaclass__ = ABCmeta

      def __init__(self, dal):
          self.dal = dal
          self.persons = {}
          self.locations = {}
          self.part_models = {}
          self.device_models = {}
          self.characteristics = {}
          self.controls = {}
          self.devices = {}

      def load_persons(self):
          pass

      def load_locations(self):
          pass

      def load_part_models(self):
          pass

      def load_device_models(self):
          pass

      def load_controls(self):
          pass

      def load_devices(self):
          pass
