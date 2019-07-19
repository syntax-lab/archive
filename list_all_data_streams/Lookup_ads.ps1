$dir = '' + (get-location) + '\Lookup_output\\'

if(!(Test-Path -Path $dir)){
    New-Item -Force -ItemType directory -Path $dir
}

$filename = $args[0]
$outputfile = "$dir$filename.txt"

Get-Item $filename -stream * | Select-Object Stream | ForEach-Object {
    $stream = $_.Stream;
    Write-Output $stream':';
    Get-Content $filename -stream $stream;
    Write-Output ""
} | Out-File -FilePath $outputfile
