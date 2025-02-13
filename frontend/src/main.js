async function fetchWithCORS(url) {
  return fetch(url, {
    mode: 'cors',
    headers: {
      'Accept': 'application/json'
    }
  });
}

function getQuantumSetting() {
  return document.getElementById('quantumCheckbox').checked;
}

async function spin() {
  clearMessage();
  const quantum = getQuantumSetting();
  try {
    const response = await fetchWithCORS(`http://54.250.157.48:8000/api/spin?use_quantum=${quantum}`);
    const data = await response.json();
    document.getElementById('reels').innerText = data.result.join(' ');
  } catch (error) {
    console.error(error);
  }
}

async function attack() {
  clearMessage();
  const quantum = getQuantumSetting();
  try {
    const response = await fetchWithCORS(`http://54.250.157.48:8000/api/attack?use_quantum=${quantum}`);
    const data = await response.json();
    if (data.status === "success") {
      document.getElementById('reels').innerText = data.result.join(' ');
      addBlink();
    } else {
      removeBlink();
    }
    document.getElementById('message').innerText = data.message;
  } catch (error) {
    console.error(error);
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
    const response = await fetchWithCORS("http://54.250.157.48:8000/api/console");
    const data = await response.json();
    document.getElementById('console').innerText = data.logs.join('\n');
  } catch (error) {
    console.error(error);
  }
}

window.onload = () => {
  setInterval(updateConsole, 2000);
  updateConsole();
};

window.spin = spin;
window.attack = attack;
