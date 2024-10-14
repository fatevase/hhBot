import unittest
from unittest.mock import patch, mock_open, MagicMock
import json
from pathlib import Path

# 假设 fetch_and_update_assignments 函数在 hhBot.common.hd2 模块中
from hhBot.common.hd2 import fetch_and_update_assignments

NEW_ASSIGNMENTS_FILE = 'new_assignments.json'
HISTORY_ASSIGNMENTS_FILE = 'history_assignments.json'

class TestFetchAndUpdateAssignments(unittest.TestCase):

    @patch('hhBot.common.hd2.requests.get')
    @patch('hhBot.common.hd2.Path.exists', return_value=True)
    def test_fetch_and_update_assignments(self, mock_exists, mock_get):
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.json.return_value = [{
            "id32": 738112495,
            "progress": [1, 1, 1, 0],
            "expiresIn": 12069,
            "setting": {
                "type": 4,
                "overrideTitle": "MAJOR ORDER",
                "overrideBrief": "The Supercolony has caused sudden outbreaks on multiple planets. They must be contained immediately.",
                "taskDescription": "Liberate all designated planets.",
                "tasks": [
                    {
                        "type": 11,
                        "values": [1, 1, 79],
                        "valueTypes": [3, 11, 12]
                    },
                    {
                        "type": 11,
                        "values": [1, 1, 127],
                        "valueTypes": [3, 11, 12]
                    }
                ],
                "reward": {
                    "type": 1,
                    "id32": 897894480,
                    "amount": 40
                },
                "flags": 0
            }
        }]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # Mock the file read/write operations
        m_open = mock_open()
        handle = m_open()
        handle.read.side_effect = [
            json.dumps({"id32": 738112494}),  # NEW_ASSIGNMENTS_FILE read
            json.dumps([])  # HISTORY_ASSIGNMENTS_FILE read
        ]

        with patch('builtins.open', m_open):
            # Mock the JSON files for reward and task types
            with patch('hhBot.common.hd2.load_json') as mock_load_json:
                mock_load_json.side_effect = lambda x: {
                    'data/json/assignments/reward/type.json': {"1": "Medals"},
                    'data/json/assignments/tasks/types.json': {
                        "2": "Extract",
                        "3": "Eradicate",
                        "11": "Liberation",
                        "12": "Defense",
                        "13": "Control",
                        "15": "Expand"
                    },
                    'data/json/assignments/tasks/values.json': {
                        "2": "Planet Index"
                    },
                    'data/json/assignments/tasks/valueTypes.json': {
                        "1": "race",
                        "2": "unknown",
                        "3": "goal",
                        "4": "unit_id",
                        "5": "item_id",
                        "11": "liberate",
                        "12": "planet_index"
                    }
                }.get(x, {})

                # Call the function
                result = fetch_and_update_assignments()

                # Expected output
                expected_output = {
                    "time": 12069,
                    "title": "MAJOR ORDER",
                    "reward": {
                        "type": "Medals",
                        "id": 897894480,
                        "amount": 40
                    },
                    "targets": [
                        {
                            "type": "Liberation",
                            "values": ["Unknown", "Unknown", "Unknown"],
                            "valueTypes": ["goal", "liberate", "planet_index"]
                        },
                        {
                            "type": "Liberation",
                            "values": ["Unknown", "Unknown", "Unknown"],
                            "valueTypes": ["goal", "liberate", "planet_index"]
                        }
                    ]
                }

                # Assertions
                self.assertEqual(result, expected_output, f"Expected '{expected_output}', but got '{result}'")

if __name__ == '__main__':
    unittest.main()