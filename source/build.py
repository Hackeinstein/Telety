import os
import shutil
import subprocess
import sys
from pathlib import Path

def clear_directory(path):
    """Clear directory contents if it exists, create if it doesn't"""
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)

def modify_main_file(build_dir):
    """Modify main.py to handle stdout/stderr properly"""
    main_path = os.path.join(build_dir, 'main.py')
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove problematic stdin/stdout handling
    modified_content = content.replace(
        """if hasattr(sys, 'frozen'):
    sys.stdin = open(os.devnull, 'r')
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')""",
        """import codecs
if hasattr(sys, 'frozen'):
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())"""
    )

    with open(main_path, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    print("✓ Modified main.py for proper encoding")

def copy_required_files(build_dir):
    """Copy necessary files to build directory"""
    files_to_copy = [
        'main.py',
        'add.py',
        'config.py',
        'login.py',
        'post.py',
        'scrape.py',
        'session_manager.py'
    ]
    
    print("📁 Copying source files...")
    for file in files_to_copy:
        shutil.copy(file, build_dir)
        print(f"✓ Copied {file}")

def create_spec_file(build_dir):
    """Create custom spec file for PyInstaller"""
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[r'{build_dir}'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'telethon',
        'qrcode',
        'cryptography',
        'asyncio',
        'logging',
        'json',
        'datetime'
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TELETY',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TELETY',
)
"""
    spec_path = os.path.join(build_dir, 'TELETY.spec')
    with open(spec_path, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    return spec_path

def build_executable(build_dir, spec_file):
    """Build the executable using PyInstaller"""
    try:
        print("\n🚀 Starting build process...")
        
        # Install required packages
        print("\n📦 Installing dependencies...")
        subprocess.run([
            sys.executable, 
            '-m', 
            'pip', 
            'install', 
            'pyinstaller',
            'telethon',
            'qrcode',
            'cryptography'
        ], check=True)
        
        # Run PyInstaller
        print("\n🔨 Building executable...")
        subprocess.run([
            'pyinstaller',
            '--clean',
            '--workpath', os.path.join(build_dir, 'build'),
            '--distpath', os.path.join(build_dir, 'dist'),
            spec_file
        ], check=True)
        
        print("\n✅ Build completed successfully!")
        print(f"📁 Executable location: {os.path.join(build_dir, 'dist', 'TELETY')}")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed: {str(e)}")
        raise
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        raise

def main():
    """Main build coordinator"""
    try:
        # Setup build directory
        build_dir = os.path.join(os.getcwd(), 'build')
        clear_directory(build_dir)
        print(f"\n📁 Created build directory: {build_dir}")
        
        # Copy files and modify them
        copy_required_files(build_dir)
        modify_main_file(build_dir)
        
        # Create spec and build
        spec_file = create_spec_file(build_dir)
        build_executable(build_dir, spec_file)
        
    except Exception as e:
        print(f"\n💥 Build failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()