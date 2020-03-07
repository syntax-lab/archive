Add-Type @"
    using System;
    using System.Runtime.InteropServices;
    [StructLayout(LayoutKind.Sequential)]
    public struct WinApiMsgStruct
    {
        public IntPtr hWnd;
        public uint   message;
        public IntPtr wParam;
        public IntPtr lParam;
        public uint   time;
    }
    public class WinApiDlls
    {
        [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
        [DllImport("user32.dll")] public static extern bool   RegisterHotKey(IntPtr hWnd, int id, uint fsModifiers, uint vk);
        [DllImport("user32.dll")] public static extern bool   GetMessage(out WinApiMsgStruct lpMsg, IntPtr hWnd, uint wMsgFilterMin, uint wMsgFilterMax);
        [DllImport("user32.dll")] public static extern bool   ShowWindow(IntPtr hWnd, int nCmdShow);
        [DllImport("user32.dll")] public static extern bool   SetForegroundWindow(IntPtr hWnd);
    }
"@

Set-Variable MOD_WIN      -Option Constant -Value 0x0008
Set-Variable MOD_SHIFT    -Option Constant -Value 0x0004
Set-Variable MOD_NOREPEAT -Option Constant -Value 0x4000

Set-Variable VK_ESC       -Option Constant -Value 0x001B
Set-Variable VK_OEM_MINUS -Option Constant -Value 0x00BD

Set-Variable SW_MINIMIZE  -Option Constant -Value 0x0006
Set-Variable SW_RESTORE   -Option Constant -Value 0x0009

Set-Variable WM_HOTKEY    -Option Constant -Value 0x0312

Set-Variable HK_CLOSE_STACKED_WND    -Option Constant -Value 0x0000
Set-Variable HK_MINIMIZE_STACKED_WND -Option Constant -Value 0x0001
Set-Variable HK_RESTORE_STACKED_WND  -Option Constant -Value 0x0002

if([WinApiDlls]::RegisterHotKey(0, $HK_CLOSE_STACKED_WND, $MOD_WIN    -Bor $MOD_NOREPEAT, $VK_ESC)       -And
   [WinApiDlls]::RegisterHotKey(0, $HK_MINIMIZE_STACKED_WND, $MOD_WIN -Bor $MOD_NOREPEAT, $VK_OEM_MINUS) -And
   [WinApiDlls]::RegisterHotKey(0, $HK_RESTORE_STACKED_WND, $MOD_WIN  -Bor $MOD_SHIFT -Bor $MOD_NOREPEAT, $VK_OEM_MINUS)){
    Write-Host("Press 'WIN+ESC' to close all stacked windows except active one.")
    Write-Host("Press 'WIN+-' to minimize all stacked windows except active one.")
    Write-Host("Press 'WIN+SHIFT+-' to restore all minimized stacked windows except active one.")
}else{
    Write-Host("Failed to register hot keys, script terminated.")
    exit(1)
}

function Find-AllChilds{
    param(
        [parameter(Mandatory = $true, ValueFromPipeline = $false)]
        [int]$child_process_id
    )

    if($child_process_id -ne $null){
        Get-CimInstance -Class Win32_Process -Filter "ParentProcessId=$child_process_id" | ForEach-Object {
            Find-AllChilds($_.ProcessId)
        }
        #NOTE: sometimes child processes enforce parent to terminate earlier
        Stop-Process -Id $child_process_id -ErrorAction SilentlyContinue
    }
}

function Get-RootNonActiveWindows{
    $explorer_process_id = (Get-Process "explorer").Id
    return Get-CimInstance -Class Win32_Process -Filter "ParentProcessId=$explorer_process_id" | ? {
        $_.ProcessId -ne $PID -And $_.ProcessId -ne $active_window_id -And $_.ProcessName -eq $active_window_module_name
    }
}

function Set-WindowsState{
    param(
        [parameter(Mandatory = $true, ValueFromPipeline = $false)]
        [System.IntPtr]$wParam
    )

    $active_window_hwnd = [WinApiDlls]::GetForegroundWindow()
    if($active_window_hwnd){
        $active_window_info = Get-Process | ? { $_.MainWindowHandle -eq $active_window_hwnd }
        if($active_window_info){
            $active_window_id = $active_window_info.Id
            $active_window_module_name = $active_window_info.MainModule.ModuleName
            $active_window_name = $active_window_info.Name
            switch($wParam){
                $HK_CLOSE_STACKED_WND{
                    Get-RootNonActiveWindows | ? {
                        Find-AllChilds($_.ProcessId)
                    }
                }
                $HK_MINIMIZE_STACKED_WND{
                    Get-RootNonActiveWindows | ? {
                        $main_window_handle = (Get-Process -Id $_.ProcessId).MainWindowHandle
                        [WinApiDlls]::ShowWindow($main_window_handle, $SW_MINIMIZE)
                    } | Out-Null
                }
                $HK_RESTORE_STACKED_WND{
                    Get-RootNonActiveWindows | ? {
                        $main_window_handle = (Get-Process -Id $_.ProcessId).MainWindowHandle
                        [WinApiDlls]::ShowWindow($main_window_handle, $SW_RESTORE)
                    } | Out-Null
                    [void][WinApiDlls]::SetForegroundWindow($active_window_hwnd)
                }
            }
        }
    }
}

$msg = [WinApiMsgStruct]@{ hWnd = [System.IntPtr]0; message = 0; wParam = [System.IntPtr]0; lParam = [System.IntPtr]0; time = 0; }

while([WinApiDlls]::GetMessage([ref]$msg, [System.IntPtr]0, 0, 0) -ne 0){
    if($msg.message -eq $WM_HOTKEY){
        Set-WindowsState($msg.wParam)
    }
}
#Â