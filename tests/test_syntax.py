"""Basic syntax tests to ensure modules can be compiled"""

import py_compile
import tempfile
import os
from pathlib import Path


def test_ocr_service_syntax():
    """Test that OCR service module compiles without syntax errors"""
    ocr_service_path = Path(__file__).parent.parent / "app" / "services" / "ocr_service.py"
    assert ocr_service_path.exists()
    
    # This will raise SyntaxError if there are syntax issues
    with tempfile.NamedTemporaryFile(suffix='.pyc', delete=False) as temp_file:
        try:
            py_compile.compile(str(ocr_service_path), cfile=temp_file.name, doraise=True)
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)


def test_endpoints_syntax():
    """Test that endpoints module compiles without syntax errors"""
    endpoints_path = Path(__file__).parent.parent / "app" / "api" / "v1" / "endpoints.py"
    assert endpoints_path.exists()
    
    # This will raise SyntaxError if there are syntax issues
    with tempfile.NamedTemporaryFile(suffix='.pyc', delete=False) as temp_file:
        try:
            py_compile.compile(str(endpoints_path), cfile=temp_file.name, doraise=True)
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)


def test_schemas_syntax():
    """Test that schemas module compiles without syntax errors"""
    schemas_path = Path(__file__).parent.parent / "app" / "schemas.py"
    assert schemas_path.exists()
    
    # This will raise SyntaxError if there are syntax issues
    with tempfile.NamedTemporaryFile(suffix='.pyc', delete=False) as temp_file:
        try:
            py_compile.compile(str(schemas_path), cfile=temp_file.name, doraise=True)
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)


def test_main_module_syntax():
    """Test that main module compiles without syntax errors"""
    main_path = Path(__file__).parent.parent / "app" / "main.py"
    assert main_path.exists()
    
    # This will raise SyntaxError if there are syntax issues
    with tempfile.NamedTemporaryFile(suffix='.pyc', delete=False) as temp_file:
        try:
            py_compile.compile(str(main_path), cfile=temp_file.name, doraise=True)
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)