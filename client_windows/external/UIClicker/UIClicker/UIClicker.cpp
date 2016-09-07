//
// UIClicker.cpp : Defines the entry point for the console application.
// Clunky Method:
// 1. Find PID by name
// 2. Find Hwnd by PID
// 3. Find Button by Hwnd
// 4. Send message
//

#include "stdafx.h"
#include <stdio.h>
#include <windows.h>
#include <vector>
#include <TlHelp32.h>
#include "UIClicker.h"

using namespace std;

typedef struct{
	DWORD Pid;
	BSTR windowTitle;
	vector<BSTR> buttonTexts;
	vector<HWND> WindowHandles;
	HWND ButtonHandle;
} UINFORMATION;

UINFORMATION ui;


int main(int argc, char *argv[])
{
	if (argc < 5)
	{
		printf("Usage:\n");
		printf("%s <process name> <window title (partial)> <button text (a,b,c)> <sleep timer (ms.)>\n", argv[0]);
		return 1;
	}

	// Globals. Globals everywhere...
	ui.Pid = 0;
	ui.windowTitle = Ansi2Unicode(argv[2]);
	ProcessButtonText(argv[3]);

	// Milliseconds
	DWORD SLEEPTIMER = atoi(argv[4]);

	while (1)
	{
		Sleep(SLEEPTIMER);

		// Wait for the process to start
		ui.Pid = FindProcessByName(Ansi2Unicode(argv[1]));
		if (ui.Pid == 0)
		{
			printf("[!] Process %s not found.\n", argv[1]);
			continue;
		}

		// Enumerate all window handles and check 
		// if their associated Pid matches
		ui.WindowHandles = {};
		EnumWindows(EnumWindowsProc, NULL);

		for (unsigned int i = 0; i < ui.WindowHandles.size(); i++)
		{
			if (ui.WindowHandles[i] == NULL)
			{
				printf("[!] Could not find Window Handle\n");
				continue;
			}

			// Winspy++ helps with this
			for (unsigned int j = 0; j < ui.buttonTexts.size(); j++)
			{
				ui.ButtonHandle = FindWindowEx(
					ui.WindowHandles[i],
					NULL,
					L"Button",
					ui.buttonTexts[j]);

				if (ui.ButtonHandle == NULL)
				{
					wprintf(L"[!] Could not find handle for button %s\n", 
						ui.buttonTexts[j]);
					continue;
				}
				wprintf(L"[*] Clicking button \"%s\" with Handle: %08x\n", 
					ui.buttonTexts[j], ui.ButtonHandle);

				// Send a message to the button that you are "clicking".
				SendMessage(
					ui.ButtonHandle,
					BM_CLICK,
					0,
					0);
			}
		}
	}

	return 0;
}


DWORD FindProcessByName(LPCWSTR wExeName)
{
	DWORD Pid = 0;
	PROCESSENTRY32 pe32;
	pe32.dwSize = sizeof(PROCESSENTRY32); // initialization.

	HANDLE hTool32 = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, NULL);
	BOOL bProcess = Process32First(hTool32, &pe32);

	wprintf(L"[*] Searching for %s...\n", wExeName);

	if (bProcess == TRUE)
	{
		while ((Process32Next(hTool32, &pe32)) == TRUE)
		{
			// NOTE: This comparison is case-insensitive :)
			if (lstrcmpi(pe32.szExeFile, wExeName) == 0)
			{
				// Found. Get the PID
				Pid = pe32.th32ProcessID;
				wprintf(L"[*] Found %s [%d]\n", wExeName, Pid);


			} // if strcmp... closing bracket
		} // while closing bracket
	}
	// Cleanup
	CloseHandle(hTool32);

	return Pid;
}


BSTR Ansi2Unicode(char *ansiStr)
{
	int l = lstrlenA(ansiStr);
	BSTR unicodeStr = SysAllocStringLen(NULL, l);
	MultiByteToWideChar(CP_ACP, 0, ansiStr, l, unicodeStr, l);

	return unicodeStr;
}


BOOL CALLBACK EnumWindowsProc(HWND hwnd, LPARAM lParam)
{
	// I will go to C hell for this...
	wchar_t class_name[1024];
	wchar_t title[1024];
	DWORD windowPid = 0;

	GetClassName(hwnd, class_name, sizeof(class_name));
	GetWindowText(hwnd, title, sizeof(title));

	if (_tcsstr(title, ui.windowTitle))
	{
		GetWindowThreadProcessId(hwnd, &windowPid);
		if (windowPid != ui.Pid)
		{
			// Exclude windows from other 
			// processes than our victim...
			// NOTE: Since GetWindowThreadProcessId return 
			// the PID of the window creating this one, only 
			// child windows will be detected 
			// (not the main one, which usually is created by explorer.exe)
			return TRUE;
		}
		

		wprintf(L"[*] Found hwnd: %08x\n", hwnd);
		ui.WindowHandles.push_back(hwnd);
	}

	return TRUE;
}


VOID ProcessButtonText(char *buttonTexts)
{
	char *token;
	const char s[2] = ",";

	token = strtok(buttonTexts, s);

	while (token != NULL)
	{
		ui.buttonTexts.push_back(Ansi2Unicode(token));
		token = strtok(NULL, s);
	}
	
}