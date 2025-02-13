const API_URL = 'http://54.250.157.48:8000';

async function fetchWithCORS(url) {
  return fetch(url, {
    mode: 'cors',
    headers: {
      'Accept': 'application/json'
    }
  });
}

function getEntanglement() {
  return document.getElementById('entangledCheckbox').checked;
}

async function spin() {
  clearMessage();
  const entangled = getEntanglement();
  try {
    const response = await fetchWithCORS(`${API_URL}/api/spin?entangled=${entangled}`);
    const data = await response.json();
    document.getElementById('reels').innerText = data.result.join(' ');
  } catch (error) {
    console.error('Error during spin:', error);
  }
}

async function attack() {
  clearMessage();
  const entangled = getEntanglement();
  try {
    const response = await fetchWithCORS(`${API_URL}/api/attack?entangled=${entangled}`);
    const data = await response.json();
    if (data.status === "success") {
      document.getElementById('reels').innerText = data.result.join(' ');
      addBlink();
    } else {
      removeBlink();
    }
    document.getElementById('message').innerText = data.message;
  } catch (error) {
    console.error('Error during attack:', error);
  }
}

function clearMessage() {
  document.getElementById('message').innerText = "";
  removeBlink();
}

function addBlink() {
  document.getElementById('message').classList.add("blink");
}

function removeBlink() {
  document.getElementById('message').classList.remove("blink");
}

async function updateConsole() {
  try {
    const response = await fetchWithCORS(`${API_URL}/api/console`);
    const data = await response.json();
    document.getElementById('console').innerText = data.logs.join('\n');
  } catch (error) {
    console.error('Error fetching console logs:', error);
  }
}

window.onload = () => {
  setInterval(updateConsole, 2000);
  updateConsole();
};

window.spin = spin;
window.attack = attack;
