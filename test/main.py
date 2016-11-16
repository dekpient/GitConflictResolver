import unittest, os
from modules import conflict_re

class TestFeatures(unittest.TestCase):

  def setUp(self):
    path = os.path.dirname(__file__)
    with open(path + '/before.txt', 'r') as file:
      self.file = file.read()
    with open( path + '/swap_success.txt', 'r') as file:
      self.swapSuccess = file.read()
    with open( path + '/keep_both_success.txt', 'r') as file:
      self.keep_both_success = file.read()

  def testSwap(self):
    swapped_text = conflict_re.swap(self.file)
    self.assertEqual(swapped_text, self.swapSuccess)

  def testKeepBoth(self):
    new_text = conflict_re.keepBoth(self.file)
    self.assertEqual(new_text, self.keep_both_success)


def main():
    unittest.main()

if __name__ == '__main__':
    main()