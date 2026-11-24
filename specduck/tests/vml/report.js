function apply(){var s=document.getElementById('f-show').value,g=document.getElementById('f-group').value,n=0;
document.querySelectorAll('.case').forEach(function(c){var ok=(s==='all')||(s==='any'?c.classList.contains('bad'):c.dataset[s]==='1');
if(g&&c.dataset.group!==g)ok=false;c.hidden=!ok;if(ok)n++;});document.getElementById('count').textContent=n+'개';}
document.getElementById('f-show').addEventListener('change',apply);document.getElementById('f-group').addEventListener('change',apply);apply();
