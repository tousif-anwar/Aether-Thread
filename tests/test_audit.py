"""
Tests for aether-audit module.
"""

import unittest
import tempfile
from pathlib import Path
from aether_thread.audit import CodeAnalyzer, StaticScanner


class TestCodeAnalyzer(unittest.TestCase):
    """Test cases for CodeAnalyzer."""
    
    def test_detect_global_mutable_variable(self):
        """Test detection of global mutable variables."""
        code = """
global_list = []
global_dict = {}
"""
        analyzer = CodeAnalyzer("test.py")
        result = analyzer.analyze(code)
        
        self.assertEqual(len(result.findings), 2)
        self.assertEqual(result.findings[0].issue_type, "mutable_global")
        self.assertEqual(result.findings[1].issue_type, "mutable_global")
    
    def test_detect_class_attribute(self):
        """Test detection of class-level mutable attributes."""
        code = """
class MyClass:
    class_list = []
    class_dict = {}
"""
        analyzer = CodeAnalyzer("test.py")
        result = analyzer.analyze(code)
        
        self.assertEqual(len(result.findings), 2)
        self.assertTrue(all(f.issue_type == "mutable_class_attribute" for f in result.findings))
    
    def test_ignore_immutable_globals(self):
        """Test that immutable values don't trigger warnings."""
        code = """
global_int = 42
global_string = "hello"
global_tuple = (1, 2, 3)
"""
        analyzer = CodeAnalyzer("test.py")
        result = analyzer.analyze(code)
        
        self.assertEqual(len(result.findings), 0)
    
    def test_syntax_error_handling(self):
        """Test handling of syntax errors."""
        code = """
def broken(
    # Missing closing parenthesis
"""
        analyzer = CodeAnalyzer("test.py")
        result = analyzer.analyze(code)
        
        self.assertEqual(len(result.findings), 1)
        self.assertEqual(result.findings[0].issue_type, "syntax_error")


class TestStaticScanner(unittest.TestCase):
    """Test cases for StaticScanner."""
    
    def test_scan_directory(self):
        """Test scanning a directory of Python files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            file1 = Path(tmpdir) / "file1.py"
            file1.write_text("global_list = []")
            
            file2 = Path(tmpdir) / "file2.py"
            file2.write_text("x = 42")
            
            # Scan directory
            scanner = StaticScanner()
            results = scanner.scan(tmpdir)
            
            self.assertEqual(len(results), 2)
            
            # Check that we found the mutable global
            findings = scanner.total_findings
            self.assertTrue(any(f.issue_type == "mutable_global" for f in findings))
    
    def test_exclude_directories(self):
        """Test that excluded directories are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create venv directory
            venv_dir = Path(tmpdir) / "venv"
            venv_dir.mkdir()
            (venv_dir / "test.py").write_text("x = []")
            
            # Create regular file
            (Path(tmpdir) / "main.py").write_text("x = []")
            
            # Scan with default exclusions
            scanner = StaticScanner()
            results = scanner.scan(tmpdir)
            
            # Should only find main.py, not venv/test.py
            self.assertEqual(len(results), 1)


if __name__ == '__main__':
    unittest.main()
