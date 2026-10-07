param([string]$ImagePath)

$ErrorActionPreference = "Stop"

try {
    Add-Type -AssemblyName System.Runtime.WindowsRuntime

    $asTaskGeneric = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
        $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
    } | Select-Object -First 1

    function AwaitTask($asyncOp, $resultType) {
        $m = $asTaskGeneric.MakeGenericMethod($resultType)
        $task = $m.Invoke($null, @($asyncOp))
        $task.Wait()
        return $task.Result
    }

    [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime] | Out-Null
    [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType = WindowsRuntime] | Out-Null
    [Windows.Media.Ocr.OcrEngine, Windows.Foundation.UniversalApiContract, ContentType = WindowsRuntime] | Out-Null

    $absPath = (Resolve-Path $ImagePath).Path
    $fileOp = [Windows.Storage.StorageFile]::GetFileFromPathAsync($absPath)
    $file = AwaitTask $fileOp ([Windows.Storage.StorageFile])

    $streamOp = $file.OpenAsync([Windows.Storage.FileAccessMode]::Read)
    $stream = AwaitTask $streamOp ([Windows.Storage.Streams.IRandomAccessStream])

    $decoderOp = [Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)
    $decoder = AwaitTask $decoderOp ([Windows.Graphics.Imaging.BitmapDecoder])

    $bitmapOp = $decoder.GetSoftwareBitmapAsync()
    $bitmap = AwaitTask $bitmapOp ([Windows.Graphics.Imaging.SoftwareBitmap])

    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
    if ($null -eq $engine) {
        $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new('en-US'))
    }

    $ocrOp = $engine.RecognizeAsync($bitmap)
    $result = AwaitTask $ocrOp ([Windows.Media.Ocr.OcrResult])

    if ($null -ne $result -and $null -ne $result.Text) {
        Write-Output $result.Text
    }
} catch {
    # Fail silently to avoid breaking caller
    Write-Output ""
}
