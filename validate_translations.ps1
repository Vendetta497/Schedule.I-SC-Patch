# Validate dictionary rows and regression fixtures with XUnity.AutoTranslator 5.4.5.
# The four original implementations are downloaded from a pinned upstream commit.
# Unity hooks, number templating, and online endpoints are not simulated here.
[CmdletBinding()]
param(
 [string]$SourceCachePath = (Join-Path ([IO.Path]::GetTempPath()) 'ScheduleI-translation-validation-5.4.5'),
 [string]$ReportPath = ''
)
$ErrorActionPreference='Stop'
$projectPath=$PSScriptRoot
$sourcesPath=Join-Path $SourceCachePath 'sources'
$compilePath=Join-Path $SourceCachePath 'compile'
New-Item -ItemType Directory -Path $sourcesPath,$compilePath -Force | Out-Null
$upstreamCommit='29583ac89239ca2764bed16f0e5c1efce48f0c47'
$upstreamFiles=@(
 @{name='TextHelper.cs';path='Utilities/TextHelper.cs';sha256='e9b1f1b36437a420141e424d3bbbc36059bb6f906de6e64ebc87520466c951ec'},
 @{name='RegexTranslation.cs';path='RegexTranslation.cs';sha256='db6c8e0e6d24cb607a2b5ae9aec530640c27c3915267b51ddf1ab6fed9e9f3de'},
 @{name='RegexTranslationSplitter.cs';path='Parsing/RegexTranslationSplitter.cs';sha256='b3737c2992c3c56cae6d6a8111a78118627dcb4292056ce0db70514d1b3fe307'},
 @{name='ParserResult.cs';path='Parsing/ParserResult.cs';sha256='2bbb154dea68486c8355c9c636813b059f3891eec939b05793eb91c49f122fb7'}
)
foreach($entry in $upstreamFiles) {
 $target=Join-Path $sourcesPath $entry.name
 if(-not (Test-Path -LiteralPath $target)) {
  $url='https://raw.githubusercontent.com/bbepis/XUnity.AutoTranslator/'+$upstreamCommit+'/src/XUnity.AutoTranslator.Plugin.Core/'+$entry.path
  Invoke-WebRequest -Uri $url -OutFile $target
 }
 if((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ine $entry.sha256) {
  throw ('Pinned source hash mismatch: '+$entry.name)
 }
}

$sourceText=@'
namespace XUnity.AutoTranslator.Plugin.Core {
internal static class AutoTranslationPlugin {
public static System.Text.RegularExpressions.RegexOptions RegexCompiledSupportedFlag=System.Text.RegularExpressions.RegexOptions.None;
}
}

namespace XUnity.AutoTranslator.Plugin.Core.Configuration {
internal static class Settings { public static object RegexPostProcessing = null; }
}
namespace XUnity.AutoTranslator.Plugin.Core.Utilities {
internal static class RomanizationHelper { public static string PostProcess(string text, object mode) { return text; } }
}
namespace XUnity.AutoTranslator.Plugin.Core.Endpoints {
internal class UntranslatedTextInfo { public string Text; public UntranslatedTextInfo(string text) { Text = text; } }
}
namespace XUnity.AutoTranslator.Plugin.Core.Parsing {
internal enum ParserResultOrigin { RegexTextParser }
internal class ArgumentedUntranslatedTextInfo {
 public string Key { get; set; } public XUnity.AutoTranslator.Plugin.Core.Endpoints.UntranslatedTextInfo Info { get; set; }
}
}

public static class EngineValidation {

public static string JoinParts(string key, string value, string input, System.Func<string,string> translate) {
 var splitter = new XUnity.AutoTranslator.Plugin.Core.Parsing.RegexTranslationSplitter(key,value);
 var match = splitter.CompiledRegex.Match(input);
 if(!match.Success) return null;
 var parsed = new XUnity.AutoTranslator.Plugin.Core.Parsing.ParserResult(
  XUnity.AutoTranslator.Plugin.Core.Parsing.ParserResultOrigin.RegexTextParser,
  input, splitter.Translation, true, true, false, true, splitter.CompiledRegex, match);
 return parsed.GetTranslationFromParts(info => translate(info.Text));
}

public static string[] Parse(string line) {return XUnity.AutoTranslator.Plugin.Core.Utilities.TextHelper.ReadTranslationLineAndDecode(line);}
public static System.Text.RegularExpressions.Regex Compile(string key, string value) {
if(key.StartsWith("sr:")) return new XUnity.AutoTranslator.Plugin.Core.Parsing.RegexTranslationSplitter(key,value).CompiledRegex;
return new XUnity.AutoTranslator.Plugin.Core.RegexTranslation(key,value).CompiledRegex;
}
}
'@
$sourceFiles=@('TextHelper.cs','RegexTranslation.cs','RegexTranslationSplitter.cs','ParserResult.cs')
# Compile the original loader implementations with only their logging import removed.
$compileFiles=@()
foreach($filename in $sourceFiles){
 $copyPath=Join-Path $compilePath ('validation-'+$filename)
 $content=(Get-Content -LiteralPath (Join-Path $sourcesPath $filename) -Raw).Replace('using XUnity.Common.Logging;','')
 [IO.File]::WriteAllText($copyPath,$content,[Text.UTF8Encoding]::new($false))
 $compileFiles+=$copyPath
}
$stubPath=Join-Path $compilePath 'validation-stub.cs'
[IO.File]::WriteAllText($stubPath,$sourceText,[Text.UTF8Encoding]::new($false))
Add-Type -Path ($compileFiles+@($stubPath))
$issues=[Collections.Generic.List[object]]::new()
$lineCount=0
foreach($file in Get-ChildItem -LiteralPath (Join-Path $projectPath 'AutoTranslator/Translation/zh-CN/Text') -Filter '*.txt'){
 $number=0
 foreach($line in [IO.File]::ReadAllLines($file.FullName)){
  $number++
  if($line.StartsWith('//') -or [string]::IsNullOrEmpty($line)){continue}
  $lineCount++
  try{
   $parts=[EngineValidation]::Parse($line)
   if($null -eq $parts -or $parts.Count -ne 2 -or [string]::IsNullOrEmpty($parts[0]) -or [string]::IsNullOrEmpty($parts[1])){throw 'Invalid or empty loader row'}
   if($parts[0].StartsWith('r:') -or $parts[0].StartsWith('sr:')){
    $regex=[EngineValidation]::Compile($parts[0],$parts[1])
    $groups=$regex.GetGroupNames()
    foreach($token in [regex]::Matches($parts[1],'(?<!\$)\$(?:\{([^}]+)\}|([1-9][0-9]*))')){
     $groupName=if($token.Groups[1].Success){$token.Groups[1].Value}else{$token.Groups[2].Value}
     if($groupName -notin $groups){$issues.Add(@{file=$file.Name;line=$number;key=$parts[0];error='Missing replacement capture: '+$token.Value})}
    }
   }
  }catch{$issues.Add(@{file=$file.Name;line=$number;error=$_.Exception.Message;raw=$line})}
 }
}
$report=@{loader_version='5.4.5';checked_lines=$lineCount;errors=@($issues.ToArray());passed=($issues.Count -eq 0)}
if($lineCount -eq 0){throw 'No translation rows found'}
$report | Select-Object passed,checked_lines,@{n='errors_count';e={$_.errors.Count}} | ConvertTo-Json

$literalRows=@()
$regexRows=@()
foreach($file in Get-ChildItem -LiteralPath (Join-Path $projectPath 'AutoTranslator/Translation/zh-CN/Text') -Filter '*.txt' | Sort-Object Name) {
 foreach($line in [IO.File]::ReadAllLines($file.FullName)) {
  if($line.StartsWith('//') -or [string]::IsNullOrEmpty($line)){continue}
  $parts=[EngineValidation]::Parse($line)
  if($null -eq $parts -or $parts.Count -ne 2){continue}
  $row=@{key=$parts[0];translation=$parts[1]}
  if($parts[0].StartsWith('r:') -or $parts[0].StartsWith('sr:')){$regexRows+=$row}else{$literalRows+=$row}
 }
}
$dictionary=[Collections.Generic.Dictionary[string,string]]::new([StringComparer]::Ordinal)
foreach($row in $literalRows){$dictionary[$row.key]=$row.translation}
$regexes=[Collections.Generic.List[object]]::new()
foreach($row in $regexRows){
 $value=$row.translation
 $first=$value.IndexOf('"');$last=$value.LastIndexOf('"')
 if($first -ge 0 -and $last -gt $first){$value=$value.Substring($first+1,$last-$first-1)}
 $regexes.Add(@{key=$row.key;regex=[EngineValidation]::Compile($row.key,$row.translation);replacement=$value;rawValue=$row.translation;split=$row.key.StartsWith('sr:')})
}
function Resolve-GameText([string]$inputText,[int]$depth=0){
 if($dictionary.ContainsKey($inputText)){return $dictionary[$inputText]}
 if($depth -gt 4){return $inputText}
 for($i=$regexes.Count-1;$i -ge 0;$i--){
  $unit=$regexes[$i]
  if($unit.split){continue}
  $match=$unit.regex.Match($inputText)
  if($match.Success){return $match.Result($unit.replacement)}
 }
 for($i=$regexes.Count-1;$i -ge 0;$i--){
  $unit=$regexes[$i]
  if(-not $unit.split){continue}
  $match=$unit.regex.Match($inputText)
  if(-not $match.Success){continue}
  $resolver = [Func[string,string]]{param($part) Resolve-GameText $part ($depth+1)}
  return [EngineValidation]::JoinParts($unit.key,$unit.rawValue,$inputText,$resolver)
 }
 return $inputText
}
$cases=@()
foreach($fixture in (Get-Content -LiteralPath (Join-Path $projectPath 'translation-regression.json') -Raw -Encoding utf8 | ConvertFrom-Json)) {
 $cases += @{text=$fixture.input;expected=$fixture.expected;rule_key=$fixture.rule_key}
}
$caseResults=@()
foreach($case in $cases){
 if($case['rule_key']) {
 $unit = $regexRows | Where-Object {$_.key -ceq $case['rule_key']} | Select-Object -First 1
 $resolver = [Func[string,string]]{param($part) Resolve-GameText $part 1}
 $actual = [EngineValidation]::JoinParts($unit.key,$unit.translation,$case.text,$resolver)
} else { $actual=Resolve-GameText $case.text }
 $ok=$true
 if($case.expected -and $actual -ne $case.expected){$ok=$false}
 if($case.mustTranslate -and $actual -notmatch '[\u4e00-\u9fff]'){$ok=$false}
 foreach($fragment in $case['contains']){if(-not $actual.Contains($fragment)){$ok=$false}}
 $caseResults+=@{input=$case.text;actual=$actual;expected=$case.expected;passed=$ok;rule_key=$case['rule_key']}
}
$regression=@{passed=(@($caseResults | Where-Object {-not $_.passed}).Count -eq 0);cases=$caseResults}
if($ReportPath){@{format=$report;regression=$regression} | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $ReportPath -Encoding utf8}
$regression | Select-Object passed,@{n='cases_count';e={$_.cases.Count}} | ConvertTo-Json
if(-not $report.passed -or -not $regression.passed){throw 'PR translation validation failed'}
