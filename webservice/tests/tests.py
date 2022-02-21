# import unittest
# from cors_webservice import create_app
# from config import Test
#
#
# class CorsModelTestCase(unittest.TestCase):
#     def setUp(self) -> None:
#         self.app = create_app(Test)
#         self.app_context = self.app.app_context()
#         self.app_context.push()
#         db.create_all()
#
#     def tearDown(self) -> None:
#         db.session.remove()
#         db.drop_all()
#         self.app_context.pop()
#
#
# if __name__ == '__main__':
#     unittest.main(verbosity=2)
