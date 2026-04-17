/**
 * Web app entry. Open:
 *   .../exec?mode=l3bootcamp
 */
function doGet(e) {
  var mode = e && e.parameter && e.parameter.mode;
  if (mode === 'l3bootcamp') {
    return HtmlService.createHtmlOutputFromFile('l3Bootcamp')
        .setTitle('FE Launchpad — Account Simulator')
        .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
  }
  if (mode === 'facilitator') {
    return HtmlService.createHtmlOutputFromFile('facilitatorGuide')
        .setTitle('FE Launchpad — Facilitator')
        .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
  }
  return HtmlService.createHtmlOutput(
      '<!DOCTYPE html><html><body style="font-family:sans-serif;padding:2rem">' +
      '<p>Add <code>?mode=l3bootcamp</code> to this URL.</p>' +
      '</body></html>'
  ).setTitle('FE Bootcamp launcher');
}
