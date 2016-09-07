/////////////////////////////////////////////////////////////////////////////////////
// BoykaSystem.cpp
//
// This module contains functions dealing with system operations.
// The snapshotting (save and restore process state) is implemented here.
// Some other auxiliary functions to, for example elevate our privileges,
// are included here as well.
//
/////////////////////////////////////////////////////////////////////////////////////

#undef UNICODE

#include <Windows.h>
#include <vector>
#include <string>
#include <TlHelp32.h>
#include "Boyka.h"

/////////////////////////////////////////////////////////////////////////////////////
// SetPrivilege()
//
// Desc: Auxiliary function. You need to set SeDebugPrivilege in order to
// open the process with OPEN_ALL_ACCESS privs.
/////////////////////////////////////////////////////////////////////////////////////
BOOL SetPrivilege(HANDLE hToken, LPCTSTR lpszPrivilege, BOOL bEnablePrivilege)
{
	TOKEN_PRIVILEGES tp = {0};
	LUID luid;
	DWORD cb = sizeof(TOKEN_PRIVILEGES);

	if(!LookupPrivilegeValue(NULL, lpszPrivilege, &luid)) // finds LUID for privilege
		{
			printf("[Debug - Priv Esc] Error (LookupPrivilegeValue)");
			DisplayError();
			return FALSE;
		}

	// Get current privilege setting.
	tp.PrivilegeCount			= 1;
	tp.Privileges[0].Luid		= luid;

	if(bEnablePrivilege)
		{
			tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED;

		}
	else {
			tp.Privileges[0].Attributes = 0;
	}

	AdjustTokenPrivileges(
			hToken,
			FALSE,
			&tp,
			cb,
			NULL,
			NULL
			);

	if(GetLastError() != ERROR_SUCCESS)
		{
			printf("[Debug - Priv Esc] Error (AdjustTokenPrivileges)\n");
			DisplayError();
			return FALSE;
		}


	return TRUE;
}


/////////////////////////////////////////////////////////////////////////////////////
// Look for a process using the executable name.
// Returns a BOYKAPROCESSINFO structure.
/////////////////////////////////////////////////////////////////////////////////////

BOYKAPROCESSINFO
FindProcessByName(char *szExeName)
{
	BOYKAPROCESSINFO bpi;
	// Structure initialization
	bpi.hProcess = NULL;
	bpi.Pid = 0;
	bpi.szExeName = (char *)malloc(BOYKA_BUFLEN);

	PROCESSENTRY32 pe32;
	pe32.dwSize = sizeof(PROCESSENTRY32); // initialization.

	HANDLE hTool32 = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, NULL);
	BOOL bProcess = Process32First(hTool32, &pe32);

	if(bProcess == TRUE)
	{
		while((Process32Next(hTool32, &pe32)) == TRUE)
		{
			if(strcmp(pe32.szExeFile, szExeName) == 0)
			{
				// Found. Populate the struct.
				strncpy(bpi.szExeName, pe32.szExeFile, sizeof(pe32.szExeFile));
				bpi.Pid = pe32.th32ProcessID;

				printf("[Debug - FindProcessByName] Found %s [%d]\n", bpi.szExeName, bpi.Pid);


				if((bpi.hProcess = OpenProcess(PROCESS_ALL_ACCESS,
						FALSE, bpi.Pid)) == NULL)
					{
						printf("Couldn't open a handle to %s\n", bpi.szExeName);
						DisplayError();
						printf("ABORTING.");
						ExitProcess(1);
					}
				//else
				//	printf("[Debug - FindProcessByName] Got an ALL_ACCESS handle to process.\n");


			} // if strcmp... closing bracket
		} // while closing bracket
	}
	// Cleanup
	CloseHandle(hTool32);

	return bpi;
}


/////////////////////////////////////////////////////////////////////////////////////
// Just a little nice auxiliary function.
// Allows for verbose debug info regarding errors.
/////////////////////////////////////////////////////////////////////////////////////
void DisplayError()
{
	LPTSTR MessageBuffer;
	DWORD dwBufferLength;

	dwBufferLength = FormatMessage(
			FORMAT_MESSAGE_ALLOCATE_BUFFER |
			FORMAT_MESSAGE_FROM_SYSTEM,
			NULL,
			GetLastError(),
			GetSystemDefaultLangID(),
			(LPTSTR) &MessageBuffer,
			0,
			NULL
			);

	if(dwBufferLength)
		printf("[Debug] Error %u: %s\n", GetLastError(), MessageBuffer);

}