"""
GIL Status Checker: Verify environment supports free-threaded Python.

Checks:
1. Is GIL currently enabled or disabled? (sys._is_gil_enabled())
2. Which packages are thread-safe or require GIL?
3. Environment compatibility for free-threaded builds
"""

import sys
import sysconfig
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import importlib.util


class GILStatus(Enum):
    """GIL operational status."""
    ENABLED = "enabled"           # GIL is ENABLED - standard Python
    DISABLED = "disabled"         # GIL is DISABLED - free-threaded Python
    BUILD_SUPPORT = "build_support"  # Binary supports disabling, but not yet disabled
    UNKNOWN = "unknown"


@dataclass
class EnvironmentStatus:
    """Status of the Python environment."""
    gil_status: GILStatus
    python_version: str
    build_info: str
    is_free_threaded_build: bool
    can_disable_gil: bool
    free_threaded_packages: List[str]
    potentially_unsafe_packages: List[str]


class GILStatusChecker:
    """Check if environment is ready for free-threaded Python."""
    
    def __init__(self):
        self.gil_status = self._check_gil_status()
        self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        self.build_info = self._get_build_info()
    
    def _check_gil_status(self) -> GILStatus:
        """Check if GIL is currently enabled or disabled."""
        # Check for sys._is_gil_enabled() (Python 3.13+)
        if hasattr(sys, '_is_gil_enabled'):
            return GILStatus.DISABLED if not sys._is_gil_enabled() else GILStatus.ENABLED
        
        # Check build configuration
        if self._is_free_threaded_build():
            return GILStatus.BUILD_SUPPORT
        
        return GILStatus.UNKNOWN
    
    def _is_free_threaded_build(self) -> bool:
        """Check if Python is built with free-threading support."""
        try:
            # Check for --disable-gil in build flags
            config_vars = sysconfig.get_config_vars()
            
            # Several indicators
            if config_vars.get('Py_NOGIL'):
                return True
            
            if 'free_threaded' in sys.version.lower():
                return True
            
            # Check for "t" suffix in implementation
            if hasattr(sys, 'implementation'):
                if 't' in str(sys.implementation.version):
                    return True
            
            return False
        except:
            return False
    
    def _get_build_info(self) -> str:
        """Get detailed build information."""
        info_parts = []
        
        # Python build info
        info_parts.append(f"Implementation: {sys.implementation.name}")
        if hasattr(sys, 'implementation'):
            info_parts.append(f"Version: {sys.implementation.version}")
        
        # Compiler info
        if hasattr(sys, 'compiler'):
            info_parts.append(f"Compiler: {sys.compiler}")
        
        # Platform
        info_parts.append(f"Platform: {sys.platform}")
        
        return " | ".join(info_parts)
    
    def check_imports(self, module_names: List[str]) -> Dict[str, str]:
        """
        Check which modules successfully import without forcing GIL.
        
        Returns: {"module_name": "status"}
           status in ("safe", "unsafe", "forces_gil", "not_installed")
        """
        results = {}
        
        for module_name in module_names:
            try:
                spec = importlib.util.find_spec(module_name)
                if spec is None:
                    results[module_name] = "not_installed"
                else:
                    # Try to import and check metadata
                    mod = importlib.import_module(module_name)
                    
                    # Check for known thread-safe packages
                    if self._is_known_safe(module_name):
                        results[module_name] = "safe"
                    elif self._is_known_unsafe(module_name):
                        results[module_name] = "unsafe"
                    else:
                        results[module_name] = "unknown"
            except Exception as e:
                results[module_name] = f"error: {str(e)}"
        
        return results
    
    def _is_known_safe(self, module_name: str) -> bool:
        """Check if module is known to be thread-safe in free-threaded Python."""
        safe_modules = {
            'threading',
            'queue', 
            'concurrent',
            'asyncio',
            'multiprocessing',
            'array',
            'collections',
            'heapq',
            'bisect',
            'datetime',
            'decimal',
            'fractions',
            'numbers',
            'json',
        }
        
        base_name = module_name.split('.')[0]
        return base_name in safe_modules
    
    def _is_known_unsafe(self, module_name: str) -> bool:
        """Check if module requires GIL or has known threading issues."""
        unsafe_modules = {
            'numpy',  # Some operations still require GIL
            'scipy',  # Depends on numpy
            'pandas',  # Many operations not thread-safe
            'sqlite3',  # Requires GIL
            'pickle',  # Not thread-safe
        }
        
        base_name = module_name.split('.')[0]
        return base_name in unsafe_modules
    
    def get_status(self) -> EnvironmentStatus:
        """Get comprehensive environment status."""
        # Check common packages
        common_packages = [
            'numpy', 'pandas', 'scipy', 'requests', 'django',
            'flask', 'scipy', 'asyncio', 'concurrent'
        ]
        
        import_results = self.check_imports(common_packages)
        
        free_threaded = [
            name for name, status in import_results.items() 
            if status == "safe"
        ]
        unsafe = [
            name for name, status in import_results.items()
            if status == "unsafe"
        ]
        
        return EnvironmentStatus(
            gil_status=self.gil_status,
            python_version=self.python_version,
            build_info=self.build_info,
            is_free_threaded_build=self._is_free_threaded_build(),
            can_disable_gil=self.gil_status != GILStatus.UNKNOWN,
            free_threaded_packages=free_threaded,
            potentially_unsafe_packages=unsafe
        )
    
    def print_status(self):
        """Print comprehensive status report."""
        status = self.get_status()
        
        print("\n" + "="*70)
        print("🔍 FREE-THREADED PYTHON ENVIRONMENT STATUS")
        print("="*70)
        
        # GIL Status
        if status.gil_status == GILStatus.ENABLED:
            icon = "🔴"
            text = "ENABLED (standard Python)"
        elif status.gil_status == GILStatus.DISABLED:
            icon = "🟢"
            text = "DISABLED (free-threaded!)"
        elif status.gil_status == GILStatus.BUILD_SUPPORT:
            icon = "🟡"
            text = "Build supports disabling (not yet disabled)"
        else:
            icon = "⚫"
            text = "UNKNOWN"
        
        print(f"\n{icon} GIL Status: {text}")
        print(f"Python Version: {status.python_version}")
        print(f"Build: {status.build_info}")
        
        # Packages
        print(f"\n📦 Package Compatibility:")
        if status.free_threaded_packages:
            print(f"  ✅ Free-Threaded: {', '.join(status.free_threaded_packages[:5])}")
            if len(status.free_threaded_packages) > 5:
                print(f"     ... and {len(status.free_threaded_packages)-5} more")
        
        if status.potentially_unsafe_packages:
            print(f"  ⚠️ Potentially Unsafe: {', '.join(status.potentially_unsafe_packages[:5])}")
            if len(status.potentially_unsafe_packages) > 5:
                print(f"     ... and {len(status.potentially_unsafe_packages)-5} more")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if status.gil_status == GILStatus.ENABLED:
            print("  • This is standard Python (GIL enabled)")
            print("  • To use free-threaded Python, install Python 3.13+ with --disable-gil")
        elif status.gil_status == GILStatus.DISABLED:
            print("  • ✅ You're running free-threaded Python!")
            print("  • Use aether-tools to optimize for no-GIL execution")
            if status.potentially_unsafe_packages:
                print(f"  • Note: {', '.join(status.potentially_unsafe_packages)} may need special handling")
        
        print("="*70 + "\n")


def get_gil_status() -> GILStatus:
    """Quick check of current GIL status."""
    return GILStatusChecker().gil_status


def is_free_threaded() -> bool:
    """Check if running in free-threaded mode."""
    checker = GILStatusChecker()
    return checker.gil_status == GILStatus.DISABLED
