/////////////////////////////////////////////////////////////////////////////////////
// PopupKiller.cpp
//
// This program controls the DLL loading
//
// COMPILE with:
// cl.exe /EHsc PopupKiller.cpp advapi32.lib
/////////////////////////////////////////////////////////////////////////////////////

#undef UNICODE

#include <Windows.h>
#include <string>
#include <TlHelp32.h>
#include "Boyka.h"


int
main(int argc, char *argv[])
{
	HANDLE hThisProcess = 0;
	BOYKAPROCESSINFO bpiCon;

	if(argc < 2)
	{
		printf("Usage: %s <victim process name>\n", argv[0]);
		return 1;
	}
	
	char *victimSoftware = argv[1];

	/////////////////////////////////////////////////////////////////////////////////////
	// Change our privileges. We need to OpenProcess() with OPEN_ALL_ACCESS
	// in order to be able to debug another process.
	/////////////////////////////////////////////////////////////////////////////////////

	if(!OpenProcessToken(
			GetCurrentProcess(),	// handle
			TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY,
			&hThisProcess
			))
		{
			printf("[Debug - PrivEsc] Error (OpenProcessToken)\n");
			DisplayError();
			return 1;
		}

	if(SetPrivilege(hThisProcess, SE_DEBUG_NAME, TRUE))
		printf("[Debug - PrivEsc] Successfully set SeDebugPrivilege :)\n");
	else {
		printf("[Debug - PrivEsc] Unable to set SeDebugPrivilege :(\n");
		DisplayError();
		return 1;
	}

	
	// This snippet must be here (after Priv Escalation) since
	// it tries to get an ALL_ACCESS handle to the process.
	bpiCon = FindProcessByName(victimSoftware);

	if(bpiCon.Pid == 0)
	{
		printf("\n[debug] Process %s NOT found. Is it running?\n", victimSoftware);
		return 1;
	}


	char *DirPath = new char[MAX_PATH];
	char *FullPath = new char[MAX_PATH];
	GetCurrentDirectory(MAX_PATH, DirPath);
	sprintf_s(FullPath, MAX_PATH, "%s\\%s", DirPath, DLL_NAME);

	printf("[Debug - DLL inject] Proceed to inject DLL now...\n");

	/////////////////////////////////////////////////////////////////////////////
	// DLL injection sexiness starts here
	/////////////////////////////////////////////////////////////////////////////
	LPVOID LoadLibraryAddr =
			(LPVOID)GetProcAddress(GetModuleHandle("kernel32.dll"), "LoadLibraryA");

	LPVOID PathStringAlloc = (LPVOID)VirtualAllocEx(bpiCon.hProcess, NULL, strlen(FullPath),
			MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE); // allocate memory for the path string.

	WriteProcessMemory(bpiCon.hProcess, PathStringAlloc, FullPath,
			strlen(FullPath), NULL); // write the string to the victim's memory space.

	HANDLE hRemoteThread = CreateRemoteThread(bpiCon.hProcess, NULL, NULL, (LPTHREAD_START_ROUTINE)LoadLibraryAddr,
			PathStringAlloc, NULL, NULL); // new thread, execs LoadLibraryA("PathStringAlloc").

	if(hRemoteThread != NULL) {
		//printf("[Debug - DLL inject] Remote Thread created.\n");
		printf("[Debug - DLL inject] >o.O<  DLL %s injected.\n", FullPath);
	} else {
		printf("[Debug - DLL inject] Error! Remote Thread couldn't be created.\n");
		DisplayError();
		return 1;
	}

	// cleanup.
	delete [] DirPath;
	delete [] FullPath;
	CloseHandle(bpiCon.hProcess);
	CloseHandle(hThisProcess);

	return 0;
}
