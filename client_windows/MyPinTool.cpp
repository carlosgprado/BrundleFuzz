//
// This is a pretencious implementation of a AFL-like fuzzer
// for black-box binaries running on Windows platforms
// Actually this is only the "client side" which instruments the binary
// in order to analyze the code coverage
//

#include <tchar.h>
#include <string.h>
#include <stdio.h>
#include <iostream>
#include <fstream>
#include <algorithm>
#include "pin.H"

namespace WIN
{
#include <windows.h>
}

#define BITMAP_SIZE 65536
#define SHMEM_SIZE BITMAP_SIZE * sizeof(UINT32)

using namespace std;
using std::vector;

std::ofstream TraceFile;

// Global variables
ADDRINT lowAddress = 0;
ADDRINT highAddress = 0;
ADDRINT last_id = 0;
ADDRINT current_id = 0;
BOOL g_instrumenting = FALSE;
PIN_LOCK lock;

// IPC related
WIN::LPCTSTR pSHM;	// pointer to shared memory
UINT32 bitmap[BITMAP_SIZE] = { 0 };	// Content to copy to shared memory
TCHAR szName[] = TEXT("Local\\NaFlSharedMemory");

// Command Line stuff
KNOB<BOOL> KnobLogDebug(KNOB_MODE_WRITEONCE, "pintool", "debug", "0", "shows some runtime information");
KNOB<UINT32> KnobTimer(KNOB_MODE_WRITEONCE, "pintool", "timer", "5000", "timer in milliseconds");
KNOB<string> KnobModuleName(KNOB_MODE_WRITEONCE, "pintool", "module", "None", "module to instrument");


string s2l(string s)
{
	std::transform(s.begin(), s.end(), s.begin(), ::tolower);

	return s;
}


int setupIPC()
{
	// This accesses an already existing shared memory
	// region. This shared memory is created by the
	// Python core, which reads the result of every execution.
	WIN::HANDLE hMapFile;

	hMapFile = WIN::OpenFileMapping(
		FILE_MAP_ALL_ACCESS,   // read/write access
		FALSE,                 // do not inherit the name
		szName);               // name of mapping object

	if (hMapFile == NULL)
	{
		LOG("Could not open file mapping object.\n");
		return 1;
	}

	pSHM = (WIN::LPTSTR)WIN::MapViewOfFile(hMapFile, // handle to map object
		FILE_MAP_WRITE,  	// read/write permission
		0,
		0,
		SHMEM_SIZE);

	if (pSHM == NULL)
	{
		LOG("Could not map view of file.\n");
		WIN::CloseHandle(hMapFile);
		return 1;
	}

	return 0;
}


// Finish and cleanup functions
void Fini(INT32 code, void *v)
{
	// Write contents to the shared memory
	CopyMemory((WIN::PVOID)pSHM, bitmap, SHMEM_SIZE);

	// Cleanup IPC
	WIN::UnmapViewOfFile(pSHM);

	if (KnobLogDebug.Value())
	{
		TraceFile << endl << "[*] Finished execution" << endl;
		TraceFile.close();
	}
}


BOOL withinInterestingExecutable(ADDRINT ip)
{
	if (ip >= lowAddress && ip <= highAddress)
		return TRUE;
	else
		return FALSE;
}


// This is called every time a MODULE (dll, etc.) is LOADED
// Analysis function (execution time)
void imageLoad_cb(IMG img, void *v)
{
	string imagename = s2l(IMG_Name(img));
	string knobmodulename = KnobModuleName.Value();

	if (std::strstr(imagename.c_str(), knobmodulename.c_str()) != NULL)
	{
		TraceFile << "[-] Instrumenting module: " << IMG_Name(img).c_str() << endl;

		// Interested in the code section only
		for (SEC sec = IMG_SecHead(img); SEC_Valid(sec); sec = SEC_Next(sec))
		{
			TraceFile << SEC_Name(sec) << endl;

			if (SEC_IsExecutable(sec))
			{
				// NOTE: only the .code section should
				// be executable but this can not be assured.
				// Maybe tighten this condition
				lowAddress = IMG_LowAddress(img);
				highAddress = IMG_HighAddress(img);

				// Let's start the action
				g_instrumenting = TRUE;
			}
		}
	} // end of is main exec
}

// Log some information related to THREAD execution
void threadStart_cb(THREADID threadIndex, CONTEXT *ctxt, INT32 flags, VOID *v)
{
	PIN_GetLock(&lock, threadIndex + 1);
	TraceFile << "[*] THREAD 0x" << hex << threadIndex << " STARTED. Flags: " << flags << endl;
	PIN_ReleaseLock(&lock);
}


void threadFinish_cb(THREADID threadIndex, const CONTEXT *ctxt, INT32 code, VOID *v)
{
	PIN_GetLock(&lock, threadIndex + 1);
	TraceFile << "[*] THREAD 0x" << hex << threadIndex << " FINISHED. Code: " << dec << code << endl;
	PIN_ReleaseLock(&lock);
}


void LogConditionalJmp(ADDRINT ip)
{
	// This is the real deal :)
	// Record the trace!
	current_id = ip - lowAddress;
	bitmap[(current_id ^ last_id) % BITMAP_SIZE]++;
	last_id = current_id >> 1;
}


//
// This identifies conditional jumps (don't care which kind)
//  NOTE: These are all instrumentation functions (JIT),
//  they just point to the analysis ones
//
void Trace(TRACE trace, void *v)
{
	if (!g_instrumenting)
		return;

	// Iterate through basic blocks
	for (BBL bbl = TRACE_BblHead(trace); BBL_Valid(bbl); bbl = BBL_Next(bbl))
	{
		// Code to instrument the events at the end of a BBL (execution transfer)
		// Checking for jnz, jle, ja, etc.
		// NOTE: This is not a BB like shown in IDA but following the definition :)
		INS tail = BBL_InsTail(bbl);

		// Instrument only the interesting code
		if (withinInterestingExecutable(INS_Address(tail)))
		{
			if (INS_IsBranch(tail))
			{
				if (INS_HasFallThrough(tail) || INS_IsCall(tail))
				{
					// From the documentation:
					// So HasFallThrough is TRUE for
					// * instructions which don’t change the control flow(most instructions)
					// * or conditional branches (which might change the control flow, but might not),
					// and FALSE for:
					// * unconditional branches and calls (where the next instruction to be executed is always explicitly specified).
					INS_InsertPredicatedCall(
						tail,
						IPOINT_BEFORE,
						AFUNPTR(LogConditionalJmp),	// Analysis function
						IARG_INST_PTR,				// [R|E]IP of instruction
						IARG_END					// No more args
						);
				}
			}
		} // end "if within exe"
	} // end "for(BBL bbl..."
} // end "void Trace..."


VOID ExceptionCallback(THREADID tid, CONTEXT_CHANGE_REASON reason, const CONTEXT *from, CONTEXT *context, INT32 info, VOID *v)
{
	// The Pin_AddContextChangeFunction() API only notifies your tool about OS events
	// that change the application’s control flow. On Windows, this happens when the
	// application triggers a Win32 exception, and for APC’s and Windows callbacks.

	// Check https://moflow-mitigations.googlecode.com/svn/trunk/BranchMonitor/BranchMonitor.cpp
	// for a complete example.
	if (reason != CONTEXT_CHANGE_REASON_EXCEPTION)
		return;

	if (info == 0xC0000005)
	{
		// Exception!
		char *crash_msg = "\x41\x41\x41\x41\x42\x42\x42\x42";

		CopyMemory((WIN::PVOID)pSHM, crash_msg, strlen(crash_msg));
		WIN::UnmapViewOfFile(pSHM);

		// Terminate the current process immediately, without calling any thread
		// or process fini callbacks that may be registered. This function should
		// be used only for abnormal termination of the instrumented process.
		PIN_ExitProcess(2);
	}
}


static VOID TimerThread(VOID *arg)
{
	// Pretty simple. Sleeps for a specified amount of time,
	// then it kills the instrumented process
	UINT32 delay = KnobTimer.Value();
	UINT32 short_delay = 100;	// milliseconds!
	UINT32 idx = 0;

	// TODO: This may be the worst idea ever...
	for (idx = 0; idx < delay; idx += short_delay)
	{
		if (PIN_IsProcessExiting())
		{
			// Timeout not reached. However, the application
			// is exiting independently. This thread has
			// nothing to do here
			PIN_ExitThread(0);
		}

		PIN_Sleep(short_delay);
	}

	// Timeout!
	if (!PIN_IsProcessExiting())
	{
		// If the process is already in process of exiting, there is no need to kill it.
		// Actually, this could be a problem:
		// "It is prohibited to call PIN_ExitApplication() from an application-fini function."
		PIN_ExitApplication(1);
	}
}


// Help message
INT32 Usage()
{
	cout << "--------------------------------------------------------------------------------------" << endl;
	cout << "The pretentious NaFl :)" << endl;
	cout << "It is totally not AFL..." << endl;
	cout << "--------------------------------------------------------------------------------------" << endl;

	cout << KNOB_BASE::StringKnobSummary() << endl;

	return -1;
}


/* Main function - initialize and set instrumentation callbacks */
int main(int argc, char *argv[])
{
	// Initialize the IPC (shmem)
	int ret = setupIPC();
	if (ret == 1)
	{
		LOG("Failed to initialize IPC");
		return -1;
	}

	// Initialize Pin with symbol capabilities
	PIN_InitSymbols();

	if (PIN_Init(argc, argv))
		return Usage();

	TRACE_AddInstrumentFunction(Trace, 0);				// Basic Block analysis
	IMG_AddInstrumentFunction(imageLoad_cb, 0);			// Image activities

	if (KnobLogDebug.Value())
	{
		TraceFile.open("debug_log.txt");
		PIN_AddThreadStartFunction(threadStart_cb, 0);		// Thread start
		PIN_AddThreadFiniFunction(threadFinish_cb, 0);		// Thread end
	}

	PIN_AddFiniUnlockedFunction(Fini, 0);

	// To check for exceptions on the instrumented program
	PIN_AddContextChangeFunction(ExceptionCallback, 0);

	// A timer thread. It will kill the instrumented
	// process properly, executing Fini()
	PIN_THREAD_UID tUid;
	THREADID tid = PIN_SpawnInternalThread(TimerThread, 0, 0, &tUid);

	// It never returns, sad :)
	PIN_StartProgram();

	return 0;
}
