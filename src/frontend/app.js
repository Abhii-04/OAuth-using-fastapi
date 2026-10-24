const byId = id => document.getElementById(id);
let mode = 'login';
let token = null;
function message(text, error = false) {
  byId('message').textContent = text;
  byId('message').dataset.error = String(error);
}
function setMode(next) {
  mode = next;
  for (const id of ['login', 'register']) byId(id).setAttribute('aria-pressed', String(id === mode));
  byId('heading').textContent = mode === 'login' ? 'Welcome back' : 'Create your account';
  byId('password').autocomplete = mode === 'login' ? 'current-password' : 'new-password';
  byId('submit').textContent = mode === 'login' ? 'Sign in →' : 'Create account →';
  message('');
}
async function request(path, options = {}) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) {
    const detail = Array.isArray(data.detail) ? data.detail.map(item => item.msg).join(' ') : data.detail;
    throw new Error(detail || 'Request failed. Please try again.');
  }
  return data;
}
function showSession(username) {
  byId('access').hidden = true;
  byId('session').hidden = false;
  byId('welcome').textContent = `Hello, ${username}`;
}
for (const id of ['login', 'register']) byId(id).onclick = () => setMode(id);
byId('account-form').onsubmit = async event => {
  event.preventDefault();
  const username = byId('username').value;
  const password = byId('password').value;
  const action = mode;
  const buttons = document.querySelectorAll('button');
  buttons.forEach(button => button.disabled = true);
  message('Please wait…');
  try {
    if (action === 'register') {
      const data = await request('/users/register', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username, password})});
      setMode('login');
      message(`${data.message} You can now sign in.`);
    } else {
      const data = await request('/users/token', {method:'POST', body:new URLSearchParams({username, password})});
      token = data.access_token;
      showSession(username);
      message('Signed in successfully.');
    }
    byId('password').value = '';
  } catch (error) { message(error.message, true); }
  finally { buttons.forEach(button => button.disabled = false); }
};
for (const action of ['check', 'logout']) byId(action).onclick = async () => {
  byId(action).disabled = true;
  try {
    const data = await request(action === 'check' ? '/users/me' : '/users/logout', {method: action === 'check' ? 'GET' : 'POST', headers:{Authorization:`Bearer ${token}`}});
    if (action === 'logout') {
      token = null;
      byId('access').hidden = false;
      byId('session').hidden = true;
      message(data.message);
    } else message(`Session active for ${data.username}.`);
  } catch (error) { message(error.message, true); }
  finally { byId(action).disabled = false; }
};
