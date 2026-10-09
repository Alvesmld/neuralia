const $ = (id) => document.getElementById(id);
const description = $('description');
const button = $('generate-btn');
const message = $('message');
const result = $('result');
const apiBase = (window.ALVESMLD_API_URL || '').replace(/\/$/, '');
function showMessage(text, error=false) { message.textContent=text; message.classList.remove('hidden','error'); if(error) message.classList.add('error'); }
function hideMessage() { message.classList.add('hidden'); }
description.addEventListener('input', () => $('char-count').textContent = `${description.value.length} / 3000`);
document.querySelectorAll('[data-prompt]').forEach(chip => chip.addEventListener('click', () => { description.value=chip.dataset.prompt; description.dispatchEvent(new Event('input')); description.focus(); }));
async function checkHealth() {
  if (!apiBase || apiBase.includes('COLOQUE-A-URL')) { $('connection-label').textContent='Configure a URL da API'; return; }
  try { const r=await fetch(`${apiBase}/health`); if(!r.ok) throw new Error(); $('connection-label').textContent='API conectada'; }
  catch { $('connection-label').textContent='API indisponível'; }
}
button.addEventListener('click', async () => {
  const text=description.value.trim(); result.classList.add('hidden');
  if(text.length<8) { showMessage('Escreva uma descrição com pelo menos 8 caracteres.',true); return; }
  if(!apiBase || apiBase.includes('COLOQUE-A-URL')) { showMessage('A interface está pronta, mas falta configurar a URL pública da API no arquivo web/config.js. Veja o DEPLOY_V11.md.',true); return; }
  button.disabled=true; button.querySelector('span:first-child').textContent='Preparando…'; hideMessage(); showMessage('A ALVESMLD está montando os arquivos. Aguarde…');
  try {
    const response=await fetch(`${apiBase}/api/generate`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({description:text})});
    const data=await response.json(); if(!response.ok) throw new Error(data.detail || 'Erro ao gerar projeto.');
    $('result-name').textContent=data.name; $('blueprint-pill').textContent=`Blueprint: ${data.blueprint}`; $('file-count').textContent=data.file_count; $('pending-count').textContent=data.requirements_pending; $('test-status').textContent='Não executados'; $('warning').textContent=data.warning;
    const list=$('file-list'); list.replaceChildren(); data.files.forEach(name=>{const li=document.createElement('li');li.textContent=name;list.appendChild(li)});
    $('download-btn').href=`${apiBase}${data.download_url}`; $('download-btn').setAttribute('download',`${data.name}.zip`); result.classList.remove('hidden'); showMessage('Projeto preparado. Baixe o ZIP e revise os arquivos antes de executar.'); result.scrollIntoView({behavior:'smooth',block:'start'});
  } catch(err) { showMessage(err.message || 'Não foi possível conectar à API. Confira a URL e o status do servidor.',true); }
  finally { button.disabled=false; button.querySelector('span:first-child').textContent='Gerar projeto'; }
});
checkHealth();
