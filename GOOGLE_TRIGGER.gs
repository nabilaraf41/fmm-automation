// FMM backup trigger: starts the GitHub "FMM hourly" job every hour (GitHub's own schedule can be late or skipped).
// Paste into https://script.google.com -> New project. Set the token once in Project Settings -> Script properties:
//   property  GITHUB_TOKEN  =  your fine-grained token (Actions: Read and write, repo nabilaraf41/fmm-automation)
// Then run setup() once and allow access. Safe if it overlaps GitHub's schedule: the job never posts a slot twice.

function runFmm() {
  var token = PropertiesService.getScriptProperties().getProperty('GITHUB_TOKEN');
  var res = UrlFetchApp.fetch(
    'https://api.github.com/repos/nabilaraf41/fmm-automation/actions/workflows/codes.yml/dispatches', {
      method: 'post',
      contentType: 'application/json',
      headers: { Authorization: 'Bearer ' + token, Accept: 'application/vnd.github+json' },
      payload: JSON.stringify({ ref: 'main' }),
      muteHttpExceptions: true
    });
  Logger.log(res.getResponseCode() + ' ' + res.getContentText());  // 204 = started
}

function setup() {
  ScriptApp.getProjectTriggers().forEach(function (t) { ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('runFmm').timeBased().everyHours(1).create();
  runFmm();
}
