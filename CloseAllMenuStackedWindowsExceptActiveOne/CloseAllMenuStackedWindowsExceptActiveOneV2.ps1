Add-Type @"
    using System;
    using System.Text;
    using System.Diagnostics;
    using System.Runtime.InteropServices;
    public class WinApi
    {
        public const int SW_MINIMIZE = 0x0006;
        public const int SW_RESTORE  = 0x0009;
        public const int WM_CLOSE    = 0x0010;

        public const int GA_PARENT = 1;
        public const int GA_ROOT   = 2;
        public const int GA_ROOTOWNER = 3;

        public const int ALL_ACCESS = 0x001FFFFF;

        [StructLayout(LayoutKind.Sequential)]
        public struct MSG
        {
            public IntPtr hWnd;
            public uint   message;
            public IntPtr wParam;
            public IntPtr lParam;
            public uint   time;
        }
        public class User32
        {
            [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
            [DllImport("user32.dll")] public static extern bool   SetForegroundWindow(IntPtr hWnd);
            [DllImport("user32.dll")] public static extern bool   RegisterHotKey(IntPtr hWnd, int id, uint fsModifiers, uint vk);
            [DllImport("user32.dll")] public static extern bool   GetMessage(out MSG lpMsg, IntPtr hWnd, uint wMsgFilterMin, uint wMsgFilterMax);
            [DllImport("user32.dll")] public static extern IntPtr SendMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
            [DllImport("user32.dll")] public static extern bool   ShowWindow(IntPtr hWnd, int nCmdShow);          
            [DllImport("user32.dll")] public static extern int    GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
            [DllImport("user32.dll")] public static extern bool   IsWindowVisible(IntPtr hWnd);
            [DllImport("user32.dll")] public static extern IntPtr GetAncestor(IntPtr hwnd, uint gaFlags);
            [DllImport("user32.dll")] public static extern int    GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
            [DllImport("user32.dll")] public static extern int    GetClassName(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
            
            public delegate bool EnumWindowsCallback(IntPtr hwnd, HandleStackedWindows.WindowInfoSenderWrapper lParam);
            [DllImport("User32.dll")] public static extern bool   EnumWindows(EnumWindowsCallback lpEnumFunc, HandleStackedWindows.WindowInfoSenderWrapper lParam);
            //[DllImport("User32.dll")] public static extern bool EnumChildWindows(IntPtr hWnd, EnumChildWindowsCallback lpEnumFunc, IntPtr lParam);
        }
        public class Kernel32
        {
            [DllImport("kernel32.dll")] public static extern IntPtr OpenProcess(int dwDesiredAccess, int bInheritHandle, int dwProcessId);
            [DllImport("kernel32.dll")] public static extern bool   QueryFullProcessImageName(IntPtr hProcess, int dwFlags, [Out] StringBuilder lpExeName, ref int lpdwSize);
            [DllImport("kernel32.dll")] public static extern uint   GetCurrentProcessId();
        }
    }
    public class HandleStackedWindows
    {
        private const int HK_CLOSE_STACKED_WND    = 0;
        private const int HK_MINIMIZE_STACKED_WND = 1;
        private const int HK_RESTORE_STACKED_WND  = 2;

        public class WindowInfo
        {
            public string className;
            public string windowText;
            public uint Pid;
            public IntPtr handle;
            public IntPtr rootHandle;
            public uint parentPid;
            public string fullModuleName = "";
            public string[] blacklistedClasses = new string[]
            {
                "Shell_TrayWnd",
                "ApplicationFrameWindow",
                "Windows.UI.Core.CoreWindow"
            };
            public string[] blacklistedProcesses = new string[]
            {
                ""
            };
            public WindowInfo(IntPtr hWnd)
            {
                StringBuilder sclassName = new StringBuilder(256);
                StringBuilder swindowText = new StringBuilder(256);
                WinApi.User32.GetWindowText(hWnd, swindowText, 256);
                WinApi.User32.GetClassName(hWnd, sclassName, 256);
                className = sclassName.ToString();
                windowText = swindowText.ToString();
                WinApi.User32.GetWindowThreadProcessId(hWnd, out Pid);
                handle = hWnd;
                rootHandle = WinApi.User32.GetAncestor(hWnd, WinApi.GA_ROOTOWNER);
                WinApi.User32.GetWindowThreadProcessId(rootHandle, out parentPid);

                IntPtr hProc = WinApi.Kernel32.OpenProcess(WinApi.ALL_ACCESS, 0, (int)Pid);

                if(hProc != IntPtr.Zero)
                {
                    int buffLength = 0x2000;
                    StringBuilder fullPathName = new StringBuilder(buffLength);
                    if(WinApi.Kernel32.QueryFullProcessImageName(hProc, 0, fullPathName, ref buffLength))
                    {
                        fullModuleName = fullPathName.ToString(0, buffLength);
                    }
                }//TODO: Throw Exception??
            }  
            public IntPtr GetWindowHandle()
            {
                return handle;
            }              
            private bool CheckByProcessName()
            {
                Func<string, string> ShortProcName = (string fullPath) => {
                    int moduleNameBegin = fullPath.LastIndexOf('\\');
                    return fullPath.Substring(moduleNameBegin + 1);
                };

                string windowProcName = ShortProcName(fullModuleName); //origin path might be different than expected here!

                switch (windowProcName)
                {
                    case "explorer.exe":
                    {
                        if (className == "CabinetWClass") //explorer window
                        {
                            return true;
                        }
                        return false;
                    }
                    default:
                    {
                        foreach (string notValidProcName in blacklistedProcesses)
                        {
                            if (windowProcName == notValidProcName) return false;
                        }
                        break;
                    }
                }
                return true;
            }
            private bool CheckByClassName()
            {
                switch (className)
                {
                    case "Windows.UI.Core.CoreWindow":
                    {
                        return false;
                    }
                    case "ApplicationFrameWindow": //partially accept that class name if...
                    {
                        if (windowText == "Calculator")
                        {
                            return true;
                        }
                        return false;
                    }
                    default:
                    {
                        foreach (string notValidClassName in blacklistedClasses)
                        {
                            if (className == notValidClassName) return false;
                        }
                        break;
                    }
                }
                return true;
            }
            public bool IsProperWindow()
            {
                if(!CheckByProcessName())
                {
                    return false;
                }
                return CheckByClassName();
            }
            public void PrintWindowInfo()
            {
                Console.WriteLine("SOP<");
                Console.WriteLine("visibility: {0:b}; handle: 0x{1:X}({1:d}); pid: 0x{2:X}({2:d}); windowText: {3}; className: {4}; fullModuleName: {5}", WinApi.User32.IsWindowVisible(handle), handle.ToInt32(), Pid, windowText, className, fullModuleName);
                Console.WriteLine("parent handle: 0x{0:X}({0:d}); pid: 0x{1:X}({1:d})", rootHandle.ToInt32(), parentPid);
                Console.WriteLine(">EOP");
            }
            public void CloseWindow()
            {
                WinApi.User32.SendMessage(handle, WinApi.WM_CLOSE, IntPtr.Zero, IntPtr.Zero);
            }
            public void MinimizeWindow()
            {
                WinApi.User32.ShowWindow(handle, WinApi.SW_MINIMIZE);
            }
            public void RestoreWindow()
            {
                WinApi.User32.ShowWindow(handle, WinApi.SW_RESTORE);
            }
        }
        public class WindowInfoSenderWrapper
        {
            public WindowInfo windowInfo;
            public int msg;
            public WindowInfoSenderWrapper(IntPtr hWnd, int msgToSend)
            {
                windowInfo = new WindowInfo(hWnd);
                msg = msgToSend;
            }
            public WindowInfo GetWindow()
            {
                return windowInfo;
            }
            public int GetMessage()
            {
                return msg;
            }

        }
        private static uint GetScriptPID()
        {
            return WinApi.Kernel32.GetCurrentProcessId();
        }
        private static bool CheckCandidates(WindowInfo currentWindow, WindowInfo activeWindow)
        {
            return !(currentWindow.fullModuleName != activeWindow.fullModuleName || currentWindow.handle == activeWindow.handle || currentWindow.Pid == GetScriptPID());
        }
        static private bool ProcessWindows(IntPtr hWnd, WindowInfoSenderWrapper lParam)
        {
            if(WinApi.User32.IsWindowVisible(hWnd))
            {
                var current_window = new WindowInfo(hWnd);
                if (current_window.IsProperWindow())
                {
                    if (CheckCandidates(current_window, lParam.GetWindow()))
                    {
                        switch (lParam.GetMessage())
                        {
                            case WinApi.WM_CLOSE:
                            {
                                current_window.CloseWindow();
                                break;
                            }
                            case WinApi.SW_MINIMIZE:
                            {
                                current_window.MinimizeWindow();
                                break;
                            }
                            case WinApi.SW_RESTORE:
                            {
                                current_window.RestoreWindow();
                                WinApi.User32.SetForegroundWindow(lParam.GetWindow().GetWindowHandle());
                                break;
                            }
                        }
                    }
                }
            }
            return true;
        }
        static public void Dispose(int hkNum){
            switch(hkNum){
                case HK_CLOSE_STACKED_WND:
                {
                    WinApi.User32.EnumWindows(ProcessWindows, new WindowInfoSenderWrapper(WinApi.User32.GetForegroundWindow(), WinApi.WM_CLOSE));
                    break;
                }
                case HK_MINIMIZE_STACKED_WND:
                {
                    WinApi.User32.EnumWindows(ProcessWindows, new WindowInfoSenderWrapper(WinApi.User32.GetForegroundWindow(), WinApi.SW_MINIMIZE));
                    break;
                }
                case HK_RESTORE_STACKED_WND:
                {
                    WinApi.User32.EnumWindows(ProcessWindows, new WindowInfoSenderWrapper(WinApi.User32.GetForegroundWindow(), WinApi.SW_RESTORE));
                    break;
                }
            }
        }

    }
"@

Set-Variable MOD_WIN      -Option Constant -Value 0x0008
Set-Variable MOD_SHIFT    -Option Constant -Value 0x0004
Set-Variable MOD_NOREPEAT -Option Constant -Value 0x4000

Set-Variable VK_ESC       -Option Constant -Value 0x001B
Set-Variable VK_OEM_MINUS -Option Constant -Value 0x00BD

Set-Variable WM_HOTKEY    -Option Constant -Value 0x0312

Set-Variable HK_CLOSE_STACKED_WND    -Option Constant -Value 0x0000
Set-Variable HK_MINIMIZE_STACKED_WND -Option Constant -Value 0x0001
Set-Variable HK_RESTORE_STACKED_WND  -Option Constant -Value 0x0002

if([WinApi+User32]::RegisterHotKey(0, $HK_CLOSE_STACKED_WND, $MOD_WIN    -Bor $MOD_NOREPEAT, $VK_ESC)       -And
   [WinApi+User32]::RegisterHotKey(0, $HK_MINIMIZE_STACKED_WND, $MOD_WIN -Bor $MOD_NOREPEAT, $VK_OEM_MINUS) -And
   [WinApi+User32]::RegisterHotKey(0, $HK_RESTORE_STACKED_WND, $MOD_WIN  -Bor $MOD_SHIFT -Bor $MOD_NOREPEAT, $VK_OEM_MINUS)){
    Write-Host("Press 'WIN+ESC' to close all stacked windows except active one.")
    Write-Host("Press 'WIN+-' to minimize all stacked windows except active one.")
    Write-Host("Press 'WIN+SHIFT+-' to restore all minimized stacked windows except active one.")
}else{
    Write-Host("Failed to register hot keys, script terminated.")
    exit(1)
}

$msg = [WinApi+MSG]@{ hWnd = [System.IntPtr]0; message = 0; wParam = [System.IntPtr]0; lParam = [System.IntPtr]0; time = 0; }

while([WinApi+User32]::GetMessage([ref]$msg, [System.IntPtr]0, 0, 0) -ne 0){
    if($msg.message -eq $WM_HOTKEY){
        [HandleStackedWindows]::Dispose([int]$msg.wParam)
    }
}
#Â