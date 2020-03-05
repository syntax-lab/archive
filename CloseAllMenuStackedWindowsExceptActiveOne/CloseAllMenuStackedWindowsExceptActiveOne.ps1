Add-Type @"
    using System;
    using System.Runtime.InteropServices;
    [StructLayout(LayoutKind.Sequential)]
    public struct WinApiMsgStruct
    {
        public IntPtr hWnd;
        public uint message;
        public IntPtr wParam;
        public IntPtr lParam;
        public uint Time;
    }
    public class WinApiDlls 
    {
        [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
        [DllImport("user32.dll")] public static extern bool RegisterHotKey(IntPtr hWnd, int id, uint fsModifiers, uint vk);
        [DllImport("user32.dll")] public static extern bool GetMessage(out WinApiMsgStruct lpMsg, IntPtr hWnd, uint wMsgFilterMin, uint wMsgFilterMax);
        [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
        [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    }
"@

Set-Variable MOD_WIN -option Constant -value 0x0008
Set-Variable MOD_SHIFT -option Constant -value 0x0004
Set-Variable MOD_NOREPEAT -option Constant -value 0x4000

Set-Variable VK_ESC -option Constant -value 0x1B
Set-Variable VK_OEM_MINUS -option Constant -value 0xBD

Set-Variable SW_MINIMIZE -option Constant -value 0x6
Set-Variable SW_RESTORE -option Constant -Value 0x9

Set-Variable WM_HOTKEY -option Constant -value 0x0312

Set-Variable HK_CLOSE_STACKED_WND -option Constant -value 0x0
Set-Variable HK_MINIMIZE_STACKED_WND -option Constant -value 0x1
Set-Variable HK_RESTORE_STACKED_WND -option Constant -value 0x2

if([WinApiDlls]::RegisterHotKey(0, $HK_CLOSE_STACKED_WND, $MOD_WIN -Bor $MOD_NOREPEAT, $VK_ESC) -And
   [WinApiDlls]::RegisterHotKey(0, $HK_MINIMIZE_STACKED_WND, $MOD_WIN -Bor $MOD_NOREPEAT, $VK_OEM_MINUS) -And
   [WinApiDlls]::RegisterHotKey(0, $HK_RESTORE_STACKED_WND, $MOD_WIN -Bor $MOD_SHIFT -Bor $MOD_NOREPEAT, $VK_OEM_MINUS)){
    Write-Host("Use 'WIN+ESC' to close all stacked windows except active one.")
    Write-Host("Use 'WIN+-' to minimize all stacked windows except active one.")
    Write-Host("Use 'WIN+SHIFT+-' to restore all minimized stacked windows except active one.")
}else{
    Write-Host("Failed to register Hot Key, application terminated.")
    exit(1)
}

$msg = [WinApiMsgStruct]@{ hWnd = [System.IntPtr]0; message = 0; wParam = [System.IntPtr]0; lParam = [System.IntPtr]0; time = 0; }

function Set-Windows-State{
    param(
        [parameter(Mandatory = $true, ValueFromPipeline = $false)]
        [System.IntPtr]$wParam
    )

    $active_window_hwnd = [WinApiDlls]::GetForegroundWindow()
    if($active_window_hwnd){
        $active_window_info = Get-Process | ? { $_.mainwindowhandle -eq $active_window_hwnd }
        if($active_window_info){
            $active_window_id = $active_window_info.Id
            $active_window_name = $active_window_info.ProcessName      
        }
    }

    switch($wParam){
        $HK_CLOSE_STACKED_WND{
            $processes_by_name = Get-Process $active_window_name | ? { $_.Id -ne $active_window_id }
            if($processes_by_name){
                Stop-Process $processes_by_name
            }
        }
        $HK_MINIMIZE_STACKED_WND{
            Get-Process $active_window_name | Select-Object mainwindowhandle | ? {
                if($_.MainWindowHandle -ne $active_window_hwnd){
                    [WinApiDlls]::ShowWindow($_.MainWindowHandle, $SW_MINIMIZE)
                }
            } | Out-Null
        }
        $HK_RESTORE_STACKED_WND{
            Get-Process $active_window_name | Select-Object mainwindowhandle | ? {
                if($_.MainWindowHandle -ne $active_window_hwnd){
                    [WinApiDlls]::ShowWindow($_.MainWindowHandle, $SW_RESTORE)
                }
            } | Out-Null
            [WinApiDlls]::SetForegroundWindow($active_window_hwnd) | Out-Null;
        }
    }
}

while([WinApiDlls]::GetMessage([ref]$msg, [System.IntPtr]0, 0, 0) -ne 0){
    if($msg.message -eq $WM_HOTKEY){
        Set-Windows-State($msg.wParam)
    }
}
#Â