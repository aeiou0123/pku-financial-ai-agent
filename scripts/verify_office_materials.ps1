param([Parameter(Mandatory=$true)][string]$PackageRoot,[Parameter(Mandatory=$true)][string]$RenderRoot)
$ErrorActionPreference='Stop'
$taskPackage=(Resolve-Path -LiteralPath $PackageRoot).Path
if(Test-Path -LiteralPath $RenderRoot){throw 'Render output must be a new directory'}
New-Item -ItemType Directory -Path $RenderRoot | Out-Null
$taskRender=(Resolve-Path -LiteralPath $RenderRoot).Path
$taskDocumentPath=Join-Path $taskPackage '01_统一信息表.docx'
$taskHashBefore=(Get-FileHash -LiteralPath $taskDocumentPath -Algorithm SHA256).Hash.ToLower()
$taskLimits=@(300,200,800,700,500);$taskCounts=@()
$taskWord=New-Object -ComObject Word.Application
$taskWord.Visible=$false;$taskWord.DisplayAlerts=0
try {
    $taskDocument=$taskWord.Documents.Open($taskDocumentPath,$false,$true)
    if($taskDocument.Tables.Count -ne 7){throw 'Official template table structure differs'}
    for($taskIndex=2;$taskIndex -le 6;$taskIndex++){
        # Microsoft documents that the end-of-cell marker interferes with ComputeStatistics.
        # https://learn.microsoft.com/en-us/office/vba/api/word.range.computestatistics
        $taskRange=$taskDocument.Tables.Item($taskIndex).Cell(1,1).Range.Duplicate
        $taskRange.End=$taskRange.End-1
        $taskCount=$taskRange.ComputeStatistics(0)
        if($taskCount -le 0 -or $taskCount -gt $taskLimits[$taskIndex-2]){throw 'Word field count invalid or over limit'}
        $taskCounts+=$taskCount
    }
    $taskTotal=($taskCounts|Measure-Object -Sum).Sum
    if($taskTotal -gt 2500){throw 'Word total exceeds limit'}
    $taskDocument.ExportAsFixedFormat((Join-Path $taskRender '01_信息表.pdf'),17)
    [ordered]@{status='PASS';method='Microsoft Word Range.ComputeStatistics(wdStatisticWords), end-of-cell marker removed';word_version=$taskWord.Version;field_word_counts=$taskCounts;total=$taskTotal;limits=$taskLimits;total_limit=2500;source='01_统一信息表.docx';source_sha256=$taskHashBefore;pages=$taskDocument.ComputeStatistics(2)} | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $taskRender 'Word字数复核.json') -Encoding UTF8
    $taskDocument.Close(0)
} finally {$taskWord.Quit()}
if((Get-FileHash -LiteralPath $taskDocumentPath -Algorithm SHA256).Hash.ToLower() -ne $taskHashBefore){throw 'Word source changed during verification'}
$taskPowerPoint=New-Object -ComObject PowerPoint.Application
$taskPresentationChecks=@()
try {
    foreach($taskPair in @(@('03_展示稿.pptx','03_展示稿.pdf'),@('07_技术题\技术题报告.pptx','07_技术题报告.pdf'))){
        $taskSource=Join-Path $taskPackage $taskPair[0]
        $taskHash=(Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash.ToLower()
        $taskPresentation=$taskPowerPoint.Presentations.Open($taskSource,-1,0,0)
        $taskPresentation.SaveAs((Join-Path $taskRender $taskPair[1]),32)
        $taskPresentationChecks += [ordered]@{source=$taskPair[0];source_sha256=$taskHash;slides=$taskPresentation.Slides.Count;export=$taskPair[1]}
        $taskPresentation.Close()
        if((Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash.ToLower() -ne $taskHash){throw 'Presentation source changed during verification'}
    }
    [ordered]@{status='PASS';powerpoint_version=$taskPowerPoint.Version;exports=$taskPresentationChecks;scope='Actual Office rendering; visual review remains separate'} | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $taskRender 'PowerPoint导出.json') -Encoding UTF8
} finally {$taskPowerPoint.Quit()}
Get-Content -LiteralPath (Join-Path $taskRender 'Word字数复核.json') -Encoding UTF8
