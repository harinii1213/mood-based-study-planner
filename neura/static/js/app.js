const tabs=[...document.querySelectorAll('.tabs button')], forms=[...document.querySelectorAll('.auth-form')];
function showTab(name){tabs.forEach(b=>b.classList.toggle('active',b.dataset.tab===name));forms.forEach(f=>f.classList.toggle('active',f.id===name));}
document.querySelectorAll('[data-tab]').forEach(b=>b.addEventListener('click',()=>showTab(b.dataset.tab)));
document.querySelectorAll('[data-open]').forEach(b=>b.addEventListener('click',()=>{showTab(b.dataset.open);document.getElementById('auth').scrollIntoView({behavior:'smooth'});}));
