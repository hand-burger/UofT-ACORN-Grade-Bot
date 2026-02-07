import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent directory to path so we can import main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import AcornBot

class TestAcornBot(unittest.TestCase):
    def setUp(self):
        self.bot = AcornBot()
        # Mock console to avoid cluttering output during tests
        self.bot.console = MagicMock()

    def test_parse_grades_success(self):
        """Test parsing of valid HTML content."""
        html_content = """
        <html>
            <body>
                <div class="courses blok">CSC108H1: Introduction to Computer Programming</div>
                <div class="courses blok">MAT137Y1: Calculus!</div>
                <div class="other">Irrelevant content</div>
            </body>
        </html>
        """
        courses = self.bot.parse_grades(html_content)
        
        self.assertEqual(len(courses), 2)
        self.assertIn("CSC108H1: Introduction to Computer Programming", courses)
        self.assertIn("MAT137Y1: Calculus!", courses)
        self.assertEqual(courses["CSC108H1: Introduction to Computer Programming"]['raw'], 
                         "CSC108H1: Introduction to Computer Programming")

    def test_parse_grades_empty(self):
        """Test parsing when no courses are present."""
        html_content = "<html><body><div>Nothing here</div></body></html>"
        courses = self.bot.parse_grades(html_content)
        self.assertEqual(len(courses), 0)

    def test_check_for_changes_no_initial_data(self):
        """Test change detection when starting from empty state."""
        new_courses = {"CSC108": {"raw": "CSC108"}}
        
        # First run (current_courses is empty)
        changes = self.bot.check_for_changes(new_courses)
        
        # Should initialize current_courses but return no changes (to avoid spam on startup)
        # Wait, looking at the code:
        # if not self.current_courses:
        #    self.current_courses = new_courses
        #    return []
        
        self.assertEqual(len(changes), 0)
        self.assertEqual(self.bot.current_courses, new_courses)

    def test_check_for_changes_no_change(self):
        """Test change detection when data is identical."""
        self.bot.current_courses = {"CSC108": {"raw": "CSC108"}}
        new_courses = {"CSC108": {"raw": "CSC108"}}
        
        changes = self.bot.check_for_changes(new_courses)
        self.assertEqual(len(changes), 0)

    def test_check_for_changes_new_course(self):
        """Test detection of a completely new course."""
        self.bot.current_courses = {"CSC108": {"raw": "CSC108"}}
        new_courses = {
            "CSC108": {"raw": "CSC108"},
            "MAT137": {"raw": "MAT137"}
        }
        
        changes = self.bot.check_for_changes(new_courses)
        self.assertEqual(len(changes), 1)
        self.assertIn("New update/grade: MAT137", changes[0])

    def test_check_for_changes_grade_update(self):
        """Test detection when a course entry changes text (e.g. grade updated)."""
        # Since the bot uses the full text string as the key, a change in grade 
        # appears as a "New entry" for the new string, and the old key is just ignored 
        # (effectively treating it as a new distinct entry).
        
        self.bot.current_courses = {"CSC108 - Grade: 80": {"raw": "CSC108 - Grade: 80"}}
        new_courses = {
            "CSC108 - Grade: 90": {"raw": "CSC108 - Grade: 90"}
        }
        
        changes = self.bot.check_for_changes(new_courses)
        self.assertEqual(len(changes), 1)
        self.assertIn("New update/grade: CSC108 - Grade: 90", changes[0])

    @patch('requests.Session.get')
    def test_fetch_grades_network_error(self, mock_get):
        """Test graceful handling of network errors."""
        mock_get.side_effect = Exception("Connection lost")
        
        result = self.bot.fetch_grades()
        
        self.assertIsNone(result)
        self.assertIn("Fetch error", self.bot.status_message)

if __name__ == '__main__':
    unittest.main()
