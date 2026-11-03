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

// Weekly plan -> owner's Google Doc (needs the token to also have Contents: Read).
var PLAN_DOC = '1O9WalUFXmszdZyfwwhl_ObmsHcm-41F8GLQeqc4ixJM';

function writePlan() {
  var token = PropertiesService.getScriptProperties().getProperty('GITHUB_TOKEN');
  var res = UrlFetchApp.fetch(
    'https://api.github.com/repos/nabilaraf41/fmm-automation/contents/content/week_plan.md', {
      headers: { Authorization: 'Bearer ' + token, Accept: 'application/vnd.github.raw' },
      muteHttpExceptions: true
    });
  if (res.getResponseCode() != 200) { Logger.log(res.getResponseCode() + ' ' + res.getContentText()); return; }
  var body = DocumentApp.openById(PLAN_DOC).getBody();
  body.clear();
  var rows = [];
  res.getContentText().split('\n').concat(['']).forEach(function (line) {
    if (line.indexOf('|') == 0) {            // markdown table row
      if (!/^[|\-\s]+$/.test(line)) rows.push(line.replace(/^\||\|$/g, '').split('|').map(function (c) { return c.trim(); }));
      return;
    }
    if (rows.length) { body.appendTable(rows); rows = []; }
    if (line.indexOf('## ') == 0) body.appendParagraph(line.slice(3)).setHeading(DocumentApp.ParagraphHeading.HEADING2);
    else if (line.indexOf('# ') == 0) body.appendParagraph(line.slice(2)).setHeading(DocumentApp.ParagraphHeading.HEADING1);
    else if (line) body.appendParagraph(line);
  });
}

function setup() {
  ScriptApp.getProjectTriggers().forEach(function (t) { ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('runFmm').timeBased().everyHours(1).create();
  ScriptApp.newTrigger('writePlan').timeBased().onWeekDay(ScriptApp.WeekDay.THURSDAY).atHour(18).create();
  runFmm();
  writePlan();
}
