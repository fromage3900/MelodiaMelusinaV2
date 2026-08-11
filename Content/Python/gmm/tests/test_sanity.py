import unittest

class TestSanity(unittest.TestCase):
    def test_logic_sanity(self):
        """A simple logic test to verify the test runner is working."""
        self.assertTrue(1 + 1 == 2)

if __name__ == '__main__':
    unittest.main()
