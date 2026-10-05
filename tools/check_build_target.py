"""Check replacement access without deleting or changing the existing executable."""
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import sys


def running_processes(path):
    if os.name != 'nt':
        return []
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    class Entry(ctypes.Structure):
        _fields_ = [('dwSize', wintypes.DWORD), ('cntUsage', wintypes.DWORD),
                    ('th32ProcessID', wintypes.DWORD), ('th32DefaultHeapID', ctypes.c_size_t),
                    ('th32ModuleID', wintypes.DWORD), ('cntThreads', wintypes.DWORD),
                    ('th32ParentProcessID', wintypes.DWORD), ('pcPriClassBase', wintypes.LONG),
                    ('dwFlags', wintypes.DWORD), ('szExeFile', wintypes.WCHAR * 260)]
    kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    for name in ('Process32FirstW', 'Process32NextW'):
        getattr(kernel, name).argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
    snapshot = kernel.CreateToolhelp32Snapshot(2, 0)
    if snapshot == wintypes.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    entry = Entry(); entry.dwSize = ctypes.sizeof(entry)
    found = []
    try:
        more = kernel.Process32FirstW(snapshot, ctypes.byref(entry))
        while more:
            if entry.szExeFile.casefold() == path.name.casefold():
                process = kernel.OpenProcess(0x1000, False, entry.th32ProcessID)
                matches = True  # Unreadable matching process: stop conservatively.
                if process:
                    try:
                        buffer = ctypes.create_unicode_buffer(32768)
                        size = wintypes.DWORD(len(buffer))
                        if kernel.QueryFullProcessImageNameW(process, 0, buffer, ctypes.byref(size)):
                            matches = os.path.normcase(buffer.value) == os.path.normcase(str(path))
                    finally:
                        kernel.CloseHandle(process)
                if matches: found.append(entry.th32ProcessID)
            more = kernel.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel.CloseHandle(snapshot)
    return found


def replacement_error(path):
    if os.name != 'nt' or not path.exists():
        return None
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                       wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    create.restype = wintypes.HANDLE
    close = kernel.CloseHandle
    close.argtypes = [wintypes.HANDLE]
    close.restype = wintypes.BOOL
    # Request DELETE access, sharing all operations, but never delete the file.
    handle = create(str(path), 0x10000, 7, None, 3, 0, None)
    if handle == wintypes.HANDLE(-1).value:
        return ctypes.get_last_error()
    close(handle)
    return None


def main():
    path = Path(__file__).resolve().parent.parent / 'dist' / 'LeerkrachtenTool.exe'
    try:
        processes = running_processes(path)
        error = 32 if processes else replacement_error(path)
    except OSError as exc:
        print(f'Kan de bouwcontrole niet uitvoeren: {exc}')
        return 1
    if error is None:
        return 0
    if processes:
        print('De bestaande toepassing draait nog. Procesnummers: '+', '.join(map(str, processes)))
    print(f'Kan de bestaande executable niet vervangen (Windows-fout {error}).')
    print(f'Bestand: {path}')
    print('Sla je werk op en sluit Leerkrachten Tool volledig af, inclusief de lokale server.')
    print('Alleen het browsertabblad sluiten stopt de server niet.')
    print('Controleer zo nodig in Taakbeheer of LeerkrachtenTool.exe nog actief is.')
    print('Start Build-exe.bat daarna opnieuw. Er is niets verwijderd of gecompileerd.')
    print('Is de tool al afgesloten? Controleer dan bestandsrechten en eventuele beveiligings-/synchronisatieblokkering.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
