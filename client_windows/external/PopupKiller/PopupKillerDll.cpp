//////////////////////////////////////////////////////////////////////////////////////////
// PopupKillerDll.cpp
//
// This DLL will be injected to the process by PopupKiller.
//
// COMPILE with:
// cl.exe /EHsc /LD PopupKillerDll.cpp user32.lib
//////////////////////////////////////////////////////////////////////////////////////////

#undef UNICODE

#include <Windows.h>
#include <string.h>
#include "Boyka.h"		// always the last one


/////////////////////////////////////////////////////////////////////
// Code gets executed at DLL loading time
// [...]
/////////////////////////////////////////////////////////////////////

BOOL APIENTRY DllMain(HMODULE hDLL, DWORD Reason, LPVOID Reserved)
{
	switch(Reason)
	{
		case DLL_PROCESS_ATTACH:
			// Simply show a message box :)
			MessageBox(NULL, 
				(LPCSTR)L"Process attach", 
				(LPCSTR)L"Test", 
				MB_YESNOCANCEL | MB_ICONEXCLAMATION);

			break;

		case DLL_PROCESS_DETACH:
			MessageBox(NULL, 
				(LPCSTR)L"Process detach", 
				(LPCSTR)L"Test", 
				MB_YESNOCANCEL | MB_ICONEXCLAMATION);

			break;

		case DLL_THREAD_ATTACH:
			MessageBox(NULL, 
				(LPCSTR)L"Thread attach", 
				(LPCSTR)L"Test", 
				MB_YESNOCANCEL | MB_ICONEXCLAMATION);

			break;

		case DLL_THREAD_DETACH:
			MessageBox(NULL, 
				(LPCSTR)L"Thread detach", 
				(LPCSTR)L"Test", 
				MB_YESNOCANCEL | MB_ICONEXCLAMATION);
			
			break;
	}
	return TRUE;
}
