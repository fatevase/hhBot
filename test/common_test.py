# tests/test_common.py

import unittest
# from unittest.mock import patch
from hhBot.common.hd2 import preserve_tags_and_translate

class TestPreserveTagsAndTranslate(unittest.TestCase):

    def test_preserve_tags_and_translate(self):
        # Mock the something
        # with patch('hhBot.common.common.translate_text') as mock_translate_text:
        
        # Test case 1: Simple text with tags
        text = "Hello [tag]world[/tag]"
        expected_output = ["您好[tag]世界[/tag]", "你好[tag]世界[/tag]"]
        result = preserve_tags_and_translate(text, 'zh')
        self.assertIn(result, expected_output, f"Expected '{expected_output}', but got '{result}'")
        
        # Test case 2: Text without tags
        text = "Hello world"
        expected_output = "你好，世界"
        result = preserve_tags_and_translate(text, 'zh')
        print(result)
        self.assertEqual(result, expected_output, f"Expected '{expected_output}', but got '{result}'")
        
        # Test case 3: Text with multiple tags
        text = "Hello [tag1]world[/tag1] and [tag2]everyone[/tag2]"
        expected_output = ["你好[tag1]世界[/tag1]和[tag2]大家好[/tag2]", "你好[tag1]世界[/tag1]和[tag2]每个人[/tag2]"]
        result = preserve_tags_and_translate(text, 'zh').replace('您', '你').replace('及', '和')
        self.assertIn(result, expected_output, f"Expected '{expected_output}', but got '{result}'")

if __name__ == '__main__':
    unittest.main()