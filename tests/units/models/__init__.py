# from sqlalchemy import event
# from sqlalchemy.orm import sessionmaker
# from quactrl.domain.persistence import dal
# from unittest.mock import Mock


# class EmptyDataTest:
#     def setup_class(cls):
#         dal.connect('sqlite:///:memory:')
#         cls.Session = sessionmaker()

#     def setup_method(self, method):
#         self.dal = dal
#         # Override session on dal to avoid Scoped Session
#         self._transaction = dal.connection.begin()
#         self.session = self.Session(bind=dal.connection)
#         # Mocking dal session with non scoped_session
#         dal.Session = Mock()
#         dal.Session.return_value = self.session

#     def teardown_method(self, method):
#         self.session.close()
#         self._transaction.rollback()


# class DataTest(EmptyDataTest):
#     pass
