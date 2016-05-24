import unittest

from lurch_bot import lurch

class TestUM(unittest.TestCase):

	def setUp(self):
        	self.bot = lurch.Bot()
		pass

	def test_01(self):
		self.assertNotEqual(self.bot, None)

	def test_02(self):
		self.assertEqual(len(self.bot.token), 45)

if __name__ == '__main__':
    unittest.main()
