from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import math
import datetime
import random

from qiskit import QuantumCircuit
from qiskit_aer import Aer
from qiskit.compiler import transpile

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# -------------------------------
# Logging (for our “console” window)
# -------------------------------
console_logs = []

def log_event(event: str):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    console_logs.append(f"[{timestamp}] {event}")
    if len(console_logs) > 100:
        console_logs.pop(0)

# -------------------------------
# Global classical RNG (seeded with 2)
# -------------------------------
classical_rng = random.Random(2)

# -------------------------------
# Quantum Random Number Generation (using Qiskit)
# -------------------------------
def quantum_random_int(n_bits: int, max_value: int) -> int:
    backend = Aer.get_backend('qasm_simulator')
    random_bits = []
    for _ in range(n_bits):
        qc = QuantumCircuit(2, 2)
        qc.h(0)        # put qubit 0 into superposition
        qc.cx(0, 1)    # entangle qubit 1 with qubit 0
        qc.measure([0, 1], [0, 1])
        qc_transpiled = transpile(qc, backend)
        job = backend.run(qc_transpiled, shots=1)
        result = job.result().get_counts(qc)
        bitstring = list(result.keys())[0]  # e.g. "00" or "11"
        # Both bits are identical due to entanglement; take the rightmost bit.
        bit = int(bitstring[-1])
        random_bits.append(bit)
    number = 0
    for bit in random_bits:
        number = (number << 1) | bit
    if number < max_value:
        return number
    else:
        return quantum_random_int(n_bits, max_value)

def quantum_random_choice(options: list) -> any:
    n_options = len(options)
    n_bits = math.ceil(math.log2(n_options))
    while True:
        num = quantum_random_int(n_bits, 2**n_bits)
        if num < n_options:
            return options[num]

# -------------------------------
# Classical Random Number Generation (seeded, for demonstration)
# -------------------------------
def classical_random_int(n_bits: int, max_value: int) -> int:
    # For classical RNG we ignore n_bits and use a seeded generator.
    num = classical_rng.randrange(max_value)
    log_event(f"Classical RNG: generated number {num} (max_value {max_value})")
    return num

def classical_random_choice(options: list) -> any:
    choice = classical_rng.choice(options)
    log_event(f"Classical RNG: choice from {options} is {choice}")
    return choice

def random_int(n_bits: int, max_value: int, use_quantum: bool) -> int:
    return quantum_random_int(n_bits, max_value) if use_quantum else classical_random_int(n_bits, max_value)

def random_choice(options: list, use_quantum: bool) -> any:
    return quantum_random_choice(options) if use_quantum else classical_random_choice(options)

# -------------------------------
# Slot Machine Logic
# -------------------------------
symbols = ["🍒", "🍋", "🍊", "⭐", "🔔", "💎"]

def spin_slot_machine(use_quantum: bool) -> list:
    reels = []
    for _ in range(3):
        reels.append(random_choice(symbols, use_quantum))
    log_event(f"Slot machine spin (quantum={use_quantum}): {' '.join(reels)}")
    return reels

def slot_attack(use_quantum: bool) -> dict:
    if use_quantum:
        # In quantum mode tampering is prevented.
        outcome = spin_slot_machine(use_quantum=True)
        log_event("Slot machine attack attempted in quantum mode; attack failed.")
        return {
            "status": "fail",
            "message": "Attack ineffective in quantum mode.",
            "result": outcome
        }
    else:
        # In classical mode, we simulate a successful attack.
        log_event("Classical slot machine attack successful: predicted jackpot outcome.")
        return {
            "status": "success",
            "message": "Attack successful! Predicted jackpot outcome.",
            "result": ["💎", "💎", "💎"]
        }

# -------------------------------
# Card Game Logic
#
# Two “cards” (each 1–10) are generated and summed to produce a target.
# Two players then enter guesses; the one whose guess is closest wins.
#
# -------------------------------
current_card_deal = None  # store the current deal for the card game

def deal_cards(use_quantum: bool, simulate_eavesdrop: bool) -> dict:
    global current_card_deal  # Declare global at the very top
    if use_quantum:
        # Generate the cards with quantum randomness
        card1 = random_choice(list(range(1, 11)), True)
        card2 = random_choice(list(range(1, 11)), True)
        total = card1 + card2
        current_card_deal = {
            "card1": card1,
            "card2": card2,
            "sum": total,
            "use_quantum": use_quantum
        }
        if simulate_eavesdrop:
            return {
                "card1": "?",
                "card2": "?",
                "message": "Error! Tampering detected: Qubits disturbed."
            }
        else:
            pass
    else:
        # Classical mode: use the seeded RNG.
        card1 = classical_rng.randint(1, 10)
        card2 = classical_rng.randint(1, 10)
        total = card1 + card2
        current_card_deal = {
            "card1": card1,
            "card2": card2,
            "sum": total,
            "use_quantum": use_quantum
        }
        log_event(f"Dealt cards (classical): {card1} + {card2} = {total}")
        if simulate_eavesdrop:
            return {
                "card1": card1,
                "card2": card2,
                "sum": total,
                "message": "Classical eavesdropping: Cards and sum revealed!"
            }
        else:
            return {
                "card1": card1,
                "card2": card2,
                "sum": total,
                "message": "Cards dealt in classical mode. Target revealed."
            }


def guess_cards(player1: int, player2: int) -> dict:
    if current_card_deal is None:
        return {"error": "No cards have been dealt yet."}
    total = current_card_deal["sum"]
    diff1 = abs(player1 - total)
    diff2 = abs(player2 - total)
    if diff1 < diff2:
        winner = "Player 1"
    elif diff2 < diff1:
        winner = "Player 2"
    else:
        winner = "Tie"
    log_event(f"Card game guess: target {total}, Player 1 guessed {player1}, Player 2 guessed {player2}, winner: {winner}")
    return {
        "target": total,
        "player1_guess": player1,
        "player2_guess": player2,
        "winner": winner
    }

# -------------------------------
# FastAPI Endpoints
# -------------------------------

# Landing page
@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Slot machine page
@app.get("/slot", response_class=HTMLResponse)
async def slot_page(request: Request):
    return templates.TemplateResponse("slot.html", {"request": request})

# Card game page
@app.get("/card", response_class=HTMLResponse)
async def card_page(request: Request):
    return templates.TemplateResponse("card.html", {"request": request})

# API endpoints for the slot machine
@app.get("/api/spin", response_class=JSONResponse)
async def api_spin(use_quantum: bool = Query(True), simulate_eavesdrop: bool = Query(False)):
    if simulate_eavesdrop:
        if use_quantum:
            return JSONResponse(status_code=500, content={"error": "Quantum eavesdropping error: Qubits disturbed!"})
        else:
            result = spin_slot_machine(use_quantum)
            return {"result": result, "use_quantum": use_quantum, "message": "Classical eavesdropping: outcome revealed!"}
    else:
        result = spin_slot_machine(use_quantum)
        return {"result": result, "use_quantum": use_quantum}

@app.get("/api/attack", response_class=JSONResponse)
async def api_attack(use_quantum: bool = Query(True), simulate_eavesdrop: bool = Query(False)):
    if simulate_eavesdrop:
        if use_quantum:
            return JSONResponse(status_code=500, content={"error": "Quantum eavesdropping error: Qubits disturbed during attack!"})
        else:
            result = slot_attack(use_quantum)
            result["message"] += " (Classical eavesdropping simulated)"
            return result
    else:
        result = slot_attack(use_quantum)
        return result

# API endpoints for the card game
@app.get("/api/card/deal", response_class=JSONResponse)
async def api_card_deal(use_quantum: bool = Query(True), simulate_eavesdrop: bool = Query(False)):
    try:
        result = deal_cards(use_quantum, simulate_eavesdrop)
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/card/guess", response_class=JSONResponse)
async def api_card_guess(player1: int, player2: int):
    result = guess_cards(player1, player2)
    return result

# Endpoint to retrieve the log (for our “console” window)
@app.get("/api/console", response_class=JSONResponse)
async def api_console():
    return {"logs": console_logs}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
