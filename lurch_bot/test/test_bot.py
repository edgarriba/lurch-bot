import unittest

from lurch_bot import lurch

class TestUM(unittest.TestCase):

	def setUp(self):
        	self.bot = lurch.Bot()
		pass

	def test_01(self):
		self.assertNotEqual(self.bot, None)

if __name__ == '__main__':
    unittest.main()
