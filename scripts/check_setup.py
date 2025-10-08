#!/usr/bin/env python3
"""
Setup Validation Script
Checks if all requirements are met before running the application
"""

import sys
import os
from pathlib import Path
import importlib.util

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_status(check_name, passed, message=""):
    """Print check status"""
    status = "✅" if passed else "❌"
    print(f"{status} {check_name}")
    if message:
        print(f"   {message}")

def check_python_version():
    """Check Python version"""
    print_header("Python Version Check")
    version = sys.version_info
    required = (3, 8)
    
    passed = version >= required
    print_status(
        "Python Version",
        passed,
        f"Found: {version.major}.{version.minor}.{version.micro}, "
        f"Required: {required[0]}.{required[1]}+"
    )
    return passed

def check_required_packages():
    """Check if required packages are installed"""
    print_header("Required Packages Check")
    
    packages = {
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'chromadb': 'ChromaDB',
        'sentence_transformers': 'Sentence-Transformers',
        'google.generativeai': 'Google Generative AI',
        'streamlit': 'Streamlit',
        'pandas': 'Pandas',
        'numpy': 'NumPy',
        'requests': 'Requests',
        'pydantic': 'Pydantic',
        'dotenv': 'Python-Dotenv'
    }
    
    all_passed = True
    for module_name, display_name in packages.items():
        spec = importlib.util.find_spec(module_name.replace('-', '_'))
        passed = spec is not None
        all_passed = all_passed and passed
        print_status(display_name, passed)
    
    if not all_passed:
        print("\n   Install missing packages with:")
        print("   pip install -r requirements.txt")
    
    return all_passed

def check_project_structure():
    """Check if project structure is correct"""
    print_header("Project Structure Check")
    
    project_root = Path(__file__).parent.parent
    
    required_files = {
        'Property_data.csv': 'Dataset file',
        'requirements.txt': 'Requirements file',
        'backend/main.py': 'Backend server',
        'backend/rag_pipeline.py': 'RAG pipeline',
        'backend/vector_store.py': 'Vector store',
        'backend/llm_handler.py': 'LLM handler',
        'backend/data_ingestion.py': 'Data ingestion',
        'frontend/app.py': 'Frontend application',
        'scripts/load_data.py': 'Data loading script'
    }
    
    all_passed = True
    for file_path, description in required_files.items():
        full_path = project_root / file_path
        passed = full_path.exists()
        all_passed = all_passed and passed
        print_status(f"{description} ({file_path})", passed)
    
    return all_passed

def check_directories():
    """Check if required directories exist"""
    print_header("Directory Structure Check")
    
    project_root = Path(__file__).parent.parent
    
    directories = {
        'backend': 'Backend directory',
        'frontend': 'Frontend directory',
        'scripts': 'Scripts directory',
        'evaluation': 'Evaluation directory',
        'tests': 'Tests directory'
    }
    
    all_passed = True
    for dir_path, description in directories.items():
        full_path = project_root / dir_path
        passed = full_path.exists() and full_path.is_dir()
        all_passed = all_passed and passed
        print_status(description, passed)
    
    return all_passed

def check_environment_file():
    """Check if .env file exists"""
    print_header("Environment Configuration Check")
    
    project_root = Path(__file__).parent.parent
    env_file = project_root / '.env'
    
    if env_file.exists():
        print_status(".env file exists", True)
        
        # Check for API key
        with open(env_file, 'r') as f:
            content = f.read()
            has_api_key = 'GEMINI_API_KEY' in content
            
            if has_api_key:
                # Check if it's not empty
                for line in content.split('\n'):
                    if line.startswith('GEMINI_API_KEY='):
                        value = line.split('=', 1)[1].strip()
                        if value and value != '':
                            print_status("Gemini API key configured", True, "AI responses enabled")
                        else:
                            print_status("Gemini API key configured", False, 
                                       "Key is empty - using fallback responses")
                        break
            else:
                print_status("Gemini API key configured", False, 
                           "Key not found - using fallback responses")
        
        return True
    else:
        print_status(".env file exists", False)
        print("   Create .env file from .env.example:")
        print("   cp .env.example .env")
        return False

def check_vector_database():
    """Check if vector database exists"""
    print_header("Vector Database Check")
    
    project_root = Path(__file__).parent.parent
    db_path = project_root / 'backend' / 'chroma_db'
    
    if db_path.exists():
        # Check if it has data
        has_files = any(db_path.iterdir())
        print_status("ChromaDB directory exists", True)
        
        if has_files:
            print_status("Database has data", True, "Ready to query")
        else:
            print_status("Database has data", False, 
                       "Run: python scripts/load_data.py")
        
        return has_files
    else:
        print_status("ChromaDB directory exists", False)
        print("   Database not initialized. Run:")
        print("   python scripts/load_data.py")
        return False

def check_csv_file():
    """Check if CSV data file exists and is valid"""
    print_header("Dataset Check")
    
    project_root = Path(__file__).parent.parent
    csv_path = project_root / 'Property_data.csv'
    
    if csv_path.exists():
        file_size = csv_path.stat().st_size / (1024 * 1024)  # MB
        print_status("Dataset file exists", True, f"Size: {file_size:.1f} MB")
        
        # Try to count lines
        try:
            with open(csv_path, 'r') as f:
                line_count = sum(1 for _ in f)
            print_status("Dataset is readable", True, f"~{line_count:,} records")
            return True
        except Exception as e:
            print_status("Dataset is readable", False, f"Error: {e}")
            return False
    else:
        print_status("Dataset file exists", False)
        print("   Property_data.csv not found in project root")
        return False

def print_summary(checks_passed, total_checks):
    """Print summary"""
    print_header("Summary")
    
    percentage = (checks_passed / total_checks * 100) if total_checks > 0 else 0
    
    print(f"\nPassed: {checks_passed}/{total_checks} ({percentage:.0f}%)")
    
    if checks_passed == total_checks:
        print("\n🎉 All checks passed! You're ready to run the application.")
        print("\nNext steps:")
        print("1. Start backend:  cd backend && python main.py")
        print("2. Start frontend: streamlit run frontend/app.py")
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        print("\nCommon solutions:")
        print("- Install packages: pip install -r requirements.txt")
        print("- Load data: python scripts/load_data.py")
        print("- Create .env: cp .env.example .env")

def main():
    """Run all checks"""
    print("\n" + "="*70)
    print("  PROPERTY RAG SYSTEM - SETUP VALIDATION")
    print("="*70)
    
    checks = [
        ("Python Version", check_python_version),
        ("Required Packages", check_required_packages),
        ("Project Structure", check_project_structure),
        ("Directory Structure", check_directories),
        ("Dataset File", check_csv_file),
        ("Environment Config", check_environment_file),
        ("Vector Database", check_vector_database)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Error running check '{name}': {e}")
            results.append(False)
    
    checks_passed = sum(results)
    total_checks = len(results)
    
    print_summary(checks_passed, total_checks)
    print()

if __name__ == "__main__":
    main()
