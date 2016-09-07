/////////////////////////////////////////////////////////////////////////////////////
// Boyka.h
//
// Definitions and stuff.
/////////////////////////////////////////////////////////////////////////////////////

// Header guards are good ;)
#ifndef _BOYKA_H
#define _BOYKA_H

#include <Windows.h>

#define DLL_NAME "PopupKiller.dll"
#define DllExport __declspec(dllexport) // for readability
#define BOYKA_BUFLEN 1024

// Process information (short)
typedef struct
{
	char*	szExeName;
	DWORD	Pid;
	HANDLE	hProcess;
} BOYKAPROCESSINFO;

/////////////////////////////////////////////////////////////////////////////////////
// Custom function declarations.
/////////////////////////////////////////////////////////////////////////////////////
BOYKAPROCESSINFO FindProcessByName(char *);
BOOL SetPrivilege(HANDLE, LPCTSTR, BOOL); // I love MSDN :)
void DisplayError(void);


#endif	// _BOYKA_H