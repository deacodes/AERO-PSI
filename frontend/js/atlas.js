// Evidence explorer bindings are in research.js.
function renderAtlasRuns() {}
async function loadAtlasGaps() {}
function renderCoverage() {}
    $$('[data-prompt]').forEach(button=>button.addEventListener('click',()=>{$('#copilotQuestion').value=button.dataset.prompt;$('#copilotQuestion').focus();}));
    $('#sourceSearch').addEventListener('input',event=>renderSourceTrail(state.copilotSources,event.target.value));
    $('#askCopilot').addEventListener('click', () => askScienceQuestion());
